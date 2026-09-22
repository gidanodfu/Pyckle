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

"""Transiciones técnicas y detalles de una reparación (mixin de OrderService)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.core.exceptions import BadRequestError, ConflictError
from app.domains.orders.events import record_event
from app.domains.orders.schemas import OrderRead, RepairDetailsUpdate
from app.models.enums import (
    ALLOWED_STATUS_TRANSITIONS,
    TERMINAL_REPAIR_STATUSES,
    NotificationType,
    OrderEventType,
    RepairStatus,
    RequestStatus,
)
from app.models.order import Order, OrderEvent
from app.models.user import User

BLOCKED_BY_PENDING_PRICE = {
    RepairStatus.IN_REPAIR,
    RepairStatus.TESTING,
    RepairStatus.READY,
}

STATUS_NOTIFICATIONS: dict[RepairStatus, tuple[NotificationType, str, str]] = {
    RepairStatus.RECEIVED: (
        NotificationType.REPAIR_RECEIVED,
        "Equipo recibido",
        "El técnico registró la recepción de tu equipo.",
    ),
    RepairStatus.IN_REPAIR: (
        NotificationType.REPAIR_IN_PROGRESS,
        "Reparación en curso",
        "La reparación de tu equipo está en curso.",
    ),
    RepairStatus.READY: (
        NotificationType.REPAIR_READY,
        "Reparación lista",
        "Tu equipo está listo para entrega.",
    ),
}


class OrderLifecycleMixin:
    async def transition_status(
        self, order_id: uuid.UUID, user: User, new_status: RepairStatus, note: str | None
    ) -> OrderRead:
        await self.repo.lock(order_id)
        order = await self._get_or_404(order_id)
        await self.access.assert_manage(order, user)
        if order.status in TERMINAL_REPAIR_STATUSES:
            raise ConflictError("La reparación ya está cerrada")
        if new_status in TERMINAL_REPAIR_STATUSES:
            raise BadRequestError(
                "El cierre usa las acciones de completar, no reparable o cancelar"
            )
        if new_status not in ALLOWED_STATUS_TRANSITIONS[order.status]:
            raise BadRequestError(f"Transición inválida: {order.status} -> {new_status}")
        if (
            new_status in BLOCKED_BY_PENDING_PRICE
            and await self.price_changes.get_pending(order.id) is not None
        ):
            raise ConflictError("Hay un cambio de precio pendiente de aprobación del cliente")

        previous = order.status
        order.status = new_status
        if new_status == RepairStatus.RECEIVED:
            order.received_at = datetime.now(UTC)
        if (
            new_status != RepairStatus.AWAITING_RECEIPT
            and order.request.status == RequestStatus.ACCEPTED
        ):
            order.request.status = RequestStatus.IN_PROGRESS
        self._record_event(
            order,
            event_type=self._event_type_for_status(new_status),
            actor_id=user.id,
            old_status=previous,
            new_status=new_status,
            description=note or f"Estado cambiado a {new_status.value}",
            metadata={"note": note} if note else None,
        )
        await self._notify_status(order, new_status)
        await self.session.commit()
        return await self._read(
            order.id,
            include_internal=await self._include_internal(order, user),
            can_see_address=True,
        )

    async def update_details(
        self, order_id: uuid.UUID, user: User, data: RepairDetailsUpdate
    ) -> OrderRead:
        await self.repo.lock(order_id)
        order = await self._get_or_404(order_id)
        await self.access.assert_manage(order, user)
        if order.status in TERMINAL_REPAIR_STATUSES:
            raise ConflictError("La reparación ya está cerrada")
        payload = data.model_dump(exclude_unset=True)
        for field, value in payload.items():
            setattr(order, field, value)
        self._record_event(
            order,
            event_type=OrderEventType.NOTE,
            actor_id=user.id,
            description="Detalles técnicos actualizados",
            visible_to_customer=False,
        )
        await self.session.commit()
        return await self._read(
            order.id,
            include_internal=await self._include_internal(order, user),
            can_see_address=True,
        )

    # ----------------------------------------------------------------- helpers

    async def _notify_status(self, order: Order, status: RepairStatus) -> None:
        config = STATUS_NOTIFICATIONS.get(status)
        if config is None:
            return
        notification_type, title, body = config
        await self.notifications.create(
            order.customer_id, notification_type, title, body, {"order_id": str(order.id)}
        )

    @staticmethod
    def _event_type_for_status(status: RepairStatus) -> OrderEventType:
        mapping = {
            RepairStatus.RECEIVED: OrderEventType.RECEIVED,
            RepairStatus.DIAGNOSIS: OrderEventType.DIAGNOSIS_STARTED,
            RepairStatus.WAITING_PART: OrderEventType.PART_REQUESTED,
            RepairStatus.IN_REPAIR: OrderEventType.REPAIR_STARTED,
            RepairStatus.TESTING: OrderEventType.TESTING_STARTED,
        }
        return mapping.get(status, OrderEventType.STATUS_CHANGED)

    def _record_event(
        self,
        order: Order,
        *,
        event_type: OrderEventType,
        actor_id: uuid.UUID | None,
        old_status: RepairStatus | None = None,
        new_status: RepairStatus | None = None,
        description: str | None = None,
        visible_to_customer: bool = True,
        metadata: dict | None = None,
    ) -> OrderEvent:
        return record_event(
            self.session,
            order,
            event_type=event_type,
            actor_id=actor_id,
            old_status=old_status,
            new_status=new_status,
            description=description,
            visible_to_customer=visible_to_customer,
            metadata=metadata,
        )
