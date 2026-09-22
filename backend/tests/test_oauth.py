"""OAuth 2.0 server-side con Google (Google mockeado; sin red)."""

import asyncio
import json
import time
import uuid
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import jwt as pyjwt
import pytest
from httpx import ASGITransport, AsyncClient
from jwt.algorithms import RSAAlgorithm

from app.core.config import get_settings
from app.core.redis import get_redis
from app.domains.auth.oauth.base import OAuthError, OAuthIdentity
from app.domains.auth.oauth.google import GoogleOAuthProvider
from app.main import app
from app.models.enums import RoleName
from app.models.oauth import OAuthAccount
from tests.conftest import ADMIN_EMAIL, PASSWORD, auth_header, create_user, register_payload

pytestmark = pytest.mark.asyncio

GOOGLE_LOCATION = "https://accounts.google.com/o/oauth2/v2/auth"

IDENTITY = OAuthIdentity(
    provider="google",
    provider_user_id="google-user-1",
    email="nuevo.google@test.dev",
    email_verified=True,
    name="Nuevo Google",
)


def _fake_google(monkeypatch, identity):
    async def exchange_code(self, *, code, code_verifier):
        return {"id_token": "fake"}

    async def get_identity(self, tokens, *, nonce):
        return identity

    monkeypatch.setattr(GoogleOAuthProvider, "exchange_code", exchange_code)
    monkeypatch.setattr(GoogleOAuthProvider, "get_identity", get_identity)


async def _begin(client, intent="login"):
    response = await client.get(f"/api/v1/auth/google?intent={intent}", follow_redirects=False)
    assert response.status_code == 302, response.text
    location = response.headers["location"]
    assert location.startswith(GOOGLE_LOCATION)
    return parse_qs(urlparse(location).query)


async def _callback(client, state, code="auth-code"):
    return await client.get(
        f"/api/v1/auth/google/callback?code={code}&state={state}",
        follow_redirects=False,
    )


def _onboarding_payload(geo, token, **extra):
    return {
        "oauth_token": token,
        "full_name": "Nuevo Google",
        "phone": "+51912345678",
        "role": "customer",
        "accept_terms": True,
        **geo,
        **extra,
    }


async def _onboard(client, monkeypatch, geo, identity=IDENTITY):
    _fake_google(monkeypatch, identity)
    query = await _begin(client)
    response = await _callback(client, query["state"][0])
    assert "/register?oauth_token=" in response.headers["location"]
    token = parse_qs(urlparse(response.headers["location"]).query)["oauth_token"][0]
    created = await client.post("/api/v1/auth/oauth/complete", json=_onboarding_payload(geo, token))
    assert created.status_code == 200, created.text
    return created.json()


async def _issue_onboarding_token(client, monkeypatch, identity=IDENTITY, intent="register"):
    """Completa el boundary de Google y devuelve el token de onboarding."""
    _fake_google(monkeypatch, identity)
    query = await _begin(client, intent=intent)
    response = await _callback(client, query["state"][0])
    assert "/register?oauth_token=" in response.headers["location"], response.headers["location"]
    return parse_qs(urlparse(response.headers["location"]).query)["oauth_token"][0]


async def test_providers_and_disabled(client, monkeypatch):
    providers = await client.get("/api/v1/auth/providers")
    assert providers.status_code == 200
    assert providers.json() == {"google": True}

    monkeypatch.setattr(
        "app.domains.auth.router.settings",
        SimpleNamespace(google_oauth_enabled=False, frontend_url="http://localhost:5173"),
    )
    assert (await client.get("/api/v1/auth/providers")).json() == {"google": False}
    disabled = await client.get("/api/v1/auth/google", follow_redirects=False)
    assert disabled.status_code == 404


