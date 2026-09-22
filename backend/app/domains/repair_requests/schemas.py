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

from pydantic import Field

from app.domains.technicians.schemas import SpecialtyRead
from app.domains.users.schemas import UserBrief
from app.models.enums import Modality, RequestStatus
from app.schemas.common import MAX_MONEY, NonBlankStr, ORMModel


class TechnicianBrief(ORMModel):
    id: uuid.UUID
    full_name: str
    rating_avg: Decimal
    rating_count: int
    is_verified: bool
    district_name: str | None = None


class RepairRequestImageRead(ORMModel):
    id: uuid.UUID
    url: str
    content_type: str
    size_bytes: int


class RepairRequestCreate(ORMModel):
    title: NonBlankStr = Field(min_length=5, max_length=160)
    description: NonBlankStr = Field(min_length=10, max_length=5000)
    specialty_id: uuid.UUID | None = None
    modality: Modality = Modality.HOME
    # Ubicación del servicio; si se omite se usa la del perfil del cliente.
    department_id: uuid.UUID | None = None
    province_id: uuid.UUID | None = None
    district_id: uuid.UUID | None = None
    address: str | None = Field(default=None, max_length=255)
    budget_min: Decimal | None = Field(default=None, ge=0, le=MAX_MONEY)
    budget_max: Decimal | None = Field(default=None, ge=0, le=MAX_MONEY)
    preferred_date: datetime | None = None


class RepairRequestUpdate(ORMModel):
    title: NonBlankStr | None = Field(default=None, min_length=5, max_length=160)
    description: NonBlankStr | None = Field(default=None, min_length=10, max_length=5000)
    specialty_id: uuid.UUID | None = None
    modality: Modality | None = None
    department_id: uuid.UUID | None = None
    province_id: uuid.UUID | None = None
    district_id: uuid.UUID | None = None
    address: str | None = Field(default=None, max_length=255)
    budget_min: Decimal | None = Field(default=None, ge=0, le=MAX_MONEY)
    budget_max: Decimal | None = Field(default=None, ge=0, le=MAX_MONEY)
    preferred_date: datetime | None = None


class RepairRequestRead(ORMModel):
    id: uuid.UUID
    title: str
    description: str
    status: RequestStatus
    modality: Modality
    # Solo se expone al dueño, al técnico asignado o a un administrador.
    address: str | None = None
    district: str | None = None
    city: str
    department_name: str | None = None
    province_name: str | None = None
    district_name: str | None = None
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    preferred_date: datetime | None = None
    specialty: SpecialtyRead | None = None
    customer: UserBrief
    assigned_technician: TechnicianBrief | None = None
    images: list[RepairRequestImageRead] = []
    created_at: datetime
    updated_at: datetime
