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

from pydantic import Field, field_validator

from app.domains.users.schemas import UserBrief
from app.schemas.common import NonBlankStr, ORMModel


class SpecialtyRead(ORMModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None = None
    is_active: bool


class SpecialtyCreate(ORMModel):
    name: NonBlankStr = Field(min_length=2, max_length=120)
    description: str | None = None
    is_active: bool = True


class SpecialtyUpdate(ORMModel):
    name: NonBlankStr | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = None
    is_active: bool | None = None


class TechnicianProfileUpdate(ORMModel):
    bio: str | None = Field(default=None, max_length=2000)
    experience_years: int | None = Field(default=None, ge=0, le=80)
    offers_home_service: bool | None = None
    offers_workshop_service: bool | None = None
    workshop_address: str | None = Field(default=None, max_length=255)
    specialty_ids: list[uuid.UUID] | None = None
    department_id: uuid.UUID | None = None
    province_id: uuid.UUID | None = None
    district_id: uuid.UUID | None = None

    @field_validator("workshop_address")
    @classmethod
    def strip_workshop_address(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class TechnicianRead(ORMModel):
    id: uuid.UUID
    user: UserBrief
    bio: str | None = None
    experience_years: int
    is_verified: bool
    offers_home_service: bool
    offers_workshop_service: bool
    workshop_address: str | None = None
    department_id: uuid.UUID | None = None
    province_id: uuid.UUID | None = None
    district_id: uuid.UUID | None = None
    department_name: str | None = None
    province_name: str | None = None
    district_name: str | None = None
    rating_avg: Decimal
    rating_count: int
    specialties: list[SpecialtyRead] = []
    created_at: datetime


class TechnicianPublic(ORMModel):
    id: uuid.UUID
    full_name: str
    bio: str | None = None
    experience_years: int
    is_verified: bool
    offers_home_service: bool
    offers_workshop_service: bool
    # Dirección del local: privada. Solo se expone en TechnicianRead (propietario)
    # o a través de un flujo autorizado de la orden; nunca en perfiles públicos.
    department_name: str | None = None
    province_name: str | None = None
    district_name: str | None = None
    rating_avg: Decimal
    rating_count: int
    specialties: list[SpecialtyRead] = []


class TechnicianStats(ORMModel):
    active_orders: int
    completed_orders: int
    total_earnings: Decimal
    pending_quotations: int


class SpecialtyCount(ORMModel):
    specialty_id: uuid.UUID
    name: str
    count: int


class TechnicianSummary(ORMModel):
    total: int
    by_status: dict[str, int]
    by_result: dict[str, int]
    by_specialty: list[SpecialtyCount]
    pending_price_changes: int
