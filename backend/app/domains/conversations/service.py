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

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.core.realtime import publish_conversation
from app.domains.conversations.repository import ConversationRepository
from app.domains.conversations.schemas import ConversationRead, MessageRead
from app.domains.notifications.service import NotificationService
from app.domains.technicians.repository import TechnicianRepository
from app.models.chat import Conversation, Message
from app.models.enums import ConversationStatus, NotificationType, RoleName
from app.models.user import User


class ConversationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ConversationRepository(session)
        self.technicians = TechnicianRepository(session)
        self.notifications = NotificationService(session)

    async def list_for_user(
        self, user: User, request_id: uuid.UUID | None = None
    ) -> list[ConversationRead]:
        self._assert_not_admin(user)
        technician = await self.technicians.get_by_user_id(user.id)
        conversations = await self.repo.list_for_user(
            user.id, technician.id if technician else None, request_id=request_id
        )
        return [ConversationRead.model_validate(c) for c in conversations]

    async def get_for_user(self, conversation_id: uuid.UUID, user: User) -> ConversationRead:
        conversation = await self._get_or_404(conversation_id)
        await self._assert_participant(conversation, user)
        return ConversationRead.model_validate(conversation)

    async def list_messages(
        self, conversation_id: uuid.UUID, user: User, limit: int = 100
    ) -> list[MessageRead]:
        conversation = await self._get_or_404(conversation_id)
        await self._assert_participant(conversation, user)
        messages = await self.repo.list_messages(conversation_id, limit=limit)
        changed = False
        for message in messages:
            if message.sender_id != user.id and not message.is_read:
                message.is_read = True
                changed = True
        if changed:
            await self.session.commit()
        return [MessageRead.model_validate(m) for m in messages]

    async def send_message(self, conversation_id: uuid.UUID, user: User, body: str) -> MessageRead:
        conversation = await self._get_or_404(conversation_id)
        await self._assert_participant(conversation, user)
        if conversation.status != ConversationStatus.OPEN:
            raise ConflictError("La conversación está cerrada; el historial permanece disponible")
        message = Message(conversation_id=conversation_id, sender_id=user.id, body=body)
        await self.repo.add_message(message)
        conversation.last_message_at = datetime.now(UTC)
        await self.session.commit()

        read = MessageRead.model_validate(message)
        await publish_conversation(
            conversation_id,
            {"event": "message.new", "message": read.model_dump(mode="json")},
        )
        recipient_id = (
            conversation.customer_id
            if user.id != conversation.customer_id
            else conversation.technician.user_id
        )
        await self.notifications.create(
            recipient_id,
            NotificationType.MESSAGE_NEW,
            "Nuevo mensaje",
            body[:120],
            {"conversation_id": str(conversation_id)},
        )
        await self.session.commit()
        return read

    async def _get_or_404(self, conversation_id: uuid.UUID) -> Conversation:
        conversation = await self.repo.get_detail(conversation_id)
        if conversation is None:
            raise NotFoundError("Conversación no encontrada")
        return conversation

    @staticmethod
    def _assert_not_admin(user: User) -> None:
        """El administrador no usa el chat, aunque tenga otros permisos de admin."""
        if RoleName.ADMIN.value in user.role_names:
            raise ForbiddenError("El administrador no participa en el chat")

    async def _assert_participant(self, conversation: Conversation, user: User) -> None:
        self._assert_not_admin(user)
        if conversation.customer_id == user.id:
            return
        technician = await self.technicians.get_by_user_id(user.id)
        if technician is not None and conversation.technician_id == technician.id:
            return
        raise ForbiddenError("No participas en esta conversación")
