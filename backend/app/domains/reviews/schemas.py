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

from app.domains.users.schemas import UserBrief
from app.schemas.common import ORMModel


class ReviewCreate(ORMModel):
    order_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class ReviewRead(ORMModel):
    id: uuid.UUID
    order_id: uuid.UUID
    rating: int
    comment: str | None = None
    customer: UserBrief
    created_at: datetime


class ReviewPublic(ORMModel):
    """Reseña sin datos de contacto del cliente (perfiles y cotizaciones públicas)."""

    id: uuid.UUID
    rating: int
    comment: str | None = None
    customer_name: str
    created_at: datetime
