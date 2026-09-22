"""Ciclo de reparación: pruebas por comportamiento."""

import pytest

from tests.conftest import (
    auth_header,
    drive_order,
    new_order,
)

pytestmark = pytest.mark.asyncio


async def test_technician_summary_and_filters(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "received")

    summary = await client.get(
        "/api/v1/technicians/me/summary", headers=auth_header(technician_token)
    )
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert body["total"] >= 1
    assert body["by_status"].get("received", 0) >= 1
    assert body["by_specialty"]

    filtered = await client.get(
        f"/api/v1/orders?status=received&specialty_id={specialty_id}",
        headers=auth_header(technician_token),
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] >= 1
