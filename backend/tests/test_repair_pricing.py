"""Ciclo de reparación: pruebas por comportamiento."""

import pytest

from tests.conftest import (
    auth_header,
    drive_order,
    new_order,
)

pytestmark = pytest.mark.asyncio


async def test_price_increase_requires_approval_and_blocks_work(
    client, customer_token, technician_ready
):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "diagnosis")

    proposal = await client.post(
        f"/api/v1/orders/{order_id}/price-changes",
        headers=auth_header(technician_token),
        json={"new_price": 250, "reason": "Se detectó un daño adicional en la placa."},
    )
    assert proposal.status_code == 201, proposal.text
    assert proposal.json()["status"] == "pending"

    blocked = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers=auth_header(technician_token),
        json={"status": "in_repair"},
    )
    assert blocked.status_code == 409

    change_id = proposal.json()["id"]
    approve = await client.post(
        f"/api/v1/orders/{order_id}/price-changes/{change_id}/approve",
        headers=auth_header(customer_token),
        json={},
    )
    assert approve.status_code == 200, approve.text

    order = await client.get(f"/api/v1/orders/{order_id}", headers=auth_header(customer_token))
    assert float(order.json()["final_price"]) == 250.0
    assert order.json()["has_pending_price_change"] is False


async def test_price_increase_rejection_returns_to_diagnosis(
    client, customer_token, technician_ready
):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "diagnosis")

    proposal = await client.post(
        f"/api/v1/orders/{order_id}/price-changes",
        headers=auth_header(technician_token),
        json={"new_price": 260, "reason": "Se requiere un repuesto adicional."},
    )
    change_id = proposal.json()["id"]
    reject = await client.post(
        f"/api/v1/orders/{order_id}/price-changes/{change_id}/reject",
        headers=auth_header(customer_token),
        json={"note": "No autorizo el costo"},
    )
    assert reject.status_code == 200, reject.text

    order = await client.get(f"/api/v1/orders/{order_id}", headers=auth_header(technician_token))
    assert order.json()["status"] == "diagnosis"
    assert float(order.json()["final_price"]) == 150.0


async def test_price_reduction_is_auto_approved(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "diagnosis")

    reduction = await client.post(
        f"/api/v1/orders/{order_id}/price-changes",
        headers=auth_header(technician_token),
        json={"new_price": 120, "reason": "El repuesto fue más económico de lo previsto."},
    )
    assert reduction.status_code == 201, reduction.text
    assert reduction.json()["status"] == "approved"

    order = await client.get(f"/api/v1/orders/{order_id}", headers=auth_header(customer_token))
    assert float(order.json()["final_price"]) == 120.0
