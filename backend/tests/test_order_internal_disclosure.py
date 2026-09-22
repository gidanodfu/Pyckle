"""Regresión: un cliente nunca recibe campos internos de su orden."""

import pytest

from tests.conftest import auth_header, new_order

pytestmark = pytest.mark.asyncio

INTERNAL_NOTE = "INTERNAL: placa sulfatada, no informar al cliente"


async def _seed_internal_data(client, technician_token: str, order_id: str) -> None:
    details = await client.put(
        f"/api/v1/orders/{order_id}/repair-details",
        headers=auth_header(technician_token),
        json={"technician_notes": INTERNAL_NOTE},
    )
    assert details.status_code == 200, details.text

    cost = await client.post(
        f"/api/v1/orders/{order_id}/costs",
        headers=auth_header(technician_token),
        json={"kind": "labor", "description": "Costo interno", "amount": 30},
    )
    assert cost.status_code == 201, cost.text


def _assert_no_internal(body: dict) -> None:
    assert body["technician_notes"] is None
    assert all(item["visible_to_customer"] for item in body["cost_items"])
    assert all(event["visible_to_customer"] for event in body["events"])


async def test_customer_cancel_hides_internal_fields(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    await _seed_internal_data(client, technician_token, order_id)

    cancelled = await client.post(
        f"/api/v1/orders/{order_id}/cancel",
        headers=auth_header(customer_token),
        json={"reason": "Ya no necesito el servicio"},
    )
    assert cancelled.status_code == 200, cancelled.text
    _assert_no_internal(cancelled.json())


async def test_customer_read_paths_never_expose_internal(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    await _seed_internal_data(client, technician_token, order_id)

    detail = await client.get(f"/api/v1/orders/{order_id}", headers=auth_header(customer_token))
    assert detail.status_code == 200
    _assert_no_internal(detail.json())

    costs = await client.get(
        f"/api/v1/orders/{order_id}/costs", headers=auth_header(customer_token)
    )
    assert costs.status_code == 200
    assert all(item["visible_to_customer"] for item in costs.json())


async def test_technician_keeps_internal_access(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    await _seed_internal_data(client, technician_token, order_id)

    detail = await client.get(f"/api/v1/orders/{order_id}", headers=auth_header(technician_token))
    assert detail.status_code == 200
    assert detail.json()["technician_notes"] == INTERNAL_NOTE
    assert any(item["visible_to_customer"] is False for item in detail.json()["cost_items"])


async def test_admin_keeps_internal_access(client, customer_token, technician_ready, admin_token):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    await _seed_internal_data(client, technician_token, order_id)

    detail = await client.get(f"/api/v1/orders/{order_id}", headers=auth_header(admin_token))
    assert detail.status_code == 200
    assert detail.json()["technician_notes"] == INTERNAL_NOTE
