import pytest

from tests.conftest import (
    PASSWORD,
    TestSession,
    auth_header,
    district_by_code,
    geo_payload,
    login,
    register_payload,
    run_flow,
)

pytestmark = pytest.mark.asyncio

SECRET_ADDRESS = "Av. Secreta 999, José Leonardo Ortiz"


async def _register_technician(client, email: str, phone: str, district_code: str = "140105"):
    async with TestSession() as db_session:
        geo = geo_payload(await district_by_code(db_session, district_code))
    response = await client.post(
        "/api/v1/auth/register",
        json=register_payload(
            geo, email=email, role="technician", phone=phone, full_name="Técnico de Prueba"
        ),
    )
    assert response.status_code == 201, response.text
    token = (await login(client, email, PASSWORD))["access_token"]
    specialty_id = (await client.get("/api/v1/specialties")).json()[0]["id"]
    await client.patch(
        "/api/v1/technicians/me",
        headers=auth_header(token),
        json={"specialty_ids": [specialty_id]},
    )
    profile = await client.get("/api/v1/technicians/me", headers=auth_header(token))
    return token, specialty_id, profile.json()["id"]


async def _create_request(client, token, specialty_id, geo, address=SECRET_ADDRESS):
    response = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(token),
        json={
            "title": "Reparación confidencial",
            "description": "La dirección exacta es privada hasta aceptar la cotización.",
            "specialty_id": specialty_id,
            "modality": "home",
            "address": address,
            **geo,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_address_hidden_until_quotation_accepted(client, customer_token, geo):
    tech_token, specialty_id, _ = await _register_technician(
        client, "priv.tech@test.dev", "+51966666661"
    )
    request_id = await _create_request(client, customer_token, specialty_id, geo)

    owner_view = await client.get(
        f"/api/v1/repair-requests/{request_id}", headers=auth_header(customer_token)
    )
    assert owner_view.json()["address"] == SECRET_ADDRESS

    tech_view = await client.get(
        f"/api/v1/repair-requests/{request_id}", headers=auth_header(tech_token)
    )
    assert tech_view.status_code == 200
    assert tech_view.json()["address"] is None

    # Un usuario ajeno no puede verla (ni siquiera la solicitud).
    other = await client.post(
        "/api/v1/auth/register",
        json=register_payload(geo, email="priv.other@test.dev", phone="+51966666662"),
    )
    assert other.status_code == 201
    other_token = (await login(client, "priv.other@test.dev", PASSWORD))["access_token"]
    forbidden = await client.get(
        f"/api/v1/repair-requests/{request_id}", headers=auth_header(other_token)
    )
    assert forbidden.status_code == 403


async def test_assigned_technician_sees_service_address(
    client, customer_token, technician_ready, geo
):
    technician_token, specialty_id = technician_ready
    request_id, _, order_id = await run_flow(client, customer_token, technician_token, specialty_id)

    request = await client.get(
        f"/api/v1/repair-requests/{request_id}", headers=auth_header(technician_token)
    )
    assert request.status_code == 200
    assert request.json()["address"] == "Av. Prueba 123"

    order = await client.get(f"/api/v1/orders/{order_id}", headers=auth_header(technician_token))
    assert order.status_code == 200
    assert order.json()["service_address"] == "Av. Prueba 123"

    # Un técnico no asignado no puede ver la solicitud aceptada.
    other_token, _, _ = await _register_technician(client, "priv.tech2@test.dev", "+51966666663")
    blocked = await client.get(
        f"/api/v1/repair-requests/{request_id}", headers=auth_header(other_token)
    )
    assert blocked.status_code == 403


async def test_public_responses_do_not_leak_email_or_address(
    client, customer_token, technician_ready, geo
):
    technician_token, specialty_id = technician_ready
    request_id = await _create_request(client, customer_token, specialty_id, geo)
    quotation = await client.post(
        "/api/v1/quotations",
        headers=auth_header(technician_token),
        json={
            "request_id": request_id,
            "price": 120,
            "preliminary_diagnosis": "Diagnóstico preliminar de prueba.",
        },
    )
    assert quotation.status_code == 201
    body = quotation.json()
    assert "address" not in body.get("technician", {})
    assert "email" not in body.get("technician", {})
    technician_id = (
        await client.get("/api/v1/technicians/me", headers=auth_header(technician_token))
    ).json()["id"]

    listing = await client.get("/api/v1/technicians?limit=50")
    assert listing.status_code == 200
    for item in listing.json()["items"]:
        assert "address" not in item
        assert "workshop_address" not in item
        assert "email" not in item

    public_profile = await client.get(f"/api/v1/technicians/{technician_id}")
    assert public_profile.status_code == 200
    assert "email" not in public_profile.json()
    assert "workshop_address" not in public_profile.json()


async def test_technician_owner_keeps_private_address(client, technician_ready):
    technician_token, _ = technician_ready
    me = await client.get("/api/v1/technicians/me", headers=auth_header(technician_token))
    assert me.status_code == 200
    # La vista del propietario sí conoce su dirección de taller (puede ser null).
    assert "workshop_address" in me.json()
