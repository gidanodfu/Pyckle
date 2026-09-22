"""Revocación inmediata de access/refresh al cambiar la contraseña (claim tv)."""

import pytest

from tests.conftest import (
    CUSTOMER_EMAIL,
    PASSWORD,
    TECHNICIAN_EMAIL,
    auth_header,
    login,
)

pytestmark = pytest.mark.asyncio

NEW_PASSWORD = "nuevaClave12345"


async def _change_password(client, token: str) -> None:
    response = await client.post(
        "/api/v1/users/me/change-password",
        headers=auth_header(token),
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
    )
    assert response.status_code == 200, response.text


async def test_access_and_refresh_revoked_after_password_change(client, customer_token):
    tokens = await login(client, CUSTOMER_EMAIL, PASSWORD)
    old_access = tokens["access_token"]
    old_refresh = tokens["refresh_token"]

    await _change_password(client, old_access)

    # El access emitido antes del cambio deja de valer de inmediato.
    stale_access = await client.get("/api/v1/users/me", headers=auth_header(old_access))
    assert stale_access.status_code == 401

    # El refresh asociado tampoco sirve.
    stale_refresh = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert stale_refresh.status_code == 401

    # Una sesión nueva con la contraseña nueva funciona.
    new_tokens = await login(client, CUSTOMER_EMAIL, NEW_PASSWORD)
    me = await client.get("/api/v1/users/me", headers=auth_header(new_tokens["access_token"]))
    assert me.status_code == 200


async def test_other_users_sessions_are_unaffected(client, customer_token, technician_token):
    tech_tokens = await login(client, TECHNICIAN_EMAIL, PASSWORD)

    await _change_password(client, customer_token)

    # La revocación es por usuario: el técnico conserva access y refresh.
    tech_access = await client.get(
        "/api/v1/users/me", headers=auth_header(tech_tokens["access_token"])
    )
    assert tech_access.status_code == 200

    tech_refresh = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tech_tokens["refresh_token"]}
    )
    assert tech_refresh.status_code == 200


async def test_missing_tv_is_treated_as_version_zero():
    """Tokens previos a la columna (sin ``tv``) equivalen a la versión 0."""

    class _User:
        token_version = 0

    from app.core.dependencies import _is_revoked

    assert _is_revoked({}, _User()) is False
    _User.token_version = 1
    assert _is_revoked({}, _User()) is True
