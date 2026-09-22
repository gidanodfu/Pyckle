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
from decimal import Decimal

from pydantic import Field, model_validator

from app.domains.repair_requests.schemas import TechnicianBrief
from app.domains.reviews.schemas import ReviewPublic
from app.models.enums import QuotationStatus
from app.schemas.common import MAX_MONEY, NonBlankStr, ORMModel


class QuotationItemCreate(ORMModel):
    description: NonBlankStr = Field(min_length=2, max_length=255)
    quantity: int = Field(default=1, ge=1, le=1000)
    unit_price: Decimal = Field(ge=0, le=MAX_MONEY)

    @model_validator(mode="after")
    def _total_within_limit(self):
        if self.unit_price * self.quantity > MAX_MONEY:
            raise ValueError("El total del ítem supera el máximo permitido")
        return self


class QuotationItemRead(ORMModel):
    id: uuid.UUID
    description: str
    quantity: int
    unit_price: Decimal
    total: Decimal


class QuotationCreate(ORMModel):
    request_id: uuid.UUID
    price: Decimal = Field(gt=0, le=MAX_MONEY)
    preliminary_diagnosis: NonBlankStr = Field(min_length=10, max_length=5000)
    estimated_days: int = Field(default=1, ge=1, le=365)
    valid_until: datetime | None = None
    items: list[QuotationItemCreate] = []


class QuotationRead(ORMModel):
    id: uuid.UUID
    request_id: uuid.UUID
    technician: TechnicianBrief
    price: Decimal
    preliminary_diagnosis: str
    estimated_days: int
    status: QuotationStatus
    valid_until: datetime | None = None
    items: list[QuotationItemRead] = []
    technician_reviews: list[ReviewPublic] = []
    created_at: datetime


class QuotationAccept(ORMModel):
    note: str | None = Field(default=None, max_length=1000)
