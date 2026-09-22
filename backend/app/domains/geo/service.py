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

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.domains.geo.repository import GeoRepository
from app.domains.geo.schemas import DepartmentRead, DistrictRead, ProvinceRead
from app.models.geo import Department, District, Province


class GeoService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = GeoRepository(session)

    async def list_departments(self) -> list[DepartmentRead]:
        return [DepartmentRead.model_validate(item) for item in await self.repo.list_departments()]

    async def list_provinces(self, department_id: uuid.UUID) -> list[ProvinceRead]:
        if await self.repo.get_department(department_id) is None:
            raise NotFoundError("Departamento no encontrado")
        return [
            ProvinceRead.model_validate(item)
            for item in await self.repo.list_provinces(department_id)
        ]

    async def list_districts(self, province_id: uuid.UUID) -> list[DistrictRead]:
        if await self.repo.get_province(province_id) is None:
            raise NotFoundError("Provincia no encontrada")
        return [
            DistrictRead.model_validate(item)
            for item in await self.repo.list_districts(province_id)
        ]

    async def resolve(
        self,
        department_id: uuid.UUID | None,
        province_id: uuid.UUID | None,
        district_id: uuid.UUID | None,
    ) -> District:
        """Valida la jerarquía departamento -> provincia -> distrito."""
        if department_id is None or province_id is None or district_id is None:
            raise BadRequestError("Debes seleccionar departamento, provincia y distrito")
        department = await self.repo.get_department(department_id)
        if department is None:
            raise BadRequestError("El departamento seleccionado no existe")
        province = await self.repo.get_province(province_id)
        if province is None or province.department_id != department.id:
            raise BadRequestError("La provincia no pertenece al departamento seleccionado")
        district = await self.repo.get_district(district_id)
        if district is None or district.province_id != province.id:
            raise BadRequestError("El distrito no pertenece a la provincia seleccionada")
        return district

    async def get_province(self, province_id: uuid.UUID) -> Province:
        province = await self.repo.get_province(province_id)
        if province is None:
            raise BadRequestError("La provincia seleccionada no existe")
        return province

    async def get_department(self, department_id: uuid.UUID) -> Department:
        department = await self.repo.get_department(department_id)
        if department is None:
            raise BadRequestError("El departamento seleccionado no existe")
        return department
