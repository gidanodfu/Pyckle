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

"""Helpers del seed demo (logica reutilizable)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select

from app.models.enums import (
    CostKind,
    Modality,
    OrderEventType,
    QuotationStatus,
    RepairResult,
    RepairStatus,
    RequestStatus,
)
from app.models.order import (
    Order,
    OrderCostItem,
    OrderEvent,
)
from app.models.quotation import Quotation
from app.models.repair import RepairRequest
from app.models.review import Review
from app.models.technician import Specialty, Technician
from app.models.user import User


async def _ensure_completed_flow(
    session,
    *,
    customer: User,
    technician: Technician,
    specialty: Specialty,
    title: str,
    price: int,
    rating: int,
    comment: str | None,
    location: dict,
) -> None:
    request = (
        await session.execute(
            select(RepairRequest).where(
                RepairRequest.customer_id == customer.id, RepairRequest.title == title
            )
        )
    ).scalar_one_or_none()
    if request is None:
        request = RepairRequest(
            customer_id=customer.id,
            assigned_technician_id=technician.id,
            specialty_id=specialty.id,
            title=title,
            description="Solicitud de prueba generada por el seed demo.",
            district=location["district"],
            city=location["city"],
            department_id=location["department_id"],
            province_id=location["province_id"],
            district_id=location["district_id"],
            modality=Modality.WORKSHOP,
            status=RequestStatus.COMPLETED,
        )
        session.add(request)
        await session.flush()

    quotation = (
        await session.execute(
            select(Quotation).where(
                Quotation.request_id == request.id, Quotation.technician_id == technician.id
            )
        )
    ).scalar_one_or_none()
    if quotation is None:
        quotation = Quotation(
            request_id=request.id,
            technician_id=technician.id,
            price=price,
            preliminary_diagnosis="Diagnóstico preliminar de prueba.",
            estimated_days=2,
            status=QuotationStatus.ACCEPTED,
        )
        session.add(quotation)
        await session.flush()

    order = (
        await session.execute(select(Order).where(Order.quotation_id == quotation.id))
    ).scalar_one_or_none()
    if order is None:
        now = datetime.now(UTC)
        order = Order(
            request_id=request.id,
            quotation_id=quotation.id,
            customer_id=customer.id,
            technician_id=technician.id,
            status=RepairStatus.COMPLETED,
            result=RepairResult.REPAIRED,
            final_price=price,
            received_at=now,
            completed_at=now,
            diagnosis="Falla detectada y confirmada en banco de pruebas.",
            work_performed="Reemplazo del componente dañado y limpieza interna.",
            tests_performed="Pruebas de encendido, carga y estabilidad.",
        )
        session.add(order)
        await session.flush()
        session.add_all(
            [
                OrderEvent(
                    order_id=order.id,
                    actor_id=customer.id,
                    event_type=OrderEventType.STATUS_CHANGED,
                    old_status=None,
                    new_status=RepairStatus.AWAITING_RECEIPT,
                    description="Reparación creada al aceptar la cotización",
                    visible_to_customer=True,
                ),
                OrderEvent(
                    order_id=order.id,
                    actor_id=technician.user_id,
                    event_type=OrderEventType.RECEIVED,
                    old_status=RepairStatus.AWAITING_RECEIPT,
                    new_status=RepairStatus.RECEIVED,
                    description="Equipo recibido",
                    visible_to_customer=True,
                ),
                OrderEvent(
                    order_id=order.id,
                    actor_id=technician.user_id,
                    event_type=OrderEventType.REPAIR_STARTED,
                    old_status=RepairStatus.DIAGNOSIS,
                    new_status=RepairStatus.IN_REPAIR,
                    description="Reparación iniciada",
                    visible_to_customer=True,
                ),
                OrderEvent(
                    order_id=order.id,
                    actor_id=technician.user_id,
                    event_type=OrderEventType.COMPLETED,
                    old_status=RepairStatus.READY,
                    new_status=RepairStatus.COMPLETED,
                    description="Reparación completada",
                    visible_to_customer=True,
                ),
            ]
        )
        session.add_all(
            [
                OrderCostItem(
                    order_id=order.id,
                    kind=CostKind.PART,
                    description="Repuesto principal",
                    amount=Decimal(str(round(price * 0.4, 2))),
                    visible_to_customer=True,
                    created_by=technician.user_id,
                ),
                OrderCostItem(
                    order_id=order.id,
                    kind=CostKind.LABOR,
                    description="Servicio técnico",
                    amount=Decimal(str(round(price * 0.6, 2))),
                    visible_to_customer=True,
                    created_by=technician.user_id,
                ),
            ]
        )
        await session.flush()

    if rating:
        existing_review = (
            await session.execute(select(Review).where(Review.order_id == order.id))
        ).scalar_one_or_none()
        if existing_review is None:
            session.add(
                Review(
                    order_id=order.id,
                    customer_id=customer.id,
                    technician_id=technician.id,
                    rating=rating,
                    comment=comment,
                )
            )
    return order


async def _ensure_open_request(
    session,
    *,
    customer: User,
    technician: Technician,
    specialty: Specialty,
    title: str,
    description: str,
    price: int,
    location: dict,
    address: str | None,
    modality: Modality,
) -> None:
    request = (
        await session.execute(
            select(RepairRequest).where(
                RepairRequest.customer_id == customer.id, RepairRequest.title == title
            )
        )
    ).scalar_one_or_none()
    if request is None:
        request = RepairRequest(
            customer_id=customer.id,
            specialty_id=specialty.id,
            title=title,
            description=description,
            address=address,
            district=location["district"],
            city=location["city"],
            department_id=location["department_id"],
            province_id=location["province_id"],
            district_id=location["district_id"],
            modality=modality,
            status=RequestStatus.OPEN,
        )
        session.add(request)
        await session.flush()

    quotation = (
        await session.execute(
            select(Quotation).where(
                Quotation.request_id == request.id, Quotation.technician_id == technician.id
            )
        )
    ).scalar_one_or_none()
    if quotation is None:
        session.add(
            Quotation(
                request_id=request.id,
                technician_id=technician.id,
                price=price,
                preliminary_diagnosis="Cotización de prueba generada por el seed demo.",
                estimated_days=2,
                status=QuotationStatus.PENDING,
            )
        )
