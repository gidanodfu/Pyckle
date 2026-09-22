import pytest

from tests.conftest import auth_header, run_flow

pytestmark = pytest.mark.asyncio


async def test_notifications_lifecycle(client, customer_token, technician_ready):
    technician_ready_token, specialty_id = technician_ready
    request_id, _, _ = await run_flow(client, customer_token, technician_ready_token, specialty_id)

    unread = await client.get(
        "/api/v1/notifications/unread-count", headers=auth_header(customer_token)
    )
    assert unread.json()["unread"] >= 1

    mark = await client.post("/api/v1/notifications/read-all", headers=auth_header(customer_token))
    assert mark.status_code == 200
    assert mark.json()["updated"] >= 1
    assert mark.json()["unread"] == 0

    # Idempotente: no hay nada pendiente.
    again = await client.post("/api/v1/notifications/read-all", headers=auth_header(customer_token))
    assert again.json()["updated"] == 0
    assert again.json()["unread"] == 0

    # Una nueva notificacion vuelve a habilitar la accion.
    conversations = (
        await client.get("/api/v1/conversations", headers=auth_header(customer_token))
    ).json()
    conversation = next(item for item in conversations if item["request_id"] == request_id)
    await client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=auth_header(technician_ready_token),
        json={"body": "Nuevo mensaje para notificar"},
    )
    count = await client.get(
        "/api/v1/notifications/unread-count", headers=auth_header(customer_token)
    )
    assert count.json()["unread"] == 1


async def test_notifications_are_per_user(client, customer_token, technician_ready, geo):
    from tests.conftest import PASSWORD, login, register_payload

    technician_token, specialty_id = technician_ready
    await run_flow(client, customer_token, technician_token, specialty_id)

    response = await client.post(
        "/api/v1/auth/register",
        json=register_payload(geo, email="notif.otro@test.dev", phone="+51910101010"),
    )
    assert response.status_code == 201
    other = (await login(client, "notif.otro@test.dev", PASSWORD))["access_token"]

    notifications = await client.get("/api/v1/notifications", headers=auth_header(other))
    assert notifications.status_code == 200
    assert notifications.json() == []

    count = await client.get("/api/v1/notifications/unread-count", headers=auth_header(other))
    assert count.json()["unread"] == 0
