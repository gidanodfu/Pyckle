"""Contrato y casos extremos de GET /admin/orders (regresión del 500 por lazy-load)."""

import pytest

from tests.conftest import auth_header, drive_order, run_flow

pytestmark = pytest.mark.asyncio


async def _order(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    await run_flow(client, customer_token, technician_token, specialty_id)
    return technician_token


async def _list(client, admin_token, query=""):
    return await client.get(f"/api/v1/admin/orders{query}", headers=auth_header(admin_token))


async def test_admin_orders_contract_empty(client, admin_token):
    response = await _list(client, admin_token, "?limit=8")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["limit"] == 8
    assert body["offset"] == 0


async def test_admin_orders_contract_with_data(
    client, admin_token, customer_token, technician_ready
):
    await _order(client, customer_token, technician_ready)

    response = await _list(client, admin_token, "?limit=8")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] >= 1
    assert len(body["items"]) == body["total"]

    item = body["items"][0]
    # OrderListItem: relaciones y properties que disparan lazy-load si faltan.
    assert item["technician"]["full_name"]
    assert item["technician"]["district_name"] == "José Leonardo Ortiz"
    assert item["request"]["specialty_name"]
    assert item["request"]["modality"] in {"home", "workshop"}
    assert item["customer"]["full_name"]
    assert item["has_pending_price_change"] is False
    assert item["has_report"] is False
    assert item["final_price"] is not None


async def test_admin_orders_limit_and_offset(client, admin_token, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    for _ in range(9):
        await run_flow(client, customer_token, technician_token, specialty_id)

    one = await _list(client, admin_token, "?limit=1")
    assert one.status_code == 200
    assert len(one.json()["items"]) == 1

    eight = await _list(client, admin_token, "?limit=8")
    assert len(eight.json()["items"]) == 8
    assert eight.json()["total"] == 9

    hundred = await _list(client, admin_token, "?limit=100")
    assert len(hundred.json()["items"]) == 9

    beyond = await _list(client, admin_token, "?limit=8&offset=50")
    assert beyond.status_code == 200
    assert beyond.json()["items"] == []
    assert beyond.json()["total"] == 9


async def test_admin_orders_multiple_price_changes(
    client, admin_token, customer_token, technician_ready
):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await run_flow(client, customer_token, technician_token, specialty_id)
    await drive_order(client, technician_token, order_id, "diagnosis")

    for price in (120, 110):
        reduction = await client.post(
            f"/api/v1/orders/{order_id}/price-changes",
            headers=auth_header(technician_token),
            json={"new_price": price, "reason": "Ajuste de precio de prueba."},
        )
        assert reduction.status_code == 201, reduction.text

    response = await _list(client, admin_token, "?limit=8")
    assert response.status_code == 200, response.text
    item = response.json()["items"][0]
    # Las reducciones se autoaprueban: no queda cambio pendiente en el listado.
    assert item["has_pending_price_change"] is False

    changes = await client.get(
        f"/api/v1/orders/{order_id}/price-changes", headers=auth_header(technician_token)
    )
    assert len(changes.json()) == 2
    assert item["final_price"] == "110.00"


async def test_admin_orders_technician_without_district(
    client, admin_token, customer_token, technician_ready, session
):
    from sqlalchemy import select

    from app.models.technician import Technician

    technician_token, specialty_id = technician_ready
    await run_flow(client, customer_token, technician_token, specialty_id)

    technician_id = (
        await client.get("/api/v1/technicians/me", headers=auth_header(technician_token))
    ).json()["id"]
    technician = (
        await session.execute(select(Technician).where(Technician.id == technician_id))
    ).scalar_one()
    technician.district_id = None
    await session.commit()

    response = await _list(client, admin_token, "?limit=8")
    assert response.status_code == 200, response.text
    assert response.json()["items"][0]["technician"]["district_name"] is None


async def test_admin_orders_authorization(client, customer_token):
    unauthenticated = await client.get("/api/v1/admin/orders?limit=8")
    assert unauthenticated.status_code == 401

    forbidden = await client.get(
        "/api/v1/admin/orders?limit=8", headers=auth_header(customer_token)
    )
    assert forbidden.status_code == 403


async def test_admin_orders_filters(client, admin_token, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    order_ids = []
    for _ in range(3):
        _, _, order_id = await run_flow(client, customer_token, technician_token, specialty_id)
        order_ids.append(order_id)
    await drive_order(client, technician_token, order_ids[0], "diagnosis")

    awaiting = await _list(client, admin_token, "?status=awaiting_receipt")
    assert awaiting.status_code == 200
    assert awaiting.json()["total"] == 2

    diagnosis = await _list(client, admin_token, "?status=diagnosis")
    assert diagnosis.json()["total"] == 1

    by_specialty = await _list(client, admin_token, f"?specialty_id={specialty_id}")
    assert by_specialty.json()["total"] == 3

    assert (await _list(client, admin_token, "?from_date=2000-01-01")).json()["total"] == 3
    assert (await _list(client, admin_token, "?to_date=2000-01-01")).json()["total"] == 0


async def test_admin_orders_invalid_pagination(client, admin_token):
    for query in ("?limit=0", "?limit=101", "?offset=-1", "?limit=abc"):
        response = await _list(client, admin_token, query)
        assert response.status_code == 422
