"""Regresión: el cierre no puede fijar un precio superior al aprobado."""

import pytest

from tests.conftest import auth_header, drive_order, new_order

pytestmark = pytest.mark.asyncio

APPROVED_PRICE = 150.0
READY_FROM_DIAGNOSIS = ["in_repair", "testing", "ready"]


async def _set_statuses(client, token: str, order_id: str, statuses: list[str]) -> None:
    for status in statuses:
        response = await client.patch(
            f"/api/v1/orders/{order_id}/status",
            headers=auth_header(token),
            json={"status": status},
        )
        assert response.status_code == 200, response.text


async def _complete(client, token: str, order_id: str, final_price=None):
    payload = {
        "diagnosis": "Diagnóstico técnico de prueba con suficiente detalle.",
        "work_performed": "Trabajo realizado de prueba.",
        "tests_performed": "Pruebas realizadas de prueba.",
    }
    if final_price is not None:
        payload["final_price"] = final_price
    return await client.post(
        f"/api/v1/orders/{order_id}/complete",
        headers=auth_header(token),
        json=payload,
    )


async def _approved_order(client, customer_token, technician_token, specialty_id):
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "ready")
    return order_id


async def test_complete_with_approved_price_succeeds(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    order_id = await _approved_order(client, customer_token, technician_token, specialty_id)

    response = await _complete(client, technician_token, order_id, APPROVED_PRICE)
    assert response.status_code == 200, response.text
    assert float(response.json()["final_price"]) == APPROVED_PRICE


async def test_complete_without_price_keeps_approved_price(
    client, customer_token, technician_ready
):
    technician_token, specialty_id = technician_ready
    order_id = await _approved_order(client, customer_token, technician_token, specialty_id)

    response = await _complete(client, technician_token, order_id)
    assert response.status_code == 200, response.text
    assert float(response.json()["final_price"]) == APPROVED_PRICE


async def test_complete_with_unapproved_increase_is_rejected(
    client, customer_token, technician_ready
):
    technician_token, specialty_id = technician_ready
    order_id = await _approved_order(client, customer_token, technician_token, specialty_id)

    rejected = await _complete(client, technician_token, order_id, 9999)
    assert rejected.status_code == 400, rejected.text

    order = await client.get(f"/api/v1/orders/{order_id}", headers=auth_header(customer_token))
    assert float(order.json()["final_price"]) == APPROVED_PRICE
    assert order.json()["status"] == "ready"


async def test_complete_with_lower_unapproved_price_is_rejected(
    client, customer_token, technician_ready
):
    technician_token, specialty_id = technician_ready
    order_id = await _approved_order(client, customer_token, technician_token, specialty_id)

    rejected = await _complete(client, technician_token, order_id, 100)
    assert rejected.status_code == 400, rejected.text


async def test_pending_price_change_blocks_complete(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "diagnosis")

    proposal = await client.post(
        f"/api/v1/orders/{order_id}/price-changes",
        headers=auth_header(technician_token),
        json={"new_price": 9999, "reason": "Se detectó un daño adicional en la placa."},
    )
    assert proposal.status_code == 201, proposal.text

    blocked = await _complete(client, technician_token, order_id, 9999)
    assert blocked.status_code == 409, blocked.text


async def test_rejected_price_change_cannot_be_used(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "diagnosis")

    proposal = await client.post(
        f"/api/v1/orders/{order_id}/price-changes",
        headers=auth_header(technician_token),
        json={"new_price": 9999, "reason": "Costo adicional no autorizado."},
    )
    change_id = proposal.json()["id"]
    reject = await client.post(
        f"/api/v1/orders/{order_id}/price-changes/{change_id}/reject",
        headers=auth_header(customer_token),
        json={"note": "No autorizado"},
    )
    assert reject.status_code == 200, reject.text

    # Tras el rechazo el estado vuelve a diagnosis.
    await _set_statuses(client, technician_token, order_id, READY_FROM_DIAGNOSIS)
    rejected = await _complete(client, technician_token, order_id, 9999)
    assert rejected.status_code == 400, rejected.text


async def test_approved_price_change_allows_matching_completion(
    client, customer_token, technician_ready
):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "diagnosis")

    proposal = await client.post(
        f"/api/v1/orders/{order_id}/price-changes",
        headers=auth_header(technician_token),
        json={"new_price": 9999, "reason": "Repuesto importado de alto costo."},
    )
    change_id = proposal.json()["id"]
    approve = await client.post(
        f"/api/v1/orders/{order_id}/price-changes/{change_id}/approve",
        headers=auth_header(customer_token),
        json={},
    )
    assert approve.status_code == 200, approve.text

    # Tras aprobar, el estado sigue en waiting_customer hasta retomar el trabajo.
    await _set_statuses(client, technician_token, order_id, READY_FROM_DIAGNOSIS)
    completed = await _complete(client, technician_token, order_id, 9999)
    assert completed.status_code == 200, completed.text
    assert float(completed.json()["final_price"]) == 9999.0


async def test_customer_cannot_complete(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    order_id = await _approved_order(client, customer_token, technician_token, specialty_id)

    forbidden = await _complete(client, customer_token, order_id, APPROVED_PRICE)
    assert forbidden.status_code == 403
