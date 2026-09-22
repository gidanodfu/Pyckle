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
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.realtime import publish_user
from app.domains.notifications.repository import NotificationRepository
from app.domains.notifications.schemas import NotificationRead
from app.models.enums import NotificationType
from app.models.notification import Notification


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = NotificationRepository(session)

    async def create(
        self,
        user_id: uuid.UUID,
        type: NotificationType,
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> Notification:
        notification = Notification(user_id=user_id, type=type, title=title, body=body, data=data)
        await self.repo.add(notification)
        event = {
            "event": "notification.new",
            "notification": NotificationRead.model_validate(notification).model_dump(mode="json"),
        }
        await publish_user(user_id, event)
        return notification

    async def list_for_user(
        self, user_id: uuid.UUID, *, unread_only: bool = False, limit: int = 50, offset: int = 0
    ) -> list[Notification]:
        return await self.repo.list_for_user(
            user_id, unread_only=unread_only, limit=limit, offset=offset
        )

    async def unread_count(self, user_id: uuid.UUID) -> int:
        return await self.repo.unread_count(user_id)

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        """Idempotente: devuelve cuantas notificaciones cambió a leídas."""
        updated = await self.repo.mark_all_read(user_id)
        await self.session.commit()
        return updated
