# Copyright (C) 2026 Josue David (gidanodfu)
# https://github.com/gidanodfu
#
# This file is part of Pyckle.
#
# Pyckle is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# Pyckle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Pyckle. If not, see <https://www.gnu.org/licenses/>.

from __future__ import annotations

import asyncio
import contextlib
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.dependencies import CurrentUser
from app.core.exceptions import AppError
from app.core.logging import get_logger
from app.core.redis import get_redis
from app.core.ws_tickets import consume_ws_ticket, issue_ws_ticket
from app.db.session import SessionLocal
from app.domains.conversations.service import ConversationService
from app.domains.users.repository import UserRepository

logger = get_logger("websocket")
router = APIRouter(tags=["websockets"])
ticket_router = APIRouter(prefix="/ws", tags=["websockets"])


@ticket_router.post("/ticket")
async def create_ws_ticket(current_user: CurrentUser) -> dict[str, object]:
    """Emite un ticket de un solo uso para abrir un WebSocket sin exponer el JWT."""
    ticket, expires_in = await issue_ws_ticket(current_user.id)
    return {"ticket": ticket, "expires_in": expires_in}


async def _authenticate(websocket: WebSocket):
    try:
        ticket = websocket.query_params.get("ticket")
        user_id = await consume_ws_ticket(ticket)
        if user_id is None:
            return None
        try:
            subject = uuid.UUID(user_id)
        except ValueError:
            return None
        async with SessionLocal() as session:
            user = await UserRepository(session).get_with_roles(subject)
        if user is None or not user.is_active:
            return None
        return user
    except Exception:  # noqa: BLE001 - autenticación best-effort; se cierra 4401
        logger.warning("Fallo autenticando WebSocket", exc_info=True)
        return None


async def _redis_to_ws(websocket: WebSocket, channels: list[str]) -> None:
    pubsub = get_redis().pubsub()
    await pubsub.subscribe(*channels)
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("type") == "message":
                await websocket.send_text(str(message["data"]))
            else:
                await asyncio.sleep(0)
    finally:
        with contextlib.suppress(Exception):
            await pubsub.unsubscribe(*channels)
        with contextlib.suppress(Exception):
            await pubsub.aclose()


async def _ws_keepalive(websocket: WebSocket) -> None:
    while True:
        await websocket.receive_text()


@router.websocket("/ws/notifications")
async def notifications_socket(websocket: WebSocket) -> None:
    user = await _authenticate(websocket)
    if user is None:
        await websocket.close(code=4401, reason="No autorizado")
        return
    await websocket.accept()
    await _run(websocket, [f"user:{user.id}"], handle_messages=False, user=user)


@router.websocket("/ws/chat/{conversation_id}")
async def chat_socket(websocket: WebSocket, conversation_id: uuid.UUID) -> None:
    user = await _authenticate(websocket)
    if user is None:
        await websocket.close(code=4401, reason="No autorizado")
        return
    async with SessionLocal() as session:
        try:
            await ConversationService(session).get_for_user(conversation_id, user)
        except AppError:
            await websocket.close(code=4403, reason="Sin acceso a la conversación")
            return
    await websocket.accept()
    await _run(websocket, [f"conversation:{conversation_id}"], handle_messages=True, user=user)


async def _run(websocket: WebSocket, channels: list[str], *, handle_messages: bool, user) -> None:
    tasks = [
        asyncio.create_task(_redis_to_ws(websocket, channels)),
        asyncio.create_task(
            _receive_messages(websocket, user) if handle_messages else _ws_keepalive(websocket)
        ),
    ]
    try:
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
        for task in pending:
            task.cancel()
        for task in done:
            with contextlib.suppress(WebSocketDisconnect, asyncio.CancelledError):
                task.result()
    except WebSocketDisconnect:
        pass
    except Exception:  # noqa: BLE001 - no propagar fallos de Redis/DB al ASGI
        logger.warning("Fallo en WebSocket", exc_info=True)
    finally:
        for task in tasks:
            task.cancel()
        with contextlib.suppress(Exception):
            await websocket.close()


async def _receive_messages(websocket: WebSocket, user) -> None:
    import json

    while True:
        raw = await websocket.receive_text()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            await websocket.send_text(json.dumps({"event": "error", "detail": "JSON inválido"}))
            continue
        if payload.get("type") != "message":
            continue
        body = (payload.get("body") or "").strip()
        if not body:
            continue
        path = websocket.url.path
        conversation_id = uuid.UUID(path.rstrip("/").split("/")[-1])
        async with SessionLocal() as session:
            try:
                await ConversationService(session).send_message(conversation_id, user, body[:4000])
            except AppError as exc:
                await websocket.send_text(json.dumps({"event": "error", "detail": exc.message}))
            except Exception:  # noqa: BLE001
                logger.warning("Fallo enviando mensaje por WebSocket", exc_info=True)
                await websocket.send_text(
                    json.dumps({"event": "error", "detail": "No se pudo enviar el mensaje"})
                )
