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

from fastapi import APIRouter

from app.core.dependencies import DbSession
from app.domains.geo.schemas import DepartmentRead, DistrictRead, ProvinceRead
from app.domains.geo.service import GeoService

router = APIRouter(prefix="/geo", tags=["geo"])


@router.get("/departments", response_model=list[DepartmentRead])
async def list_departments(session: DbSession) -> list[DepartmentRead]:
    return await GeoService(session).list_departments()


@router.get("/departments/{department_id}/provinces", response_model=list[ProvinceRead])
async def list_provinces(department_id: uuid.UUID, session: DbSession) -> list[ProvinceRead]:
    return await GeoService(session).list_provinces(department_id)


@router.get("/provinces/{province_id}/districts", response_model=list[DistrictRead])
async def list_districts(province_id: uuid.UUID, session: DbSession) -> list[DistrictRead]:
    return await GeoService(session).list_districts(province_id)
