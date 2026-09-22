import pytest

from tests.conftest import (
    auth_header,
    complete_order,
    drive_order,
    run_flow,
)

pytestmark = pytest.mark.asyncio


async def _new_order(client, customer_token, technician_token, specialty_id):
    return await run_flow(client, customer_token, technician_token, specialty_id)


async def test_customer_cannot_change_order_status(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await _new_order(client, customer_token, technician_token, specialty_id)
    response = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers=auth_header(customer_token),
        json={"status": "received"},
    )
    assert response.status_code == 403


async def test_invalid_status_transition(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    _, _, order_id = await _new_order(client, customer_token, technician_token, specialty_id)
    # No se puede saltar de awaiting_receipt a un estado lejano, ni cerrar por /status.
    jump = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers=auth_header(technician_token),
        json={"status": "ready"},
    )
    assert jump.status_code == 400

    terminal = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        headers=auth_header(technician_token),
        json={"status": "completed"},
    )
    assert terminal.status_code == 400


async def test_full_order_lifecycle_and_review(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    request_id, _, order_id = await _new_order(
        client, customer_token, technician_token, specialty_id
    )

    review_too_early = await client.post(
        "/api/v1/reviews",
        headers=auth_header(customer_token),
        json={"order_id": order_id, "rating": 4},
    )
    assert review_too_early.status_code == 400

    await drive_order(client, technician_token, order_id, "ready")

    completed = await complete_order(client, technician_token, order_id)
    assert completed.status_code == 200, completed.text
    body = completed.json()
    assert body["status"] == "completed"
    assert body["result"] == "repaired"
    assert body["completed_at"] is not None
    assert body["report"] is not None
    assert any(event["new_status"] == "completed" for event in body["events"])

    request = await client.get(
        f"/api/v1/repair-requests/{request_id}", headers=auth_header(customer_token)
    )
    assert request.json()["status"] == "completed"

    review = await client.post(
        "/api/v1/reviews",
        headers=auth_header(customer_token),
        json={"order_id": order_id, "rating": 5, "comment": "Muy buen trabajo"},
    )
    assert review.status_code == 201, review.text

    duplicate = await client.post(
        "/api/v1/reviews",
        headers=auth_header(customer_token),
        json={"order_id": order_id, "rating": 3},
    )
    assert duplicate.status_code == 409

    stats = await client.get("/api/v1/technicians/me/stats", headers=auth_header(technician_token))
    assert stats.status_code == 200
    assert stats.json()["completed_orders"] == 1
    assert float(stats.json()["total_earnings"]) == 150.0


async def test_customer_order_list_shape(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    await _new_order(client, customer_token, technician_token, specialty_id)

    response = await client.get("/api/v1/orders?limit=8", headers=auth_header(customer_token))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["technician"]["district_name"] == "José Leonardo Ortiz"
    assert item["request"]["specialty_name"]


async def test_technician_order_list_shape(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    await _new_order(client, customer_token, technician_token, specialty_id)

    response = await client.get("/api/v1/orders?limit=8", headers=auth_header(technician_token))
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["technician"]["district_name"] == "José Leonardo Ortiz"
