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
    PriceChangeStatus,
    QuotationStatus,
    RepairResult,
    RepairStatus,
    RequestStatus,
)
from app.models.order import (
    Order,
    OrderCostItem,
    OrderEvent,
    OrderPriceChange,
)
from app.models.quotation import Quotation
from app.models.repair import RepairRequest
from app.models.technician import Specialty, Technician
from app.models.user import User

_STATUS_PATH: dict[RepairStatus, list[tuple[RepairStatus, OrderEventType, str]]] = {
    RepairStatus.AWAITING_RECEIPT: [],
    RepairStatus.RECEIVED: [
        (RepairStatus.RECEIVED, OrderEventType.RECEIVED, "Equipo recibido"),
    ],
    RepairStatus.DIAGNOSIS: [
        (RepairStatus.RECEIVED, OrderEventType.RECEIVED, "Equipo recibido"),
        (RepairStatus.DIAGNOSIS, OrderEventType.DIAGNOSIS_STARTED, "Diagnóstico iniciado"),
    ],
    RepairStatus.WAITING_CUSTOMER: [
        (RepairStatus.RECEIVED, OrderEventType.RECEIVED, "Equipo recibido"),
        (RepairStatus.DIAGNOSIS, OrderEventType.DIAGNOSIS_STARTED, "Diagnóstico iniciado"),
        (
            RepairStatus.WAITING_CUSTOMER,
            OrderEventType.STATUS_CHANGED,
            "Esperando aprobación del cliente",
        ),
    ],
    RepairStatus.WAITING_PART: [
        (RepairStatus.RECEIVED, OrderEventType.RECEIVED, "Equipo recibido"),
        (RepairStatus.DIAGNOSIS, OrderEventType.DIAGNOSIS_STARTED, "Diagnóstico iniciado"),
        (RepairStatus.WAITING_PART, OrderEventType.PART_REQUESTED, "Esperando repuesto"),
    ],
    RepairStatus.IN_REPAIR: [
        (RepairStatus.RECEIVED, OrderEventType.RECEIVED, "Equipo recibido"),
        (RepairStatus.DIAGNOSIS, OrderEventType.DIAGNOSIS_STARTED, "Diagnóstico iniciado"),
        (RepairStatus.IN_REPAIR, OrderEventType.REPAIR_STARTED, "Reparación en curso"),
    ],
    RepairStatus.TESTING: [
        (RepairStatus.RECEIVED, OrderEventType.RECEIVED, "Equipo recibido"),
        (RepairStatus.DIAGNOSIS, OrderEventType.DIAGNOSIS_STARTED, "Diagnóstico iniciado"),
        (RepairStatus.IN_REPAIR, OrderEventType.REPAIR_STARTED, "Reparación en curso"),
        (RepairStatus.TESTING, OrderEventType.TESTING_STARTED, "Pruebas finales"),
    ],
    RepairStatus.READY: [
        (RepairStatus.RECEIVED, OrderEventType.RECEIVED, "Equipo recibido"),
        (RepairStatus.DIAGNOSIS, OrderEventType.DIAGNOSIS_STARTED, "Diagnóstico iniciado"),
        (RepairStatus.IN_REPAIR, OrderEventType.REPAIR_STARTED, "Reparación en curso"),
        (RepairStatus.TESTING, OrderEventType.TESTING_STARTED, "Pruebas finales"),
        (RepairStatus.READY, OrderEventType.STATUS_CHANGED, "Listo para entrega"),
    ],
    RepairStatus.COMPLETED: [
        (RepairStatus.RECEIVED, OrderEventType.RECEIVED, "Equipo recibido"),
        (RepairStatus.DIAGNOSIS, OrderEventType.DIAGNOSIS_STARTED, "Diagnóstico iniciado"),
        (RepairStatus.IN_REPAIR, OrderEventType.REPAIR_STARTED, "Reparación en curso"),
        (RepairStatus.COMPLETED, OrderEventType.COMPLETED, "Reparación finalizada"),
    ],
    RepairStatus.CANCELLED: [
        (RepairStatus.CANCELLED, OrderEventType.CANCELLED, "Reparación cancelada"),
    ],
}


