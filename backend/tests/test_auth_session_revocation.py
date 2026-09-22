"""Regresión: el cambio de contraseña revoca los refresh tokens previos."""

import asyncio

import pytest

from app.core.redis import get_redis
from app.core.security import decode_token
from tests.conftest import (
    CUSTOMER_EMAIL,
    PASSWORD,
    TECHNICIAN_EMAIL,
    auth_header,
    login,
)

pytestmark = pytest.mark.asyncio

NEW_PASSWORD = "nuevaClave123"


async def _change_password(client, access_token: str) -> None:
    response = await client.post(
        "/api/v1/users/me/change-password",
        headers=auth_header(access_token),
        json={"current_password": PASSWORD, "new_password": NEW_PASSWORD},
    )
    assert response.status_code == 200, response.text


async def _refresh(client, refresh_token: str):
    return await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})


async def test_refresh_works_before_change(client, customer_token):
    tokens = await login(client, CUSTOMER_EMAIL, PASSWORD)
    rotated = await _refresh(client, tokens["refresh_token"])
    assert rotated.status_code == 200
    assert rotated.json()["access_token"]


async def test_password_change_revokes_all_previous_refresh_tokens(client, customer_token):
    first = await login(client, CUSTOMER_EMAIL, PASSWORD)
    second = await login(client, CUSTOMER_EMAIL, PASSWORD)

    await _change_password(client, customer_token)

    for tokens in (first, second):
        revoked = await _refresh(client, tokens["refresh_token"])
        assert revoked.status_code == 401, revoked.text


async def test_new_login_after_change_can_refresh(client, customer_token):
    await _change_password(client, customer_token)

    fresh = await login(client, CUSTOMER_EMAIL, NEW_PASSWORD)
    rotated = await _refresh(client, fresh["refresh_token"])
    assert rotated.status_code == 200, rotated.text


async def test_logout_only_revokes_presented_token(client, customer_token):
    first = await login(client, CUSTOMER_EMAIL, PASSWORD)
    second = await login(client, CUSTOMER_EMAIL, PASSWORD)

    logged_out = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": first["refresh_token"]}
    )
    assert logged_out.status_code == 200

    assert (await _refresh(client, first["refresh_token"])).status_code == 401
    assert (await _refresh(client, second["refresh_token"])).status_code == 200


async def test_change_password_does_not_revoke_other_users(
    client, customer_token, technician_token
):
    other = await login(client, TECHNICIAN_EMAIL, PASSWORD)

    await _change_password(client, customer_token)

    still_valid = await _refresh(client, other["refresh_token"])
    assert still_valid.status_code == 200, still_valid.text


async def test_natural_expiry_is_respected(client, customer_token):
    tokens = await login(client, CUSTOMER_EMAIL, PASSWORD)
    jti = decode_token(tokens["refresh_token"])["jti"]
    await get_redis().delete(f"refresh:{jti}")

    assert (await _refresh(client, tokens["refresh_token"])).status_code == 401


async def test_concurrent_refresh_and_password_change_leaves_no_usable_session(
    client, customer_token
):
    tokens = await login(client, CUSTOMER_EMAIL, PASSWORD)

    refresh_task = _refresh(client, tokens["refresh_token"])
    change_task = _change_password(client, customer_token)
    refreshed, _ = await asyncio.gather(refresh_task, change_task)

    # Si el refresh alcanzó a emitir tokens, deben quedar inválidos tras el
    # cambio de contraseña (no debe sobrevivir ninguna sesión previa).
    if refreshed.status_code == 200:
        minted = refreshed.json()["refresh_token"]
        again = await _refresh(client, minted)
        assert again.status_code == 401
    else:
        assert refreshed.status_code == 401
