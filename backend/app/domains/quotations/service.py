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

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.domains.conversations.repository import ConversationRepository
from app.domains.notifications.service import NotificationService
from app.domains.orders.repository import OrderRepository
from app.domains.orders.schemas import OrderRead
from app.domains.orders.service import build_order_read
from app.domains.quotations.repository import QuotationRepository
from app.domains.quotations.schemas import QuotationCreate, QuotationRead
from app.domains.repair_requests.repository import RepairRequestRepository
from app.domains.reviews.repository import ReviewRepository
from app.domains.reviews.service import build_review_public
from app.domains.technicians.repository import TechnicianRepository
from app.models.chat import Conversation
from app.models.enums import (
    NotificationType,
    OrderEventType,
    PermissionCode,
    QuotationStatus,
    RepairStatus,
    RequestStatus,
)
from app.models.order import Order, OrderEvent
from app.models.quotation import Quotation, QuotationItem
from app.models.user import User


class QuotationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = QuotationRepository(session)
        self.requests = RepairRequestRepository(session)
        self.technicians = TechnicianRepository(session)
        self.orders = OrderRepository(session)
        self.conversations = ConversationRepository(session)
        self.reviews = ReviewRepository(session)
        self.notifications = NotificationService(session)

    async def create(self, user: User, data: QuotationCreate) -> QuotationRead:
        technician = await self.technicians.get_by_user_id(user.id)
        if technician is None:
            raise ForbiddenError("El usuario no tiene perfil de técnico")
        if not technician.is_verified:
            raise ForbiddenError("Tu cuenta de técnico debe estar verificada para cotizar")
        request = await self.requests.get_detail(data.request_id)
        if request is None:
            raise NotFoundError("Solicitud no encontrada")
        if request.customer_id == user.id:
            raise BadRequestError("No puedes cotizar tu propia solicitud")
        if request.status not in {RequestStatus.OPEN, RequestStatus.QUOTED}:
            raise BadRequestError("La solicitud ya no acepta cotizaciones")
        specialty_ids = {s.id for s in technician.specialties}
        if request.specialty_id and request.specialty_id not in specialty_ids:
            raise ForbiddenError("La solicitud no corresponde a tus especialidades")
        if await self.repo.get_by_request_technician(request.id, technician.id):
            raise ConflictError("Ya enviaste una cotización para esta solicitud")

        quotation = Quotation(
            request_id=request.id,
            technician_id=technician.id,
            price=data.price,
            preliminary_diagnosis=data.preliminary_diagnosis,
            estimated_days=data.estimated_days,
            valid_until=data.valid_until,
        )
        for item in data.items:
            quotation.items.append(
                QuotationItem(
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total=item.unit_price * item.quantity,
                )
            )
        await self.repo.add(quotation)
        if request.status == RequestStatus.OPEN:
            request.status = RequestStatus.QUOTED
        await self.session.commit()

        await self.notifications.create(
            request.customer_id,
            NotificationType.QUOTATION_CREATED,
            "Nueva cotización recibida",
            f"{technician.full_name} envio una cotización de S/ {data.price}.",
            {"request_id": str(request.id), "quotation_id": str(quotation.id)},
        )
        await self.session.commit()
        return await self._to_read(quotation.id)

    async def list_for_request(self, request_id: uuid.UUID, user: User) -> list[QuotationRead]:
        request = await self.requests.get_detail(request_id)
        if request is None:
            raise NotFoundError("Solicitud no encontrada")
        if request.customer_id != user.id:
            if PermissionCode.REPAIR_REQUEST_MODERATE not in user.permission_codes:
                technician = await self.technicians.get_by_user_id(user.id)
                own = (
                    await self.repo.get_by_request_technician(request_id, technician.id)
                    if technician is not None
                    else None
                )
                if own is None:
                    raise ForbiddenError("No tienes acceso a las cotizaciones de esta solicitud")
                # Un técnico solo ve su propia cotización; nunca las de la competencia.
                return await self._with_reviews([own])
        quotations = await self.repo.list_for_request(request_id)
        return await self._with_reviews(quotations)

    async def list_for_technician(self, user: User) -> list[QuotationRead]:
        technician = await self.technicians.get_by_user_id(user.id)
        if technician is None:
            raise ForbiddenError("El usuario no tiene perfil de técnico")
        quotations = await self.repo.list_for_technician(technician.id)
        return await self._with_reviews(quotations)

    async def accept(self, quotation_id: uuid.UUID, user: User, note: str | None) -> OrderRead:
        quotation = await self.repo.get_detail(quotation_id)
        if quotation is None:
            raise NotFoundError("Cotización no encontrada")
        # Serializa aceptaciones concurrentes sobre la misma solicitud.
        await self.requests.lock(quotation.request_id)
        quotation = await self.repo.get_detail(quotation_id)
        if quotation is None:
            raise NotFoundError("Cotización no encontrada")
        request = quotation.request
        if request.customer_id != user.id:
            raise ForbiddenError("Solo el cliente puede aceptar esta cotización")
        if quotation.status != QuotationStatus.PENDING:
            raise BadRequestError("La cotización ya no está pendiente")
        if request.status not in {RequestStatus.OPEN, RequestStatus.QUOTED}:
            raise BadRequestError("La solicitud ya no acepta cotizaciones")

        for other in await self.repo.list_for_request(request.id):
            if other.id != quotation.id and other.status == QuotationStatus.PENDING:
                other.status = QuotationStatus.REJECTED
        quotation.status = QuotationStatus.ACCEPTED
        request.status = RequestStatus.ACCEPTED
        request.assigned_technician_id = quotation.technician_id

        order = Order(
            request_id=request.id,
            quotation_id=quotation.id,
            customer_id=request.customer_id,
            technician_id=quotation.technician_id,
            status=RepairStatus.AWAITING_RECEIPT,
            final_price=quotation.price,
        )
        self.session.add(order)
        await self.session.flush()
        self.session.add(
            OrderEvent(
                order_id=order.id,
                actor_id=user.id,
                event_type=OrderEventType.STATUS_CHANGED,
                old_status=None,
                new_status=RepairStatus.AWAITING_RECEIPT,
                description=note or "Reparación creada al aceptar la cotización",
                visible_to_customer=True,
            )
        )

        conversation = await self.conversations.get_by_request_technician(
            request.id, quotation.technician_id
        )
        if conversation is None:
            self.session.add(
                Conversation(
                    request_id=request.id,
                    customer_id=request.customer_id,
                    technician_id=quotation.technician_id,
                    order_id=order.id,
                )
            )
        else:
            conversation.order_id = order.id
        await self.session.commit()

        await self.notifications.create(
            quotation.technician.user_id,
            NotificationType.QUOTATION_ACCEPTED,
            "Cotización aceptada",
            f"Tu cotización para '{request.title}' fue aceptada.",
            {"order_id": str(order.id), "request_id": str(request.id)},
        )
        await self.session.commit()
        created = await self.orders.get_detail(order.id)
        if created is None:
            raise NotFoundError("Orden no encontrada")
        return build_order_read(created, can_see_address=True)

    async def _to_read(self, quotation_id: uuid.UUID) -> QuotationRead:
        quotation = await self.repo.get_detail(quotation_id)
        if quotation is None:
            raise NotFoundError("Cotización no encontrada")
        return (await self._with_reviews([quotation]))[0]

    async def _with_reviews(self, quotations: list[Quotation]) -> list[QuotationRead]:
        technician_ids = list({q.technician_id for q in quotations})
        reviews = await self.reviews.list_recent_for_technicians(technician_ids, limit=3)
        result: list[QuotationRead] = []
        for quotation in quotations:
            read = QuotationRead.model_validate(quotation)
            read.technician_reviews = [
                build_review_public(review) for review in reviews.get(quotation.technician_id, [])
            ]
            result.append(read)
        return result

    async def withdraw(self, quotation_id: uuid.UUID, user: User) -> QuotationRead:
        quotation = await self.repo.get_detail(quotation_id)
        if quotation is None:
            raise NotFoundError("Cotización no encontrada")
        technician = await self.technicians.get_by_user_id(user.id)
        if technician is None or quotation.technician_id != technician.id:
            raise ForbiddenError("No puedes retirar esta cotización")
        if quotation.status != QuotationStatus.PENDING:
            raise BadRequestError("Solo se pueden retirar cotizaciones pendientes")
        quotation.status = QuotationStatus.WITHDRAWN
        await self.session.commit()
        return QuotationRead.model_validate(quotation)
