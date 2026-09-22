"""El administrador es estrictamente de solo lectura sobre las órdenes."""

import uuid

import pytest
from sqlalchemy import func, select

from app.models.order import (
    Order,
    OrderCostItem,
    OrderEvent,
    OrderPriceChange,
    RepairReport,
)
from tests.conftest import TestSession, auth_header, complete_order, drive_order, new_order

pytestmark = pytest.mark.asyncio


async def _snapshot(order_id: str) -> tuple:
    oid = uuid.UUID(order_id)
    async with TestSession() as session:
        order = await session.get(Order, oid)
        counts = []
        for model in (OrderEvent, OrderCostItem, OrderPriceChange, RepairReport):
            stmt = select(func.count()).select_from(model).where(model.order_id == oid)
            counts.append(int((await session.execute(stmt)).scalar_one()))
        return (
            order.status,
            order.result,
            order.final_price,
            order.completed_at,
            *counts,
        )


async def _pending_change(client, technician_token: str, order_id: str) -> str:
    response = await client.post(
        f"/api/v1/orders/{order_id}/price-changes",
        headers=auth_header(technician_token),
        json={"new_price": 9999, "reason": "Repuesto importado de alto costo."},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_admin_can_read_order_data(client, admin_token, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "diagnosis")

    headers = auth_header(admin_token)
    assert (await client.get(f"/api/v1/orders/{order_id}", headers=headers)).status_code == 200
    assert (
        await client.get(f"/api/v1/orders/{order_id}/customer-profile", headers=headers)
    ).status_code == 200
    assert (
        await client.get(f"/api/v1/orders/{order_id}/price-changes", headers=headers)
    ).status_code == 200
    assert (
        await client.get(f"/api/v1/orders/{order_id}/costs", headers=headers)
    ).status_code == 200
    assert (
        await client.get(f"/api/v1/orders/{order_id}/reports", headers=headers)
    ).status_code == 200


async def test_admin_cannot_mutate_and_state_is_unchanged(
    client, admin_token, customer_token, technician_ready
):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "diagnosis")
    change_id = await _pending_change(client, technician_token, order_id)

    headers = auth_header(admin_token)
    before = await _snapshot(order_id)

    mutations = [
        ("patch", f"/api/v1/orders/{order_id}/status", {"status": "in_repair"}),
        ("put", f"/api/v1/orders/{order_id}/repair-details", {"diagnosis": "admin edit"}),
        (
            "post",
            f"/api/v1/orders/{order_id}/complete",
            {
                "diagnosis": "Intento de cierre del administrador.",
                "work_performed": "Trabajo no autorizado.",
                "tests_performed": "Pruebas.",
            },
        ),
        (
            "post",
            f"/api/v1/orders/{order_id}/not-repairable",
            {"reason": "Motivo suficientemente largo.", "diagnosis": "Diagnóstico admin."},
        ),
        ("post", f"/api/v1/orders/{order_id}/cancel", {"reason": "Cancelación admin"}),
        (
            "post",
            f"/api/v1/orders/{order_id}/price-changes",
            {"new_price": 500, "reason": "Cambio propuesto por admin."},
        ),
        ("post", f"/api/v1/orders/{order_id}/price-changes/{change_id}/approve", {}),
        ("post", f"/api/v1/orders/{order_id}/price-changes/{change_id}/reject", {}),
        (
            "post",
            f"/api/v1/orders/{order_id}/costs",
            {"kind": "labor", "description": "Costo admin", "amount": 10},
        ),
    ]

    for method, url, payload in mutations:
        response = await getattr(client, method)(url, headers=headers, json=payload)
        assert response.status_code == 403, (
            f"{method} {url} -> {response.status_code}: {response.text}"
        )

    assert await _snapshot(order_id) == before


async def test_admin_can_download_report(client, admin_token, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "ready")
    completed = await complete_order(client, technician_token, order_id)
    assert completed.status_code == 200, completed.text

    headers = auth_header(admin_token)
    reports = await client.get(f"/api/v1/orders/{order_id}/reports", headers=headers)
    assert reports.status_code == 200
    assert len(reports.json()) == 1

    download = await client.get(f"/api/v1/orders/{order_id}/report", headers=headers)
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"


async def test_unauthorized_customer_cannot_mutate(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await new_order(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "diagnosis")

    forbidden = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers=auth_header(customer_token),
        json={"status": "in_repair"},
    )
    assert forbidden.status_code == 403
