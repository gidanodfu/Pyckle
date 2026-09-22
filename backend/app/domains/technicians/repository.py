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

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.infrastructure.repository import BaseRepository
from app.models.repair import RepairRequest
from app.models.technician import Specialty, Technician, technician_specialties
from app.models.user import User


class TechnicianRepository(BaseRepository[Technician]):
    model = Technician

    def _detail(self):
        return select(Technician).options(
            selectinload(Technician.user),
            selectinload(Technician.specialties),
            selectinload(Technician.department),
            selectinload(Technician.province),
            selectinload(Technician.district_geo),
        )

    async def get_by_user_id(self, user_id: uuid.UUID) -> Technician | None:
        stmt = self._detail().where(Technician.user_id == user_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_detail(self, technician_id: uuid.UUID) -> Technician | None:
        stmt = self._detail().where(Technician.id == technician_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_public(
        self,
        *,
        specialty_id: uuid.UUID | None = None,
        verified_only: bool = False,
        search: str | None = None,
        department_id: uuid.UUID | None = None,
        province_id: uuid.UUID | None = None,
        district_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Technician], int]:
        stmt = self._detail().join(Technician.user)
        count_stmt = select(func.count(func.distinct(Technician.id))).select_from(Technician)
        conditions = []
        if verified_only:
            conditions.append(Technician.is_verified.is_(True))
        if search:
            like = f"%{search.lower()}%"
            conditions.append(
                func.lower(User.full_name).like(like)
                | func.lower(func.coalesce(Technician.bio, "")).like(like)
            )
        if district_id is not None:
            conditions.append(Technician.district_id == district_id)
        elif province_id is not None:
            conditions.append(Technician.province_id == province_id)
        elif department_id is not None:
            conditions.append(Technician.department_id == department_id)
        if conditions:
            stmt = stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)
        if specialty_id:
            stmt = stmt.join(Technician.specialties).where(Specialty.id == specialty_id)
            count_stmt = count_stmt.join(Technician.specialties).where(Specialty.id == specialty_id)
        stmt = stmt.order_by(Technician.rating_avg.desc(), Technician.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)
        items = list((await self.session.execute(stmt)).scalars().unique().all())
        total = int((await self.session.execute(count_stmt)).scalar_one())
        return items, total


class SpecialtyRepository(BaseRepository[Specialty]):
    model = Specialty

    async def get_by_slug(self, slug: str) -> Specialty | None:
        stmt = select(Specialty).where(Specialty.slug == slug)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_active(self) -> list[Specialty]:
        stmt = select(Specialty).where(Specialty.is_active.is_(True)).order_by(Specialty.name)
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_by_ids(self, ids: list[uuid.UUID]) -> list[Specialty]:
        if not ids:
            return []
        stmt = select(Specialty).where(Specialty.id.in_(ids))
        return list((await self.session.execute(stmt)).scalars().all())

    async def is_in_use(self, specialty_id: uuid.UUID) -> bool:
        """True si algún técnico o solicitud referencia la especialidad."""
        technician_stmt = (
            select(func.count())
            .select_from(technician_specialties)
            .where(technician_specialties.c.specialty_id == specialty_id)
        )
        request_stmt = (
            select(func.count())
            .select_from(RepairRequest)
            .where(RepairRequest.specialty_id == specialty_id)
        )
        technicians = int((await self.session.execute(technician_stmt)).scalar_one())
        requests = int((await self.session.execute(request_stmt)).scalar_one())
        return (technicians + requests) > 0
