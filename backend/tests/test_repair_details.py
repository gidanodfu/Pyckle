"""Regresión de PUT /orders/{id}/repair-details.

El endpoint fallaba con 500 por un keyword inconsistente en `_record_event`
(`visible` vs `visible_to_customer`). Estos tests ejercitan el flujo real.
"""

import uuid

import pytest

from tests.conftest import (
    PASSWORD,
    auth_header,
    complete_order,
    drive_order,
    login,
    register_payload,
    run_flow,
    verify_technician,
)

pytestmark = pytest.mark.asyncio

DETAILS = {
    "diagnosis": "Diagnóstico técnico de prueba.",
    "work_performed": "Trabajo realizado de prueba.",
    "tests_performed": "Pruebas realizadas de prueba.",
    "technician_notes": "Nota interna del técnico.",
}


async def _new_order(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    request_id, _, order_id = await run_flow(client, customer_token, technician_token, specialty_id)
    return technician_token, request_id, order_id


async def _other_verified_technician(client, geo, *, email, phone, specialty_id):
    response = await client.post(
        "/api/v1/auth/register",
        json=register_payload(
            geo, email=email, role="technician", phone=phone, full_name="Técnico Ajeno"
        ),
    )
    assert response.status_code == 201, response.text
    token = (await login(client, email, PASSWORD))["access_token"]
    await client.patch(
        "/api/v1/technicians/me",
        headers=auth_header(token),
        json={"specialty_ids": [specialty_id]},
    )
    await verify_technician(email)
    return token


async def test_assigned_technician_updates_and_persists(client, customer_token, technician_ready):
    technician_token, _, order_id = await _new_order(client, customer_token, technician_ready)

    response = await client.put(
        f"/api/v1/orders/{order_id}/repair-details",
        headers=auth_header(technician_token),
        json=DETAILS,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["diagnosis"] == DETAILS["diagnosis"]
    assert body["work_performed"] == DETAILS["work_performed"]
    assert body["technician_notes"] == DETAILS["technician_notes"]

    # Persistido.
    again = await client.get(f"/api/v1/orders/{order_id}", headers=auth_header(technician_token))
    assert again.json()["diagnosis"] == DETAILS["diagnosis"]

    # Evento interno registrado y marcado como no visible al cliente.
    assert any(
        event["event_type"] == "note" and event["visible_to_customer"] is False
        for event in again.json()["events"]
    )

    # El cliente no ve las notas internas ni el evento interno.
    customer_view = await client.get(
        f"/api/v1/orders/{order_id}", headers=auth_header(customer_token)
    )
    assert customer_view.status_code == 200
    assert customer_view.json()["technician_notes"] is None
    assert all(event["event_type"] != "note" for event in customer_view.json()["events"])


async def test_admin_cannot_update_repair_details(
    client, customer_token, technician_ready, admin_token
):
    # El administrador es de solo lectura sobre las órdenes.
    _, _, order_id = await _new_order(client, customer_token, technician_ready)
    response = await client.put(
        f"/api/v1/orders/{order_id}/repair-details",
        headers=auth_header(admin_token),
        json={"diagnosis": "Diagnóstico revisado por admin."},
    )
    assert response.status_code == 403


async def test_other_technician_cannot_update(client, customer_token, technician_ready, geo):
    _, _, order_id = await _new_order(client, customer_token, technician_ready)
    _, specialty_id = technician_ready
    intruder = await _other_verified_technician(
        client,
        geo,
        email="details.intruso@test.dev",
        phone="+51966666661",
        specialty_id=specialty_id,
    )
    response = await client.put(
        f"/api/v1/orders/{order_id}/repair-details",
        headers=auth_header(intruder),
        json=DETAILS,
    )
    assert response.status_code == 403


async def test_customer_cannot_update(client, customer_token, technician_ready):
    _, _, order_id = await _new_order(client, customer_token, technician_ready)
    response = await client.put(
        f"/api/v1/orders/{order_id}/repair-details",
        headers=auth_header(customer_token),
        json=DETAILS,
    )
    assert response.status_code == 403


async def test_missing_order_returns_404(client, technician_ready):
    technician_token, _ = technician_ready
    response = await client.put(
        f"/api/v1/orders/{uuid.uuid4()}/repair-details",
        headers=auth_header(technician_token),
        json=DETAILS,
    )
    assert response.status_code == 404


async def test_terminal_order_returns_409(client, customer_token, technician_ready):
    technician_token, _, order_id = await _new_order(client, customer_token, technician_ready)
    await drive_order(client, technician_token, order_id, "ready")
    completed = await complete_order(client, technician_token, order_id)
    assert completed.status_code == 200, completed.text

    response = await client.put(
        f"/api/v1/orders/{order_id}/repair-details",
        headers=auth_header(technician_token),
        json=DETAILS,
    )
    assert response.status_code == 409


async def test_invalid_payload_returns_422(client, customer_token, technician_ready):
    technician_token, _, order_id = await _new_order(client, customer_token, technician_ready)
    response = await client.put(
        f"/api/v1/orders/{order_id}/repair-details",
        headers=auth_header(technician_token),
        json={"diagnosis": "x" * 6000},
    )
    assert response.status_code == 422
