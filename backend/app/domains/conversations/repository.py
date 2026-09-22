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

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.infrastructure.repository import BaseRepository
from app.models.chat import Conversation, Message
from app.models.technician import Technician


class ConversationRepository(BaseRepository[Conversation]):
    model = Conversation

    def _detail(self):
        return select(Conversation).options(
            selectinload(Conversation.customer),
            selectinload(Conversation.technician).selectinload(Technician.user),
            selectinload(Conversation.technician).selectinload(Technician.district_geo),
            selectinload(Conversation.request),
        )

    async def get_detail(self, conversation_id: uuid.UUID) -> Conversation | None:
        stmt = self._detail().where(Conversation.id == conversation_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_request_technician(
        self, request_id: uuid.UUID, technician_id: uuid.UUID
    ) -> Conversation | None:
        stmt = self._detail().where(
            Conversation.request_id == request_id, Conversation.technician_id == technician_id
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_order(self, order_id: uuid.UUID) -> Conversation | None:
        stmt = self._detail().where(Conversation.order_id == order_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        technician_id: uuid.UUID | None,
        request_id: uuid.UUID | None = None,
    ) -> list[Conversation]:
        conditions = [Conversation.customer_id == user_id]
        if technician_id is not None:
            conditions = [
                or_(
                    Conversation.customer_id == user_id, Conversation.technician_id == technician_id
                )
            ]
        if request_id is not None:
            conditions.append(Conversation.request_id == request_id)
        stmt = (
            self._detail()
            .where(*conditions)
            .order_by(func.coalesce(Conversation.last_message_at, Conversation.created_at).desc())
        )
        return list((await self.session.execute(stmt)).scalars().unique().all())

    async def count_for_participant(
        self, user_id: uuid.UUID, technician_id: uuid.UUID | None
    ) -> int:
        conditions = [Conversation.customer_id == user_id]
        if technician_id is not None:
            conditions = [
                or_(
                    Conversation.customer_id == user_id,
                    Conversation.technician_id == technician_id,
                )
            ]
        stmt = select(func.count(Conversation.id)).where(*conditions)
        return int((await self.session.execute(stmt)).scalar_one())

    async def list_messages(self, conversation_id: uuid.UUID, limit: int = 100) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def add_message(self, message: Message) -> Message:
        self.session.add(message)
        await self.session.flush()
        await self.session.refresh(message)
        return message
