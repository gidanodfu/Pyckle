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

import uuid

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUser, DbSession
from app.domains.conversations.schemas import ConversationRead, MessageCreate, MessageRead
from app.domains.conversations.service import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationRead])
async def list_conversations(
    current_user: CurrentUser,
    session: DbSession,
    request_id: uuid.UUID | None = None,
) -> list[ConversationRead]:
    return await ConversationService(session).list_for_user(current_user, request_id=request_id)


@router.get("/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    conversation_id: uuid.UUID, current_user: CurrentUser, session: DbSession
) -> ConversationRead:
    return await ConversationService(session).get_for_user(conversation_id, current_user)


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
async def list_messages(
    conversation_id: uuid.UUID,
    current_user: CurrentUser,
    session: DbSession,
    limit: int = Query(default=100, ge=1, le=200),
) -> list[MessageRead]:
    return await ConversationService(session).list_messages(
        conversation_id, current_user, limit=limit
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: uuid.UUID,
    data: MessageCreate,
    current_user: CurrentUser,
    session: DbSession,
) -> MessageRead:
    return await ConversationService(session).send_message(conversation_id, current_user, data.body)
