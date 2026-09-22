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

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession
from app.domains.notifications.schemas import NotificationRead, NotificationsReadAllResult
from app.domains.notifications.service import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    current_user: CurrentUser,
    session: DbSession,
    unread_only: bool = False,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[NotificationRead]:
    notifications = await NotificationService(session).list_for_user(
        current_user.id, unread_only=unread_only, limit=limit, offset=offset
    )
    return [NotificationRead.model_validate(n) for n in notifications]


@router.get("/unread-count")
async def unread_count(current_user: CurrentUser, session: DbSession) -> dict[str, int]:
    count = await NotificationService(session).unread_count(current_user.id)
    return {"unread": count}


@router.post("/read-all", response_model=NotificationsReadAllResult)
async def mark_all_read(
    current_user: CurrentUser, session: DbSession
) -> NotificationsReadAllResult:
    service = NotificationService(session)
    updated = await service.mark_all_read(current_user.id)
    unread = await service.unread_count(current_user.id)
    return NotificationsReadAllResult(updated=updated, unread=unread)
