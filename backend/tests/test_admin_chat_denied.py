"""El administrador no tiene acceso al chat (solo customer/técnico)."""

import uuid

import pytest

from app.core.exceptions import ForbiddenError
from app.domains.conversations.service import ConversationService
from app.domains.users.repository import UserRepository
from tests.conftest import ADMIN_EMAIL, TestSession, auth_header, new_order

pytestmark = pytest.mark.asyncio


async def _conversation_for(client, token: str, request_id: str) -> dict:
    conversations = (await client.get("/api/v1/conversations", headers=auth_header(token))).json()
    return next(item for item in conversations if item["request_id"] == request_id)


async def test_admin_cannot_use_chat_api(client, admin_token, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    request_id, _, _ = await new_order(client, customer_token, technician_token, specialty_id)
    conversation = await _conversation_for(client, customer_token, request_id)
    headers = auth_header(admin_token)

    assert (await client.get("/api/v1/conversations", headers=headers)).status_code == 403
    assert (
        await client.get(f"/api/v1/conversations/{conversation['id']}", headers=headers)
    ).status_code == 403
    assert (
        await client.get(f"/api/v1/conversations/{conversation['id']}/messages", headers=headers)
    ).status_code == 403
    assert (
        await client.post(
            f"/api/v1/conversations/{conversation['id']}/messages",
            headers=headers,
            json={"body": "Mensaje de administrador"},
        )
    ).status_code == 403


async def test_chat_service_denies_admin_before_websocket(
    client, admin_token, customer_token, technician_ready
):
    """El WebSocket de chat autoriza con ConversationService.get_for_user.

    httpx ASGITransport no abre sockets, así que se valida exactamente el check
    que usa `chat_socket` (equivale al cierre 4403).
    """
    technician_token, specialty_id = technician_ready
    request_id, _, _ = await new_order(client, customer_token, technician_token, specialty_id)
    conversation = await _conversation_for(client, customer_token, request_id)

    async with TestSession() as session:
        admin = await UserRepository(session).get_by_email(ADMIN_EMAIL)
        assert admin is not None
        with pytest.raises(ForbiddenError):
            await ConversationService(session).get_for_user(uuid.UUID(conversation["id"]), admin)


async def test_customer_and_technician_chat_still_work(client, customer_token, technician_ready):
    technician_token, specialty_id = technician_ready
    request_id, _, _ = await new_order(client, customer_token, technician_token, specialty_id)
    conversation = await _conversation_for(client, customer_token, request_id)

    for token, body in (
        (customer_token, "Mensaje del cliente"),
        (technician_token, "Respuesta del técnico"),
    ):
        sent = await client.post(
            f"/api/v1/conversations/{conversation['id']}/messages",
            headers=auth_header(token),
            json={"body": body},
        )
        assert sent.status_code == 201, sent.text

    history = await client.get(
        f"/api/v1/conversations/{conversation['id']}/messages",
        headers=auth_header(customer_token),
    )
    assert history.status_code == 200
    assert [message["body"] for message in history.json()] == [
        "Mensaje del cliente",
        "Respuesta del técnico",
    ]
