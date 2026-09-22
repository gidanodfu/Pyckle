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

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.infrastructure.repository import BaseRepository
from app.models.geo import Department, District, Province


class GeoRepository(BaseRepository[Department]):
    model = Department

    async def list_departments(self) -> list[Department]:
        stmt = select(Department).order_by(Department.name)
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_provinces(self, department_id: uuid.UUID) -> list[Province]:
        stmt = (
            select(Province).where(Province.department_id == department_id).order_by(Province.name)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_districts(self, province_id: uuid.UUID) -> list[District]:
        stmt = select(District).where(District.province_id == province_id).order_by(District.name)
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_department(self, department_id: uuid.UUID) -> Department | None:
        stmt = select(Department).where(Department.id == department_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_province(self, province_id: uuid.UUID) -> Province | None:
        stmt = select(Province).where(Province.id == province_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_district(self, district_id: uuid.UUID) -> District | None:
        stmt = (
            select(District)
            .options(
                selectinload(District.province).selectinload(Province.department),
                selectinload(District.department),
            )
            .where(District.id == district_id)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def district_by_name(self, department_id: uuid.UUID, name: str) -> District | None:
        stmt = select(District).where(
            District.department_id == department_id, District.name == name
        )
        return (await self.session.execute(stmt)).scalars().first()