async def test_begin_redirects_to_google(client):
    query = await _begin(client)
    assert query["client_id"] == ["test-google-client"]
    assert query["response_type"] == ["code"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["state"][0]
    assert query["nonce"][0]
    assert query["code_challenge"][0]


async def test_callback_requires_binding_cookie(client, monkeypatch):
    """Un state iniciado en otro navegador no puede completarse (login CSRF)."""
    _fake_google(monkeypatch, IDENTITY)
    query = await _begin(client)

    # "Otro navegador": cliente nuevo sin la cookie de binding.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as other:
        response = await _callback(other, query["state"][0])
    assert response.status_code == 302
    assert "oauth_error=oauth_state_invalid" in response.headers["location"]

    # El navegador que inició el flujo sí completa (nuevo state).
    query = await _begin(client)
    response = await _callback(client, query["state"][0])
    assert "/register?oauth_token=" in response.headers["location"]


async def test_callback_invalid_state_redirects_with_error(client, monkeypatch):
    _fake_google(monkeypatch, IDENTITY)
    response = await _callback(client, "estado-invalido")
    assert response.status_code == 302
    location = response.headers["location"]
    assert "/login?oauth_error=oauth_state_invalid" in location
    # El redirect nunca lleva datos sensibles.
    assert IDENTITY.email not in location
    for needle in ("id_token", "access_token", "refresh_token", "state=", "nonce="):
        assert needle not in location


async def test_new_identity_onboarding_then_complete(client, monkeypatch, geo):
    _fake_google(monkeypatch, IDENTITY)
    query = await _begin(client, intent="register")
    response = await _callback(client, query["state"][0])
    assert "/register?oauth_token=" in response.headers["location"]
    token = parse_qs(urlparse(response.headers["location"]).query)["oauth_token"][0]

    payload = _onboarding_payload(geo, token)
    created = await client.post("/api/v1/auth/oauth/complete", json=payload)
    assert created.status_code == 200, created.text
    tokens = created.json()

    me = await client.get("/api/v1/auth/me", headers=auth_header(tokens["access_token"]))
    assert me.status_code == 200
    assert me.json()["user"]["email"] == IDENTITY.email
    assert any(role["name"] == "customer" for role in me.json()["user"]["roles"])

    reused = await client.post("/api/v1/auth/oauth/complete", json=payload)
    assert reused.status_code == 400


async def test_onboarding_rejects_admin_role(client, monkeypatch, geo):
    _fake_google(monkeypatch, IDENTITY)
    query = await _begin(client)
    response = await _callback(client, query["state"][0])
    token = parse_qs(urlparse(response.headers["location"]).query)["oauth_token"][0]
    payload = _onboarding_payload(geo, token, role="admin")
    rejected = await client.post("/api/v1/auth/oauth/complete", json=payload)
    assert rejected.status_code == 422


async def test_existing_account_logs_in_and_exchange_is_single_use(client, monkeypatch, geo):
    await _onboard(client, monkeypatch, geo)

    _fake_google(monkeypatch, IDENTITY)
    query = await _begin(client)
    response = await _callback(client, query["state"][0])
    assert "/auth/callback?code=" in response.headers["location"]
    otp = parse_qs(urlparse(response.headers["location"]).query)["code"][0]

    exchanged = await client.post("/api/v1/auth/oauth/exchange", json={"code": otp})
    assert exchanged.status_code == 200
    assert exchanged.json()["access_token"]
    reused = await client.post("/api/v1/auth/oauth/exchange", json={"code": otp})
    assert reused.status_code == 400
    assert reused.json()["code"] == "oauth_exchange_expired"


async def test_existing_email_without_link_is_rejected(client, monkeypatch, geo):
    await client.post(
        "/api/v1/auth/register",
        json=register_payload(geo, email=IDENTITY.email, phone="+51911111001"),
    )
    _fake_google(monkeypatch, IDENTITY)
    query = await _begin(client)
    response = await _callback(client, query["state"][0])
    location = response.headers["location"]
    assert "/login?oauth_error=oauth_email_already_registered" in location
    # No se crea ningún OAuthAccount por vinculación implícita.
    assert IDENTITY.email not in location


async def test_admin_linked_account_rejected(client, monkeypatch, session):
    admin = await create_user(ADMIN_EMAIL, PASSWORD, RoleName.ADMIN)
    session.add(
        OAuthAccount(
            user_id=admin.id,
            provider="google",
            provider_user_id=IDENTITY.provider_user_id,
            email=ADMIN_EMAIL,
        )
    )
    await session.commit()

    _fake_google(monkeypatch, IDENTITY)
    query = await _begin(client)
    response = await _callback(client, query["state"][0])
    assert "/login?oauth_error=" in response.headers["location"]


# ------------------------------------------------- onboarding (TTL y consumo)


async def test_onboarding_ttl_is_120_seconds(client, monkeypatch):
    token = await _issue_onboarding_token(client, monkeypatch)
    ttl = await get_redis().ttl(f"oauth:onboarding:{token}")
    assert 0 < ttl <= 120, ttl
    assert get_settings().oauth_onboarding_ttl_seconds == 120


async def test_onboarding_peek_is_non_consuming_and_minimal(client, monkeypatch, geo):
    token = await _issue_onboarding_token(client, monkeypatch)

    first = await client.post("/api/v1/auth/oauth/onboarding", json={"oauth_token": token})
    assert first.status_code == 200, first.text
    body = first.json()
    assert body == {"email": IDENTITY.email, "full_name": IDENTITY.name, "provider": "google"}
    for secret in ("access_token", "refresh_token", "id_token", "code", "state", "nonce"):
        assert secret not in body

    # El peek no consume: se puede consultar de nuevo y luego completar.
    second = await client.post("/api/v1/auth/oauth/onboarding", json={"oauth_token": token})
    assert second.status_code == 200
    created = await client.post("/api/v1/auth/oauth/complete", json=_onboarding_payload(geo, token))
    assert created.status_code == 200, created.text


async def test_onboarding_peek_rejects_unknown_token(client):
    response = await client.post(
        "/api/v1/auth/oauth/onboarding", json={"oauth_token": "inexistente"}
    )
    assert response.status_code == 400
    assert response.json()["code"] == "oauth_onboarding_expired"


async def test_onboarding_token_expires(client, monkeypatch, geo):
    token = await _issue_onboarding_token(client, monkeypatch)
    # Simula el paso del TTL: la clave deja de existir.
    await get_redis().expire(f"oauth:onboarding:{token}", 0)

    response = await client.post(
        "/api/v1/auth/oauth/complete", json=_onboarding_payload(geo, token)
    )
    assert response.status_code == 400
    assert response.json()["code"] == "oauth_onboarding_expired"
    assert response.json().get("details") is None


async def test_onboarding_validation_failure_does_not_consume_token(client, monkeypatch, geo):
    token = await _issue_onboarding_token(client, monkeypatch)
    bad_location = _onboarding_payload(geo, token, district_id=str(uuid.uuid4()))

    rejected = await client.post("/api/v1/auth/oauth/complete", json=bad_location)
    assert rejected.status_code == 400

    # El token sigue vigente: el usuario puede corregir el formulario.
    retry = await client.post("/api/v1/auth/oauth/complete", json=_onboarding_payload(geo, token))
    assert retry.status_code == 200, retry.text


async def test_onboarding_duplicate_phone_does_not_consume_token(client, monkeypatch, geo):
    reuse_phone = "+51911111999"
    await client.post(
        "/api/v1/auth/register",
        json=register_payload(geo, email="ocupado@test.dev", phone=reuse_phone),
    )
    token = await _issue_onboarding_token(client, monkeypatch)

    rejected = await client.post(
        "/api/v1/auth/oauth/complete",
        json=_onboarding_payload(geo, token, phone=reuse_phone),
    )
    assert rejected.status_code == 409
    assert rejected.json()["code"] == "phone_already_registered"

    retry = await client.post(
        "/api/v1/auth/oauth/complete",
        json=_onboarding_payload(geo, token, phone="+51911111000"),
    )
    assert retry.status_code == 200, retry.text


async def test_onboarding_concurrent_consumption_only_one_wins(client, monkeypatch, geo):
    token = await _issue_onboarding_token(client, monkeypatch)
    payload = _onboarding_payload(geo, token)

    responses = await asyncio.gather(
        client.post("/api/v1/auth/oauth/complete", json=payload),
        client.post("/api/v1/auth/oauth/complete", json=payload),
    )
    statuses = sorted(response.status_code for response in responses)
    assert statuses == [200, 400], [response.text for response in responses]


async def test_onboarding_email_registered_after_issuance_is_conflict(client, monkeypatch, geo):
    token = await _issue_onboarding_token(client, monkeypatch)
    # El email de Google es ocupado localmente antes de completar el onboarding.
    registered = await client.post(
        "/api/v1/auth/register",
        json=register_payload(geo, email=IDENTITY.email, phone="+51911111007"),
    )
    assert registered.status_code == 201, registered.text

    response = await client.post(
        "/api/v1/auth/oauth/complete", json=_onboarding_payload(geo, token)
    )
    assert response.status_code == 409
    assert response.json()["code"] == "email_already_registered"


# --------------------------------------------------- validación del proveedor


def _rsa_private_key():
    from cryptography.hazmat.primitives.asymmetric import rsa

    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _token(key, **overrides):
    claims = {
        "iss": "https://accounts.google.com",
        "aud": "test-google-client",
        "exp": int(time.time()) + 300,
        "sub": "1234567890",
        "email": "persona@gmail.com",
        "email_verified": True,
        "nonce": "nonce-1",
        "name": "Persona Google",
    }
    claims.update(overrides)
    return pyjwt.encode(claims, key, algorithm="RS256", headers={"kid": "kid-1"})


async def _provider_with_key(monkeypatch, key):
    jwk = json.loads(RSAAlgorithm.to_jwk(key.public_key()))
    jwk["kid"] = "kid-1"
    provider = GoogleOAuthProvider()

    async def fake_jwks():
        return {"keys": [jwk]}

    monkeypatch.setattr(provider, "_get_jwks", fake_jwks)
    return provider


async def test_provider_accepts_valid_token(monkeypatch):
    key = _rsa_private_key()
    provider = await _provider_with_key(monkeypatch, key)
    identity = await provider.get_identity({"id_token": _token(key)}, nonce="nonce-1")
    assert identity.email == "persona@gmail.com"
    assert identity.provider == "google"


@pytest.mark.parametrize(
    "overrides",
    [
        {"iss": "https://evil.example"},
        {"aud": "otro-cliente"},
        {"nonce": "incorrecto"},
        {"email_verified": False},
        {"sub": None},
        {"exp": int(time.time()) - 10},
    ],
)
async def test_provider_rejects_invalid_claims(monkeypatch, overrides):
    key = _rsa_private_key()
    provider = await _provider_with_key(monkeypatch, key)
    with pytest.raises(OAuthError):
        await provider.get_identity({"id_token": _token(key, **overrides)}, nonce="nonce-1")


async def test_provider_rejects_bad_signature(monkeypatch):
    key = _rsa_private_key()
    provider = await _provider_with_key(monkeypatch, key)
    other = _rsa_private_key()
    with pytest.raises(OAuthError):
        await provider.get_identity({"id_token": _token(other)}, nonce="nonce-1")