async def _ensure_lifecycle_repair(
    session,
    *,
    customer: User,
    technician: Technician,
    specialty: Specialty,
    title: str,
    status: RepairStatus,
    price: int,
    location: dict,
    result: RepairResult | None = None,
    price_change: dict | None = None,
) -> Order | None:
    """Crea (idempotente) una reparación con un estado técnico concreto."""
    request = (
        await session.execute(
            select(RepairRequest).where(
                RepairRequest.customer_id == customer.id, RepairRequest.title == title
            )
        )
    ).scalar_one_or_none()
    if request is not None:
        return None
    request = RepairRequest(
        customer_id=customer.id,
        assigned_technician_id=technician.id,
        specialty_id=specialty.id,
        title=title,
        description="Caso de demostración del ciclo de reparación.",
        district=location["district"],
        city=location["city"],
        department_id=location["department_id"],
        province_id=location["province_id"],
        district_id=location["district_id"],
        modality=Modality.WORKSHOP,
        status=RequestStatus.ACCEPTED,
    )
    session.add(request)
    await session.flush()

    quotation = Quotation(
        request_id=request.id,
        technician_id=technician.id,
        price=price,
        preliminary_diagnosis="Diagnóstico preliminar de demostración.",
        estimated_days=2,
        status=QuotationStatus.ACCEPTED,
    )
    session.add(quotation)
    await session.flush()

    received = status != RepairStatus.AWAITING_RECEIPT
    order = Order(
        request_id=request.id,
        quotation_id=quotation.id,
        customer_id=customer.id,
        technician_id=technician.id,
        status=status,
        result=result if status == RepairStatus.COMPLETED else None,
        final_price=price,
        received_at=datetime.now(UTC) if received else None,
        completed_at=datetime.now(UTC) if status == RepairStatus.COMPLETED else None,
        diagnosis="Diagnóstico técnico de demostración.",
        work_performed="Trabajo realizado de demostración."
        if status == RepairStatus.COMPLETED
        else None,
        tests_performed="Pruebas realizadas de demostración."
        if status == RepairStatus.COMPLETED
        else None,
    )
    session.add(order)
    await session.flush()

    previous: RepairStatus | None = None
    for step_status, event_type, description in _STATUS_PATH[status]:
        session.add(
            OrderEvent(
                order_id=order.id,
                actor_id=technician.user_id,
                event_type=event_type,
                old_status=previous,
                new_status=step_status,
                description=description,
                visible_to_customer=True,
            )
        )
        previous = step_status
    if not _STATUS_PATH[status]:
        session.add(
            OrderEvent(
                order_id=order.id,
                actor_id=customer.id,
                event_type=OrderEventType.STATUS_CHANGED,
                old_status=None,
                new_status=RepairStatus.AWAITING_RECEIPT,
                description="Reparación creada al aceptar la cotización",
                visible_to_customer=True,
            )
        )

    if price_change:
        change_status = price_change.get("status", PriceChangeStatus.PENDING)
        decided = change_status != PriceChangeStatus.PENDING
        if change_status == PriceChangeStatus.APPROVED:
            order.final_price = price_change["new_price"]
        session.add(
            OrderPriceChange(
                order_id=order.id,
                previous_price=price,
                new_price=price_change["new_price"],
                reason=price_change["reason"],
                requested_by=technician.user_id,
                status=change_status,
                decided_by=customer.id if decided else None,
                decided_at=datetime.now(UTC) if decided else None,
            )
        )
        session.add(
            OrderEvent(
                order_id=order.id,
                actor_id=technician.user_id,
                event_type=OrderEventType.PRICE_CHANGE_PROPOSED,
                old_status=None,
                new_status=None,
                description=f"Nuevo costo propuesto: {price_change['reason']}",
                visible_to_customer=True,
            )
        )
        if change_status == PriceChangeStatus.APPROVED:
            session.add(
                OrderEvent(
                    order_id=order.id,
                    actor_id=customer.id,
                    event_type=OrderEventType.PRICE_CHANGE_APPROVED,
                    description="El cliente aprobó el nuevo costo",
                    visible_to_customer=True,
                )
            )
        elif change_status == PriceChangeStatus.REJECTED:
            session.add(
                OrderEvent(
                    order_id=order.id,
                    actor_id=customer.id,
                    event_type=OrderEventType.PRICE_CHANGE_REJECTED,
                    description="El cliente rechazó el nuevo costo",
                    visible_to_customer=True,
                )
            )
    if status == RepairStatus.COMPLETED:
        session.add(
            OrderCostItem(
                order_id=order.id,
                kind=CostKind.LABOR,
                description="Servicio técnico",
                amount=Decimal(str(price)),
                visible_to_customer=True,
                created_by=technician.user_id,
            )
        )
    await session.flush()
    return order
