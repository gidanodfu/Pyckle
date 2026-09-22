"""Regresión: no se elimina una especialidad en uso (se desactiva)."""

import pytest

from tests.conftest import auth_header

pytestmark = pytest.mark.asyncio


async def test_delete_unused_specialty_succeeds(client, admin_token):
    created = await client.post(
        "/api/v1/admin/specialties",
        headers=auth_header(admin_token),
        json={"name": "Especialidad Sin Uso"},
    )
    assert created.status_code == 200, created.text
    specialty_id = created.json()["id"]

    deleted = await client.delete(
        f"/api/v1/admin/specialties/{specialty_id}", headers=auth_header(admin_token)
    )
    assert deleted.status_code == 200, deleted.text


async def test_delete_specialty_in_use_is_blocked(client, admin_token, technician_ready):
    _, specialty_id = technician_ready

    blocked = await client.delete(
        f"/api/v1/admin/specialties/{specialty_id}", headers=auth_header(admin_token)
    )
    assert blocked.status_code == 409, blocked.text

    # La especialidad sigue existiendo (no se produjo el SET NULL que anularía
    # la validación de cotización por especialidad).
    listing = await client.get("/api/v1/specialties")
    assert specialty_id in {item["id"] for item in listing.json()}
