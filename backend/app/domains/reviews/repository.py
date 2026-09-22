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
from app.models.review import Review


class ReviewRepository(BaseRepository[Review]):
    model = Review

    async def get_by_order(self, order_id: uuid.UUID) -> Review | None:
        stmt = select(Review).where(Review.order_id == order_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_for_technician(self, technician_id: uuid.UUID, limit: int = 50) -> list[Review]:
        stmt = (
            select(Review)
            .options(selectinload(Review.customer))
            .where(Review.technician_id == technician_id)
            .order_by(Review.created_at.desc())
            .limit(limit)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_recent_for_technicians(
        self, technician_ids: list[uuid.UUID], limit: int = 3
    ) -> dict[uuid.UUID, list[Review]]:
        """Ultimas reseñas por técnico en una sola consulta (evita N+1)."""
        if not technician_ids:
            return {}
        ranked = (
            select(
                Review.id.label("review_id"),
                func.row_number()
                .over(
                    partition_by=Review.technician_id,
                    order_by=Review.created_at.desc(),
                )
                .label("position"),
            )
            .where(Review.technician_id.in_(technician_ids))
            .subquery()
        )
        stmt = (
            select(Review)
            .options(selectinload(Review.customer))
            .join(ranked, Review.id == ranked.c.review_id)
            .where(ranked.c.position <= limit)
            .order_by(Review.created_at.desc())
        )
        reviews = list((await self.session.execute(stmt)).scalars().all())
        grouped: dict[uuid.UUID, list[Review]] = {}
        for review in reviews:
            grouped.setdefault(review.technician_id, []).append(review)
        return grouped

    async def count_for_customer(self, customer_id: uuid.UUID) -> int:
        stmt = select(func.count(Review.id)).where(Review.customer_id == customer_id)
        return int((await self.session.execute(stmt)).scalar_one())

    async def count_for_technician(self, technician_id: uuid.UUID) -> int:
        stmt = select(func.count(Review.id)).where(Review.technician_id == technician_id)
        return int((await self.session.execute(stmt)).scalar_one())

    async def stats_for_technician(self, technician_id: uuid.UUID) -> tuple[float, int]:
        stmt = select(func.avg(Review.rating), func.count(Review.id)).where(
            Review.technician_id == technician_id
        )
        avg, count = (await self.session.execute(stmt)).one()
        return (float(avg) if avg is not None else 0.0), int(count)
