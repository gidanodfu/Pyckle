import pytest

from tests.conftest import auth_header, complete_order, drive_order, run_flow

pytestmark = pytest.mark.asyncio


async def _conversation_for(client, token: str, request_id: str) -> dict:
    conversations = (await client.get("/api/v1/conversations", headers=auth_header(token))).json()
    return next(item for item in conversations if item["request_id"] == request_id)


async def test_open_chat_allows_messages(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    request_id, _, _ = await run_flow(client, customer_token, technician_token, specialty_id)
    conversation = await _conversation_for(client, customer_token, request_id)
    assert conversation["status"] == "open"
    assert conversation["closed_at"] is None

    sent = await client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=auth_header(customer_token),
        json={"body": "Hola, ¿cuándo puedes venir?"},
    )
    assert sent.status_code == 201, sent.text

    reply = await client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=auth_header(technician_token),
        json={"body": "Mañana por la tarde."},
    )
    assert reply.status_code == 201, reply.text


async def test_completing_order_archives_chat_and_blocks_messages(
    client, customer_token, technician_ready
):
    technician_token, specialty_id = technician_ready
    request_id, _, order_id = await run_flow(client, customer_token, technician_token, specialty_id)
    conversation = await _conversation_for(client, customer_token, request_id)

    await client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=auth_header(customer_token),
        json={"body": "Primer mensaje"},
    )
    await drive_order(client, technician_token, order_id, "ready")
    completed = await complete_order(client, technician_token, order_id)
    assert completed.status_code == 200

    archived = await _conversation_for(client, customer_token, request_id)
    assert archived["status"] == "archived"
    assert archived["closed_at"] is not None

    rejected = await client.post(
        f"/api/v1/conversations/{archived['id']}/messages",
        headers=auth_header(customer_token),
        json={"body": "¿Sigues ahí?"},
    )
    assert rejected.status_code == 409

    rejected_tech = await client.post(
        f"/api/v1/conversations/{archived['id']}/messages",
        headers=auth_header(technician_token),
        json={"body": "Respuesta tardía"},
    )
    assert rejected_tech.status_code == 409

    history = await client.get(
        f"/api/v1/conversations/{archived['id']}/messages",
        headers=auth_header(customer_token),
    )
    assert history.status_code == 200
    assert [message["body"] for message in history.json()] == ["Primer mensaje"]


async def test_foreign_user_cannot_read_or_write_conversation(
    client, customer_token, technician_ready, geo
):
    from tests.conftest import PASSWORD, login, register_payload

    technician_token, specialty_id = technician_ready
    request_id, _, _ = await run_flow(client, customer_token, technician_token, specialty_id)
    conversation = await _conversation_for(client, customer_token, request_id)

    response = await client.post(
        "/api/v1/auth/register",
        json=register_payload(geo, email="chat.intruso@test.dev", phone="+51988888881"),
    )
    assert response.status_code == 201
    intruder = (await login(client, "chat.intruso@test.dev", PASSWORD))["access_token"]

    blocked = await client.post(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=auth_header(intruder),
        json={"body": "No debería poder escribir"},
    )
    assert blocked.status_code == 403

    blocked_read = await client.get(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=auth_header(intruder),
    )
    assert blocked_read.status_code == 403
