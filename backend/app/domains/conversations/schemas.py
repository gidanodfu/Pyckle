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
from datetime import datetime

from pydantic import Field

from app.domains.repair_requests.schemas import TechnicianBrief
from app.domains.users.schemas import UserBrief
from app.models.enums import ConversationStatus
from app.schemas.common import NonBlankStr, ORMModel


class ConversationRead(ORMModel):
    id: uuid.UUID
    request_id: uuid.UUID
    order_id: uuid.UUID | None = None
    status: ConversationStatus
    closed_at: datetime | None = None
    customer: UserBrief
    technician: TechnicianBrief
    last_message_at: datetime | None = None
    created_at: datetime


class MessageCreate(ORMModel):
    body: NonBlankStr = Field(min_length=1, max_length=4000)


class MessageRead(ORMModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender: UserBrief
    body: str
    is_read: bool
    created_at: datetime
