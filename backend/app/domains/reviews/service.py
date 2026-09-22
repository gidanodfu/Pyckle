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
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.domains.notifications.service import NotificationService
from app.domains.orders.repository import OrderRepository
from app.domains.reviews.repository import ReviewRepository
from app.domains.reviews.schemas import ReviewCreate, ReviewPublic, ReviewRead
from app.domains.technicians.repository import TechnicianRepository
from app.domains.users.schemas import UserBrief
from app.models.enums import NotificationType, RepairStatus
from app.models.review import Review
from app.models.user import User


def build_review_public(review: Review) -> ReviewPublic:
    return ReviewPublic(
        id=review.id,
        rating=review.rating,
        comment=review.comment,
        customer_name=review.customer.full_name if review.customer else "Cliente",
        created_at=review.created_at,
    )


class ReviewService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = ReviewRepository(session)
        self.orders = OrderRepository(session)
        self.technicians = TechnicianRepository(session)
        self.notifications = NotificationService(session)

    async def create(self, user: User, data: ReviewCreate) -> ReviewRead:
        order = await self.orders.get_detail(data.order_id)
        if order is None:
            raise NotFoundError("Orden no encontrada")
        if order.customer_id != user.id:
            raise ForbiddenError("Solo el cliente puede calificar esta orden")
        if order.status != RepairStatus.COMPLETED:
            raise BadRequestError("Solo se pueden calificar ordenes completadas")
        if await self.repo.get_by_order(order.id):
            raise ConflictError("Esta orden ya tiene una reseña")

        review = Review(
            order_id=order.id,
            customer_id=user.id,
            technician_id=order.technician_id,
            rating=data.rating,
            comment=data.comment,
        )
        await self.repo.add(review)

        average, count = await self.repo.stats_for_technician(order.technician_id)
        technician = await self.technicians.get(order.technician_id)
        if technician is not None:
            technician.rating_avg = Decimal(str(round(average, 2)))
            technician.rating_count = count
        await self.session.commit()

        await self.notifications.create(
            order.technician.user_id,
            NotificationType.REVIEW_CREATED,
            "Nueva reseña recibida",
            f"Recibiste una calificación de {data.rating}/5.",
            {"order_id": str(order.id), "rating": data.rating},
        )
        await self.session.commit()
        return ReviewRead(
            id=review.id,
            order_id=review.order_id,
            rating=review.rating,
            comment=review.comment,
            customer=UserBrief.model_validate(order.customer),
            created_at=review.created_at,
        )

    async def list_for_technician(
        self, technician_id: uuid.UUID, limit: int = 50
    ) -> list[ReviewPublic]:
        reviews = await self.repo.list_for_technician(technician_id, limit=limit)
        return [build_review_public(review) for review in reviews]
