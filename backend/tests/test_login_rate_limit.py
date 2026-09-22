import asyncio

import pytest

from app.core.config import get_settings
from app.core.exceptions import TooManyRequestsError
from app.core.ratelimit import LoginRateLimiter, login_identifier
from app.core.redis import get_redis
from tests.conftest import CUSTOMER_EMAIL, PASSWORD, login

pytestmark = pytest.mark.asyncio

GENERIC_MESSAGE = "Credenciales incorrectas."


async def _fail(client, email: str, password: str = "incorrecta123") -> dict:
    response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return response


async def _clear_block(email: str, ip: str = "127.0.0.1") -> None:
    identifier = login_identifier(email, ip)
    redis = get_redis()
    await redis.delete(f"login:attempts:{identifier}", f"login:blocked:{identifier}")


async def test_third_failure_blocks_for_300_seconds(client, customer_token):
    assert get_settings().login_block_seconds == 300

    for _ in range(2):
        response = await _fail(client, CUSTOMER_EMAIL)
        assert response.status_code == 401
        assert response.json()["detail"] == GENERIC_MESSAGE

    third = await _fail(client, CUSTOMER_EMAIL)
    assert third.status_code == 401
    assert third.json()["detail"] == GENERIC_MESSAGE

    # Incluso con credenciales correctas el bloqueo se mantiene.
    blocked = await _fail(client, CUSTOMER_EMAIL, PASSWORD)
    assert blocked.status_code == 429
    assert "Demasiados intentos fallidos" in blocked.json()["detail"]

    identifier = login_identifier(CUSTOMER_EMAIL, "127.0.0.1")
    ttl = await get_redis().ttl(f"login:blocked:{identifier}")
    assert 0 < ttl <= 300


async def test_new_window_after_block_expires(client, customer_token):
    await _clear_block(CUSTOMER_EMAIL)
    for _ in range(3):
        assert (await _fail(client, CUSTOMER_EMAIL)).status_code == 401
    assert (await _fail(client, CUSTOMER_EMAIL, PASSWORD)).status_code == 429

    # Simula la expiracion del TTL: se elimina el bloqueo.
    await _clear_block(CUSTOMER_EMAIL)

    recovered = await login(client, CUSTOMER_EMAIL, PASSWORD)
    assert recovered["access_token"]

    # Nueva ventana de 3 intentos y segundo bloqueo.
    for _ in range(3):
        assert (await _fail(client, CUSTOMER_EMAIL)).status_code == 401
    second_block = await _fail(client, CUSTOMER_EMAIL, PASSWORD)
    assert second_block.status_code == 429
    assert "Demasiados intentos fallidos" in second_block.json()["detail"]


async def test_unknown_user_has_same_generic_response_and_blocks(client):
    unknown = "nadie@test.dev"
    for _ in range(3):
        response = await _fail(client, unknown)
        assert response.status_code == 401
        assert response.json()["detail"] == GENERIC_MESSAGE

    blocked = await _fail(client, unknown)
    assert blocked.status_code == 429
    assert "Demasiados intentos fallidos" in blocked.json()["detail"]


async def test_rate_limit_uses_trusted_real_ip(client, customer_token):
    await _clear_block(CUSTOMER_EMAIL)
    for _ in range(3):
        assert (await _fail(client, CUSTOMER_EMAIL)).status_code == 401
    assert (await _fail(client, CUSTOMER_EMAIL, PASSWORD)).status_code == 429

    # Un X-Forwarded-For enviado por el cliente no cambia la IP efectiva:
    # el bloqueo se mantiene (no se puede evadir el rate limit).
    spoofed = await client.post(
        "/api/v1/auth/login",
        headers={"X-Forwarded-For": "10.20.30.40"},
        json={"email": CUSTOMER_EMAIL, "password": PASSWORD},
    )
    assert spoofed.status_code == 429

    # La IP confiable la aporta el proxy vía X-Real-IP.
    other_ip = await client.post(
        "/api/v1/auth/login",
        headers={"X-Real-IP": "10.20.30.40"},
        json={"email": CUSTOMER_EMAIL, "password": PASSWORD},
    )
    assert other_ip.status_code == 200

    # Otro email desde la IP original tampoco está bloqueado.
    other_email = await _fail(client, "otro.login@test.dev")
    assert other_email.status_code == 401


async def test_block_window_resets_after_expiry():
    limiter = LoginRateLimiter(max_attempts=3, block_seconds=1)
    identifier = login_identifier("ttl@test.dev", "10.0.0.9")
    for _ in range(3):
        await limiter.reserve(identifier)

    with pytest.raises(TooManyRequestsError):
        await limiter.reserve(identifier)

    await asyncio.sleep(1.2)
    await limiter.reserve(identifier)  # nueva ventana: no lanza


async def test_concurrent_attempts_cannot_exceed_limit(client, customer_token):
    """Una ráfaga concurrente no supera el máximo de verificaciones."""
    await _clear_block(CUSTOMER_EMAIL)
    responses = await asyncio.gather(*[_fail(client, CUSTOMER_EMAIL) for _ in range(12)])
    codes = [response.status_code for response in responses]

    assert codes.count(401) <= get_settings().login_max_attempts
    assert codes.count(429) == len(codes) - codes.count(401)
    assert all(code in (401, 429) for code in codes)


async def test_successful_login_resets_attempts(client, customer_token):
    for _ in range(2):
        assert (await _fail(client, CUSTOMER_EMAIL)).status_code == 401
    assert (await _fail(client, CUSTOMER_EMAIL, PASSWORD)).status_code == 200

    identifier = login_identifier(CUSTOMER_EMAIL, "127.0.0.1")
    assert await get_redis().exists(f"login:attempts:{identifier}") == 0
