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

from app.schemas.common import ORMModel


class DepartmentRead(ORMModel):
    id: uuid.UUID
    code: str
    name: str


class ProvinceRead(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    department_id: uuid.UUID


class DistrictRead(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    province_id: uuid.UUID
    department_id: uuid.UUID


class LocationRead(ORMModel):
    department_id: uuid.UUID | None = None
    province_id: uuid.UUID | None = None
    district_id: uuid.UUID | None = None
    department_name: str | None = None
    province_name: str | None = None
    district_name: str | None = None
