"""Reglas de modalidad de atención del técnico (local / domicilio / ambas)."""

import pytest
from sqlalchemy import select

from app.db import demo_seed
from app.models.technician import Technician
from tests.conftest import PASSWORD, TestSession, auth_header, login, register_payload

pytestmark = pytest.mark.asyncio


def _technician_payload(geo: dict[str, str], email: str, **extra) -> dict:
    return register_payload(
        geo,
        email=email,
        role="technician",
        full_name="Técnico de Prueba",
        phone=extra.pop("phone", "+51933333331"),
        **extra,
    )


async def _profile(client, token: str) -> dict:
    response = await client.get("/api/v1/technicians/me", headers=auth_header(token))
    assert response.status_code == 200, response.text
    return response.json()


async def _patch(client, token: str, **payload):
    return await client.patch("/api/v1/technicians/me", headers=auth_header(token), json=payload)


async def test_register_home_only_discards_workshop_address(client, geo):
    payload = _technician_payload(
        geo,
        "home.only@test.dev",
        offers_home_service=True,
        offers_workshop_service=False,
        workshop_address="Av. falsa 123",
    )
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text

    token = (await login(client, "home.only@test.dev", PASSWORD))["access_token"]
    profile = await _profile(client, token)
    assert profile["offers_home_service"] is True
    assert profile["offers_workshop_service"] is False
    assert profile["workshop_address"] is None


async def test_register_defaults_to_home_service(client, geo):
    payload = _technician_payload(geo, "default.home@test.dev")
    payload.pop("offers_home_service", None)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text

    token = (await login(client, "default.home@test.dev", PASSWORD))["access_token"]
    profile = await _profile(client, token)
    assert profile["offers_home_service"] is True
    assert profile["offers_workshop_service"] is False


async def test_register_workshop_only_requires_address(client, geo):
    payload = _technician_payload(
        geo, "workshop.only@test.dev", offers_home_service=False, offers_workshop_service=True
    )
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400

    payload["workshop_address"] = "Jr. Taller 456"
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text

    token = (await login(client, "workshop.only@test.dev", PASSWORD))["access_token"]
    profile = await _profile(client, token)
    assert profile["offers_home_service"] is False
    assert profile["offers_workshop_service"] is True
    assert profile["workshop_address"] == "Jr. Taller 456"


async def test_register_requires_at_least_one_modality(client, geo):
    payload = _technician_payload(
        geo, "no.modality@test.dev", offers_home_service=False, offers_workshop_service=False
    )
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400


async def test_register_both_requires_address(client, geo):
    payload = _technician_payload(
        geo, "both@test.dev", offers_home_service=True, offers_workshop_service=True
    )
    assert (await client.post("/api/v1/auth/register", json=payload)).status_code == 400

    payload["workshop_address"] = "Calle Ambos 789"
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text

    token = (await login(client, "both@test.dev", PASSWORD))["access_token"]
    profile = await _profile(client, token)
    assert profile["offers_home_service"] is True
    assert profile["offers_workshop_service"] is True
    assert profile["workshop_address"] == "Calle Ambos 789"


async def test_patch_validates_final_state(client, geo):
    payload = _technician_payload(geo, "patch.modality@test.dev")
    assert (await client.post("/api/v1/auth/register", json=payload)).status_code == 201
    token = (await login(client, "patch.modality@test.dev", PASSWORD))["access_token"]

    assert (await _patch(client, token, offers_workshop_service=True)).status_code == 400
    assert (await _patch(client, token, offers_home_service=False)).status_code == 400

    response = await _patch(
        client, token, offers_workshop_service=True, workshop_address="Av. Nueva 321"
    )
    assert response.status_code == 200, response.text
    assert response.json()["offers_workshop_service"] is True
    assert response.json()["workshop_address"] == "Av. Nueva 321"

    response = await _patch(client, token, offers_workshop_service=False)
    assert response.status_code == 200, response.text
    assert response.json()["offers_home_service"] is True
    assert response.json()["offers_workshop_service"] is False
    assert response.json()["workshop_address"] is None


async def test_patch_workshop_only_to_home_only(client, geo):
    payload = _technician_payload(
        geo,
        "switch.modality@test.dev",
        offers_home_service=False,
        offers_workshop_service=True,
        workshop_address="Jr. Cambio 654",
    )
    assert (await client.post("/api/v1/auth/register", json=payload)).status_code == 201
    token = (await login(client, "switch.modality@test.dev", PASSWORD))["access_token"]

    response = await _patch(client, token, offers_home_service=True, offers_workshop_service=False)
    assert response.status_code == 200, response.text
    assert response.json()["offers_home_service"] is True
    assert response.json()["offers_workshop_service"] is False
    assert response.json()["workshop_address"] is None


async def test_demo_seed_technicians_have_valid_modality(monkeypatch):
    monkeypatch.setattr(demo_seed.settings, "demo_password", "demo-password-123", raising=False)
    async with TestSession() as session:
        from app.models.technician import Specialty

        specialties = list((await session.execute(select(Specialty))).scalars().all())
        await demo_seed.seed_demo(session, specialties)

    async with TestSession() as session:
        technicians = list((await session.execute(select(Technician))).scalars().all())

    assert technicians
    for technician in technicians:
        assert technician.offers_home_service or technician.offers_workshop_service
        if technician.offers_workshop_service:
            assert technician.workshop_address
        else:
            assert technician.workshop_address is None
