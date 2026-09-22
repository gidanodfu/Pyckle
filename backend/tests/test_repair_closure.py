"""Ciclo de reparación: pruebas por comportamiento."""

import pytest

from tests.conftest import (
    auth_header,
    complete_order,
    drive_order,
    new_order,
)

pytestmark = pytest.mark.asyncio


async def test_cost_items_visibility(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)

    for payload in (
        {
            "kind": "part",
            "description": "Repuesto visible",
            "amount": 60,
            "visible_to_customer": True,
        },
        {
            "kind": "labor",
            "description": "Costo interno",
            "amount": 30,
            "visible_to_customer": False,
        },
    ):
        response = await client.post(
            f"/api/v1/orders/{order_id}/costs",
            headers=auth_header(technician_token),
            json=payload,
        )
        assert response.status_code == 201, response.text

    tech_costs = await client.get(
        f"/api/v1/orders/{order_id}/costs", headers=auth_header(technician_token)
    )
    assert len(tech_costs.json()) == 2

    customer_costs = await client.get(
        f"/api/v1/orders/{order_id}/costs", headers=auth_header(customer_token)
    )
    assert len(customer_costs.json()) == 1
    assert customer_costs.json()[0]["visible_to_customer"] is True

    detail = await client.get(f"/api/v1/orders/{order_id}", headers=auth_header(customer_token))
    assert detail.json()["technician_notes"] is None


async def test_not_repairable_requires_reason_and_generates_report(
    client, customer_token, technician_ready
):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "diagnosis")

    invalid = await client.post(
        f"/api/v1/orders/{order_id}/not-repairable",
        headers=auth_header(technician_token),
        json={"reason": "corto", "diagnosis": "Diagnóstico válido y suficiente."},
    )
    assert invalid.status_code == 422

    response = await client.post(
        f"/api/v1/orders/{order_id}/not-repairable",
        headers=auth_header(technician_token),
        json={
            "reason": "La placa principal presenta daño irreparable por corrosión.",
            "diagnosis": "Diagnóstico técnico detallado del daño encontrado.",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "completed"
    assert body["result"] == "not_repairable"
    assert body["report"] is not None


async def test_cancel_rules(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, first_order = await new_order(client, customer_token, technician_token, specialty_id)
    cancelled = await client.post(
        f"/api/v1/orders/{first_order}/cancel",
        headers=auth_header(customer_token),
        json={"reason": "Ya no necesito el servicio"},
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["result"] == "cancelled"

    _, _, second_order = await new_order(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, second_order, "in_repair")
    too_late = await client.post(
        f"/api/v1/orders/{second_order}/cancel",
        headers=auth_header(customer_token),
        json={"reason": "Quiero cancelar ahora"},
    )
    assert too_late.status_code == 403

    technician_cancel = await client.post(
        f"/api/v1/orders/{second_order}/cancel",
        headers=auth_header(technician_token),
        json={"reason": "No es posible continuar"},
    )
    assert technician_cancel.status_code == 200


async def test_complete_requires_receipt(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    too_early = await complete_order(client, technician_token, order_id)
    assert too_early.status_code == 400


async def test_complete_is_idempotent(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "ready")

    first = await complete_order(client, technician_token, order_id)
    assert first.status_code == 200, first.text
    second = await complete_order(client, technician_token, order_id)
    assert second.status_code == 200, second.text
    assert second.json()["report"]["id"] == first.json()["report"]["id"]

    reports = await client.get(
        f"/api/v1/orders/{order_id}/reports", headers=auth_header(technician_token)
    )
    assert len(reports.json()) == 1
