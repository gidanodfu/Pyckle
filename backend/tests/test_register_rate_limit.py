"""Rate limit de alta de cuentas por IP confiable.

El principal es la IP (no el email): variar el email no debe esquivar el
límite. Es una política independiente del TTL de onboarding OAuth.
"""

import asyncio

import pytest
import redis

from app.core.exceptions import TooManyRequestsError
from app.core.ratelimit import RegistrationRateLimiter
from tests.conftest import register_payload

pytestmark = pytest.mark.asyncio


class _BrokenRedis:
    def __getattr__(self, name):
        if name == "pipeline":

            def _raise_pipeline(*_args, **_kwargs):
                raise redis.RedisError("redis caído")

            return _raise_pipeline

        async def _raise(*_args, **_kwargs):
            raise redis.RedisError("redis caído")

        return _raise


def _low_limit(monkeypatch, module: str, *, max_attempts: int, block_seconds: int = 300) -> None:
    monkeypatch.setattr(
        f"{module}.RegistrationRateLimiter",
        lambda: RegistrationRateLimiter(max_attempts=max_attempts, block_seconds=block_seconds),
    )


async def _register(client, geo, *, email: str, phone: str):
    return await client.post(
        "/api/v1/auth/register",
        json=register_payload(geo, email=email, phone=phone),
    )


async def test_registration_allowed_under_limit(client, geo):
    response = await _register(client, geo, email="ok@test.dev", phone="+51955555501")
    assert response.status_code == 201, response.text


async def test_registration_blocks_after_limit(client, geo, monkeypatch):
    _low_limit(monkeypatch, "app.domains.auth.service", max_attempts=2)

    assert (
        await _register(client, geo, email="r1@test.dev", phone="+51955555502")
    ).status_code == 201
    assert (
        await _register(client, geo, email="r2@test.dev", phone="+51955555503")
    ).status_code == 201

    blocked = await _register(client, geo, email="r3@test.dev", phone="+51955555504")
    assert blocked.status_code == 429
    assert "Demasiados registros" in blocked.json()["detail"]


async def test_varying_email_does_not_bypass_limit(client, geo, monkeypatch):
    _low_limit(monkeypatch, "app.domains.auth.service", max_attempts=2)

    for index in range(2):
        response = await _register(
            client, geo, email=f"vary{index}@test.dev", phone=f"+5195555561{index}"
        )
        assert response.status_code == 201, response.text

    # Un email nuevo desde la misma IP sigue bloqueado.
    blocked = await _register(client, geo, email="vary.new@test.dev", phone="+51955555599")
    assert blocked.status_code == 429


async def test_different_ips_are_independent(client, geo, monkeypatch):
    _low_limit(monkeypatch, "app.domains.auth.service", max_attempts=1)

    first = await _register(client, geo, email="ip1@test.dev", phone="+51955555505")
    assert first.status_code == 201

    same_ip = await _register(client, geo, email="ip1b@test.dev", phone="+51955555506")
    assert same_ip.status_code == 429

    other_ip = await client.post(
        "/api/v1/auth/register",
        headers={"X-Real-IP": "10.20.30.40"},
        json=register_payload(geo, email="ip2@test.dev", phone="+51955555507"),
    )
    assert other_ip.status_code == 201, other_ip.text


async def test_window_expiry_allows_new_registration():
    limiter = RegistrationRateLimiter(max_attempts=2, block_seconds=1)
    identifier = "ttl-register"
    await limiter.reserve(identifier)
    await limiter.reserve(identifier)

    with pytest.raises(TooManyRequestsError):
        await limiter.reserve(identifier)

    await asyncio.sleep(1.2)
    await limiter.reserve(identifier)  # nueva ventana: no lanza


async def test_concurrent_registrations_cannot_exceed_limit(client, geo, monkeypatch):
    _low_limit(monkeypatch, "app.domains.auth.service", max_attempts=3)

    emails = [f"race{index}@test.dev" for index in range(10)]
    responses = await asyncio.gather(
        *[
            _register(client, geo, email=email, phone=f"+5196666660{index}")
            for index, email in enumerate(emails)
        ]
    )
    codes = [response.status_code for response in responses]

    assert codes.count(201) <= 3
    assert codes.count(429) == len(codes) - codes.count(201)


async def test_oauth_complete_is_rate_limited(client, geo, monkeypatch):
    """El alta vía Google también pasa por el limiter de registro."""
    _low_limit(monkeypatch, "app.domains.auth.oauth_service", max_attempts=1)

    payload = {
        "oauth_token": "tokonboardinginválidoperonoimporta",
        "full_name": "Usuario Google",
        "phone": "+51977777777",
        "role": "customer",
        "accept_terms": True,
        **geo,
    }
    first = await client.post("/api/v1/auth/oauth/complete", json=payload)
    assert first.status_code == 400  # token inválido, pero consumió la reserva

    second = await client.post("/api/v1/auth/oauth/complete", json=payload)
    assert second.status_code == 429


async def test_redis_down_returns_503_for_registration(client, geo, monkeypatch):
    monkeypatch.setattr("app.core.ratelimit.get_redis", lambda: _BrokenRedis())
    response = await _register(client, geo, email="redisdn@test.dev", phone="+51955555508")
    assert response.status_code == 503


async def test_registration_identifier_is_ip_only():
    from app.core.ratelimit import registration_identifier

    assert registration_identifier(" 10.0.0.1 ") == registration_identifier("10.0.0.1")
    assert registration_identifier("10.0.0.1") != registration_identifier("10.0.0.2")
