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
from app.models.quotation import Quotation
from app.models.technician import Technician


class QuotationRepository(BaseRepository[Quotation]):
    model = Quotation

    def _detail(self):
        return select(Quotation).options(
            selectinload(Quotation.items),
            selectinload(Quotation.technician).selectinload(Technician.user),
            selectinload(Quotation.technician).selectinload(Technician.district_geo),
            selectinload(Quotation.request),
        )

    async def get_detail(self, quotation_id: uuid.UUID) -> Quotation | None:
        stmt = self._detail().where(Quotation.id == quotation_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_request_technician(
        self, request_id: uuid.UUID, technician_id: uuid.UUID
    ) -> Quotation | None:
        stmt = select(Quotation).where(
            Quotation.request_id == request_id, Quotation.technician_id == technician_id
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_for_request(self, request_id: uuid.UUID) -> list[Quotation]:
        stmt = (
            self._detail().where(Quotation.request_id == request_id).order_by(Quotation.created_at)
        )
        return list((await self.session.execute(stmt)).scalars().unique().all())

    async def list_for_technician(self, technician_id: uuid.UUID) -> list[Quotation]:
        stmt = (
            self._detail()
            .where(Quotation.technician_id == technician_id)
            .order_by(Quotation.created_at.desc())
        )
        return list((await self.session.execute(stmt)).scalars().unique().all())

    async def count_pending_for_technician(self, technician_id: uuid.UUID) -> int:
        stmt = select(func.count(Quotation.id)).where(
            Quotation.technician_id == technician_id, Quotation.status == "pending"
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def count_for_technician(self, technician_id: uuid.UUID) -> int:
        stmt = select(func.count(Quotation.id)).where(Quotation.technician_id == technician_id)
        return int((await self.session.execute(stmt)).scalar_one())
