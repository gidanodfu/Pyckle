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

from pydantic import EmailStr, Field, field_validator

from app.core.phone import normalize_phone
from app.schemas.common import NonBlankStr, ORMModel


class RoleRead(ORMModel):
    id: uuid.UUID
    name: str
    description: str | None = None


class PermissionRead(ORMModel):
    id: uuid.UUID
    code: str
    description: str | None = None


class UserBrief(ORMModel):
    id: uuid.UUID
    full_name: str


class UserRead(ORMModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    phone: str | None = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    roles: list[RoleRead] = []


class UserUpdate(ORMModel):
    full_name: NonBlankStr | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=30)

    _validate_phone = field_validator("phone")(normalize_phone)


class AdminUserUpdate(ORMModel):
    full_name: NonBlankStr | None = Field(default=None, min_length=2, max_length=150)
    phone: str | None = Field(default=None, max_length=30)
    is_active: bool | None = None
    is_verified: bool | None = None
    roles: list[str] | None = None

    _validate_phone = field_validator("phone")(normalize_phone)


class ChangePasswordRequest(ORMModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class CustomerProfileRead(ORMModel):
    id: uuid.UUID
    address: str | None = None
    district: str | None = None
    city: str
    department_id: uuid.UUID | None = None
    province_id: uuid.UUID | None = None
    district_id: uuid.UUID | None = None
    department_name: str | None = None
    province_name: str | None = None
    district_name: str | None = None


class CustomerProfileUpdate(ORMModel):
    address: str | None = Field(default=None, max_length=255)
    department_id: uuid.UUID | None = None
    province_id: uuid.UUID | None = None
    district_id: uuid.UUID | None = None

    @field_validator("address")
    @classmethod
    def strip_address(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class CustomerPublicProfile(ORMModel):
    id: uuid.UUID
    full_name: str
    member_since: datetime
    completed_repairs: int
    department_name: str | None = None
    province_name: str | None = None
    district_name: str | None = None


class MeRead(ORMModel):
    user: UserRead
    customer_profile: CustomerProfileRead | None = None
    technician_id: uuid.UUID | None = None
    permissions: list[str] = []
