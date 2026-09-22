import pytest

from tests.conftest import auth_header, run_flow

pytestmark = pytest.mark.asyncio


async def test_accept_quotation_creates_order_and_conversation(
    client, customer_token, technician_ready
):
    technician_token, specialty_id = technician_ready
    request_id, quotation_id, order_id = await run_flow(
        client, customer_token, technician_token, specialty_id
    )

    request = await client.get(
        f"/api/v1/repair-requests/{request_id}", headers=auth_header(customer_token)
    )
    assert request.json()["status"] == "accepted"
    assert request.json()["assigned_technician"] is not None

    quotation = await client.get(
        f"/api/v1/quotations/request/{request_id}", headers=auth_header(customer_token)
    )
    statuses = [q["status"] for q in quotation.json()]
    assert statuses == ["accepted"]

    order = await client.get(f"/api/v1/orders/{order_id}", headers=auth_header(customer_token))
    assert order.status_code == 200
    assert order.json()["status"] == "awaiting_receipt"
    assert order.json()["events"][0]["new_status"] == "awaiting_receipt"

    conversations = await client.get("/api/v1/conversations", headers=auth_header(customer_token))
    assert any(c["request_id"] == request_id for c in conversations.json())


async def test_duplicate_quotation_conflict(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    response = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(customer_token),
        json={
            "title": "Solicitud duplicada",
            "description": "El tecnico no deberia poder cotizar dos veces.",
            "specialty_id": specialty_id,
        },
    )
    request_id = response.json()["id"]
    payload = {
        "request_id": request_id,
        "price": 100,
        "preliminary_diagnosis": "Diagnostico preliminar valido.",
    }
    assert (
        await client.post("/api/v1/quotations", headers=auth_header(technician_token), json=payload)
    ).status_code == 201
    duplicate = await client.post(
        "/api/v1/quotations", headers=auth_header(technician_token), json=payload
    )
    assert duplicate.status_code == 409


async def test_technician_cannot_quote_foreign_specialty(client, customer_token, technician_ready):
    technician_token, _ = technician_ready
    specialties = (await client.get("/api/v1/specialties")).json()
    other_specialty = specialties[1]["id"]
    response = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(customer_token),
        json={
            "title": "Especialidad distinta",
            "description": "El tecnico no cubre esta especialidad.",
            "specialty_id": other_specialty,
        },
    )
    request_id = response.json()["id"]
    quotation = await client.post(
        "/api/v1/quotations",
        headers=auth_header(technician_token),
        json={
            "request_id": request_id,
            "price": 100,
            "preliminary_diagnosis": "Diagnostico preliminar valido.",
        },
    )
    assert quotation.status_code == 403


async def test_accepting_rejects_other_quotations(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    response = await client.post(
        "/api/v1/repair-requests",
        headers=auth_header(customer_token),
        json={
            "title": "Varias cotizaciones",
            "description": "Al aceptar una, las demas deben rechazarse.",
            "specialty_id": specialty_id,
        },
    )
    request_id = response.json()["id"]

    first = (
        await client.post(
            "/api/v1/quotations",
            headers=auth_header(technician_token),
            json={
                "request_id": request_id,
                "price": 120,
                "preliminary_diagnosis": "Primera cotizacion valida.",
            },
        )
    ).json()

    from tests.conftest import (
        PASSWORD,
        TestSession,
        geo_payload,
        get_district,
        login,
        register_payload,
        verify_technician,
    )
    from tests.conftest import auth_header as header

    async with TestSession() as db_session:
        geo = geo_payload(await get_district(db_session))

    await client.post(
        "/api/v1/auth/register",
        json=register_payload(
            geo,
            email="tech2@test.dev",
            role="technician",
            phone="+51922222225",
            full_name="Técnico Dos",
        ),
    )
    second_token = (await login(client, "tech2@test.dev", PASSWORD))["access_token"]
    await client.patch(
        "/api/v1/technicians/me",
        headers=header(second_token),
        json={"specialty_ids": [specialty_id]},
    )
    await verify_technician("tech2@test.dev")
    second = (
        await client.post(
            "/api/v1/quotations",
            headers=header(second_token),
            json={
                "request_id": request_id,
                "price": 90,
                "preliminary_diagnosis": "Segunda cotizacion valida.",
            },
        )
    ).json()

    accepted = await client.post(
        f"/api/v1/quotations/{second['id']}/accept",
        headers=auth_header(customer_token),
        json={},
    )
    assert accepted.status_code == 200

    quotations = await client.get(
        f"/api/v1/quotations/request/{request_id}", headers=auth_header(customer_token)
    )
    statuses = {q["id"]: q["status"] for q in quotations.json()}
    assert statuses[second["id"]] == "accepted"
    assert statuses[first["id"]] == "rejected"
