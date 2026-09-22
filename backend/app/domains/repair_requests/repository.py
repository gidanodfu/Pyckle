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
from app.models.enums import RequestStatus
from app.models.repair import RepairRequest, RepairRequestImage
from app.models.technician import Specialty, Technician


class RepairRequestRepository(BaseRepository[RepairRequest]):
    model = RepairRequest

    def _detail(self):
        return select(RepairRequest).options(
            selectinload(RepairRequest.images),
            selectinload(RepairRequest.specialty),
            selectinload(RepairRequest.customer),
            selectinload(RepairRequest.assigned_technician).selectinload(Technician.user),
            selectinload(RepairRequest.assigned_technician).selectinload(Technician.district_geo),
            selectinload(RepairRequest.department),
            selectinload(RepairRequest.province),
            selectinload(RepairRequest.district_geo),
        )

    async def get_detail(self, request_id: uuid.UUID) -> RepairRequest | None:
        stmt = self._detail().where(RepairRequest.id == request_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def lock(self, request_id: uuid.UUID) -> None:
        """Bloquea la fila de la solicitud dentro de la transacción actual."""
        await self.session.execute(
            select(RepairRequest.id).where(RepairRequest.id == request_id).with_for_update()
        )

    async def list_for_customer(
        self,
        customer_id: uuid.UUID,
        *,
        status: RequestStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[RepairRequest], int]:
        return await self._paginated(
            [RepairRequest.customer_id == customer_id]
            + ([RepairRequest.status == status] if status else []),
            limit,
            offset,
        )

    async def list_available(
        self,
        *,
        specialty_ids: list[uuid.UUID],
        customer_id: uuid.UUID,
        department_id: uuid.UUID | None = None,
        province_id: uuid.UUID | None = None,
        district_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[RepairRequest], int]:
        conditions = [
            RepairRequest.status.in_([RequestStatus.OPEN, RequestStatus.QUOTED]),
            RepairRequest.customer_id != customer_id,
        ]
        if specialty_ids:
            conditions.append(
                (RepairRequest.specialty_id.in_(specialty_ids))
                | (RepairRequest.specialty_id.is_(None))
            )
        if district_id is not None:
            conditions.append(RepairRequest.district_id == district_id)
        elif province_id is not None:
            conditions.append(RepairRequest.province_id == province_id)
        elif department_id is not None:
            conditions.append(RepairRequest.department_id == department_id)
        return await self._paginated(conditions, limit, offset)

    async def list_all(
        self, *, status: RequestStatus | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[RepairRequest], int]:
        conditions = [RepairRequest.status == status] if status else []
        return await self._paginated(conditions, limit, offset)

    async def _paginated(
        self, conditions: list, limit: int, offset: int
    ) -> tuple[list[RepairRequest], int]:
        stmt = self._detail().where(*conditions)
        count_stmt = select(func.count(RepairRequest.id)).where(*conditions)
        stmt = stmt.order_by(RepairRequest.created_at.desc()).limit(limit).offset(offset)
        items = list((await self.session.execute(stmt)).scalars().unique().all())
        total = int((await self.session.execute(count_stmt)).scalar_one())
        return items, total

    async def count_by_status(self) -> dict[str, int]:
        stmt = select(RepairRequest.status, func.count()).group_by(RepairRequest.status)
        return {
            status.value: int(count) for status, count in (await self.session.execute(stmt)).all()
        }

    async def count_images(self, request_id: uuid.UUID) -> int:
        stmt = select(func.count(RepairRequestImage.id)).where(
            RepairRequestImage.request_id == request_id
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def count_for_customer(self, customer_id: uuid.UUID) -> int:
        stmt = select(func.count(RepairRequest.id)).where(RepairRequest.customer_id == customer_id)
        return int((await self.session.execute(stmt)).scalar_one())


class RepairRequestImageRepository(BaseRepository[RepairRequestImage]):
    model = RepairRequestImage

    async def get_by_storage_key(self, storage_key: str) -> RepairRequestImage | None:
        stmt = select(RepairRequestImage).where(RepairRequestImage.storage_key == storage_key)
        return (await self.session.execute(stmt)).scalar_one_or_none()


class SpecialtyLookupRepository(BaseRepository[Specialty]):
    model = Specialty
