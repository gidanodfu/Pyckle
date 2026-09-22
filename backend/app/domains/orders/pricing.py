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

"""Cambios de precio de una reparación y su aprobación por el cliente."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.domains.notifications.service import NotificationService
from app.domains.orders.access import OrderAccess
from app.domains.orders.events import record_event
from app.domains.orders.repository import OrderPriceChangeRepository, OrderRepository
from app.domains.orders.schemas import (
    PriceChangeCreate,
    PriceChangeDecision,
    PriceChangeRead,
)
from app.models.enums import (
    TERMINAL_REPAIR_STATUSES,
    NotificationType,
    OrderEventType,
    PriceChangeStatus,
    RepairStatus,
)
from app.models.order import Order, OrderPriceChange
from app.models.user import User


class PriceChangeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.orders = OrderRepository(session)
        self.changes = OrderPriceChangeRepository(session)
        self.access = OrderAccess(session)
        self.notifications = NotificationService(session)

    async def list_for_user(self, order_id: uuid.UUID, user: User) -> list[PriceChangeRead]:
        order = await self._get_or_404(order_id)
        await self.access.assert_can_view(order, user)
        changes = await self.changes.list_for_order(order.id)
        return [PriceChangeRead.model_validate(change) for change in changes]

    async def propose(
        self, order_id: uuid.UUID, user: User, data: PriceChangeCreate
    ) -> PriceChangeRead:
        await self.orders.lock(order_id)
        order = await self._get_or_404(order_id)
        await self.access.assert_manage(order, user)
        if order.status in TERMINAL_REPAIR_STATUSES:
            raise ConflictError("La reparación ya está cerrada")
        if await self.changes.get_pending(order.id) is not None:
            raise ConflictError("Ya existe un cambio de precio pendiente de aprobación")

        previous = Decimal(order.final_price)
        new_price = Decimal(data.new_price)
        if new_price == previous:
            raise BadRequestError("El nuevo precio debe ser distinto al actual")

        auto_approved = new_price < previous
        change = OrderPriceChange(
            order_id=order.id,
            previous_price=previous,
            new_price=new_price,
            reason=data.reason,
            requested_by=user.id,
            status=PriceChangeStatus.APPROVED if auto_approved else PriceChangeStatus.PENDING,
            decided_by=user.id if auto_approved else None,
            decided_at=datetime.now(UTC) if auto_approved else None,
            decided_note="Reducción registrada" if auto_approved else None,
        )
        self.session.add(change)

        if auto_approved:
            order.final_price = new_price
            record_event(
                self.session,
                order,
                event_type=OrderEventType.PRICE_CHANGE_APPROVED,
                actor_id=user.id,
                description=(
                    f"Precio reducido de S/ {previous:.2f} a S/ {new_price:.2f}: {data.reason}"
                ),
                metadata={"previous_price": str(previous), "new_price": str(new_price)},
            )
            await self.notifications.create(
                order.customer_id,
                NotificationType.PRICE_CHANGE_APPROVED,
                "Precio actualizado",
                f"El precio de tu reparación bajó a S/ {new_price:.2f}.",
                {"order_id": str(order.id)},
            )
        else:
            if order.status != RepairStatus.WAITING_CUSTOMER:
                previous_status = order.status
                order.status = RepairStatus.WAITING_CUSTOMER
                record_event(
                    self.session,
                    order,
                    event_type=OrderEventType.STATUS_CHANGED,
                    actor_id=user.id,
                    old_status=previous_status,
                    new_status=RepairStatus.WAITING_CUSTOMER,
                    description="Esperando aprobación del cliente",
                )
            record_event(
                self.session,
                order,
                event_type=OrderEventType.PRICE_CHANGE_PROPOSED,
                actor_id=user.id,
                description=f"Nuevo costo propuesto de S/ {new_price:.2f}: {data.reason}",
                metadata={"previous_price": str(previous), "new_price": str(new_price)},
            )
            await self.notifications.create(
                order.customer_id,
                NotificationType.PRICE_CHANGE_REQUESTED,
                "Aprobación de nuevo costo",
                f"El técnico propone un nuevo precio de S/ {new_price:.2f}. Revísalo.",
                {"order_id": str(order.id)},
            )
        await self.session.commit()
        return PriceChangeRead.model_validate(change)

    async def approve(
        self, order_id: uuid.UUID, change_id: uuid.UUID, user: User, data: PriceChangeDecision
    ) -> PriceChangeRead:
        return await self._decide(order_id, change_id, user, data, approve=True)

    async def reject(
        self, order_id: uuid.UUID, change_id: uuid.UUID, user: User, data: PriceChangeDecision
    ) -> PriceChangeRead:
        return await self._decide(order_id, change_id, user, data, approve=False)

    async def _decide(
        self,
        order_id: uuid.UUID,
        change_id: uuid.UUID,
        user: User,
        data: PriceChangeDecision,
        *,
        approve: bool,
    ) -> PriceChangeRead:
        await self.orders.lock(order_id)
        order = await self._get_or_404(order_id)
        if order.status in TERMINAL_REPAIR_STATUSES:
            raise ConflictError("La reparación ya está cerrada")
        if order.customer_id != user.id:
            raise ForbiddenError("Solo el cliente puede decidir sobre el cambio de precio")
        change = await self.changes.get(change_id)
        if change is None or change.order_id != order.id:
            raise NotFoundError("Cambio de precio no encontrado")
        if change.status != PriceChangeStatus.PENDING:
            raise ConflictError("El cambio de precio ya fue decidido")

        change.status = PriceChangeStatus.APPROVED if approve else PriceChangeStatus.REJECTED
        change.decided_by = user.id
        change.decided_at = datetime.now(UTC)
        change.decided_note = data.note

        if approve:
            order.final_price = change.new_price
            record_event(
                self.session,
                order,
                event_type=OrderEventType.PRICE_CHANGE_APPROVED,
                actor_id=user.id,
                description=f"El cliente aprobó el nuevo precio de S/ {change.new_price:.2f}",
            )
            await self.notifications.create(
                order.technician.user_id,
                NotificationType.PRICE_CHANGE_APPROVED,
                "Cambio de precio aprobado",
                "El cliente aprobó el nuevo costo propuesto.",
                {"order_id": str(order.id)},
            )
        else:
            record_event(
                self.session,
                order,
                event_type=OrderEventType.PRICE_CHANGE_REJECTED,
                actor_id=user.id,
                description="El cliente rechazó el nuevo costo propuesto",
            )
            await self.notifications.create(
                order.technician.user_id,
                NotificationType.PRICE_CHANGE_REJECTED,
                "Cambio de precio rechazado",
                "El cliente rechazó el nuevo costo propuesto.",
                {"order_id": str(order.id)},
            )
            if order.status == RepairStatus.WAITING_CUSTOMER:
                order.status = RepairStatus.DIAGNOSIS
                record_event(
                    self.session,
                    order,
                    event_type=OrderEventType.STATUS_CHANGED,
                    actor_id=user.id,
                    old_status=RepairStatus.WAITING_CUSTOMER,
                    new_status=RepairStatus.DIAGNOSIS,
                    description="Replanificación tras rechazo del costo adicional",
                )
        await self.session.commit()
        return PriceChangeRead.model_validate(change)

    async def _get_or_404(self, order_id: uuid.UUID) -> Order:
        order = await self.orders.get_detail(order_id)
        if order is None:
            raise NotFoundError("Orden no encontrada")
        return order
