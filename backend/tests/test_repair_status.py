"""Ciclo de reparación: pruebas por comportamiento."""

import pytest

from tests.conftest import (
    auth_header,
    new_order,
    other_verified_technician,
)

pytestmark = pytest.mark.asyncio


async def test_status_machine_rejects_invalid_transitions(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)

    jump = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers=auth_header(technician_token),
        json={"status": "in_repair"},
    )
    assert jump.status_code == 400

    terminal = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers=auth_header(technician_token),
        json={"status": "cancelled"},
    )
    assert terminal.status_code == 400


async def test_receipt_sets_timestamp_and_progresses(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)

    received = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers=auth_header(technician_token),
        json={"status": "received"},
    )
    assert received.status_code == 200, received.text
    assert received.json()["received_at"] is not None


async def test_only_assigned_technician_manages(
    client, customer_token, technician_ready, geo, admin_token
):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)

    intruder = await other_verified_technician(
        client,
        geo,
        email="lifecycle.intruso@test.dev",
        phone="+51977777771",
        specialty_id=specialty_id,
    )
    forbidden = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers=auth_header(intruder),
        json={"status": "received"},
    )
    assert forbidden.status_code == 403

    customer_forbidden = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers=auth_header(customer_token),
        json={"status": "received"},
    )
    assert customer_forbidden.status_code == 403

    # El administrador supervisa en solo lectura: no puede gestionar.
    admin_forbidden = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers=auth_header(admin_token),
        json={"status": "received"},
    )
    assert admin_forbidden.status_code == 403

    # El técnico asignado sí puede gestionar.
    assigned_ok = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers=auth_header(technician_token),
        json={"status": "received"},
    )
    assert assigned_ok.status_code == 200
