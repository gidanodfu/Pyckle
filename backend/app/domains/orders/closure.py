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

"""Cierre de reparación: completar, no reparable y cancelar (mixin)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.core.exceptions import BadRequestError, ConflictError, ForbiddenError
from app.domains.orders.schemas import OrderCancel, OrderComplete, OrderNotRepairable, OrderRead
from app.models.chat import Conversation
from app.models.enums import (
    CUSTOMER_CANCELLABLE_STATUSES,
    TERMINAL_REPAIR_STATUSES,
    ConversationStatus,
    NotificationType,
    OrderEventType,
    PriceChangeStatus,
    RepairResult,
    RepairStatus,
    RequestStatus,
)
from app.models.order import Order
from app.models.user import User


class OrderClosureMixin:
    async def complete(self, order_id: uuid.UUID, user: User, data: OrderComplete) -> OrderRead:
        await self.repo.lock(order_id)
        order = await self._get_or_404(order_id)
        await self.access.assert_manage(order, user)
        if order.status in TERMINAL_REPAIR_STATUSES:
            if order.result == RepairResult.REPAIRED:
                return await self._read(
                    order.id,
                    include_internal=await self._include_internal(order, user),
                    can_see_address=True,
                )
            raise ConflictError("La reparación ya está cerrada con otro resultado")

        await self._assert_can_close(order)
        payload = data.model_dump(exclude_unset=True)
        for field in ("diagnosis", "work_performed", "tests_performed"):
            value = payload.get(field)
            if value:
                setattr(order, field, value)
        submitted_price = payload.get("final_price")
        if submitted_price is not None:
            approved_price = Decimal(submitted_price)
            await self._assert_approved_final_price(order, approved_price)
            order.final_price = approved_price
        await self._assert_close_data(order)

        previous = order.status
        order.status = RepairStatus.COMPLETED
        order.result = RepairResult.REPAIRED
        order.completed_at = datetime.now(UTC)
        order.request.status = RequestStatus.COMPLETED
        self._record_event(
            order,
            event_type=OrderEventType.COMPLETED,
            actor_id=user.id,
            old_status=previous,
            new_status=RepairStatus.COMPLETED,
            description=data.note or "Reparación completada",
        )
        try:
            await self._persist_report(order, actor_id=user.id)
            await self._archive_conversation(order.id)
            await self.notifications.create(
                order.customer_id,
                NotificationType.REPAIR_COMPLETED,
                "Reparación completada",
                f"Tu reparación '{order.request.title}' fue completada.",
                {"order_id": str(order.id)},
            )
            await self.notifications.create(
                order.customer_id,
                NotificationType.REPORT_AVAILABLE,
                "Informe disponible",
                "Ya puedes descargar el informe de reparación.",
                {"order_id": str(order.id)},
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            await self._cleanup_pending_report()
            raise
        return await self._read(
            order.id,
            include_internal=await self._include_internal(order, user),
            can_see_address=True,
        )

    async def not_repairable(
        self, order_id: uuid.UUID, user: User, data: OrderNotRepairable
    ) -> OrderRead:
        await self.repo.lock(order_id)
        order = await self._get_or_404(order_id)
        await self.access.assert_manage(order, user)
        if order.status in TERMINAL_REPAIR_STATUSES:
            if order.result == RepairResult.NOT_REPAIRABLE:
                return await self._read(
                    order.id,
                    include_internal=await self._include_internal(order, user),
                    can_see_address=True,
                )
            raise ConflictError("La reparación ya está cerrada con otro resultado")
        if order.status == RepairStatus.AWAITING_RECEIPT:
            raise BadRequestError("El equipo debe estar recepcionado antes del diagnóstico")
        await self._assert_can_close(order)

        order.diagnosis = data.diagnosis
        reason = data.reason
        if data.recommendation:
            reason = f"{reason}\n\nRecomendación: {data.recommendation}"
        order.not_repairable_reason = reason
        order.status = RepairStatus.COMPLETED
        order.result = RepairResult.NOT_REPAIRABLE
        order.completed_at = datetime.now(UTC)
        order.request.status = RequestStatus.COMPLETED
        self._record_event(
            order,
            event_type=OrderEventType.NOT_REPAIRABLE,
            actor_id=user.id,
            new_status=RepairStatus.COMPLETED,
            description=data.reason,
        )
        try:
            await self._persist_report(order, actor_id=user.id)
            await self._archive_conversation(order.id)
            await self.notifications.create(
                order.customer_id,
                NotificationType.REPAIR_NOT_REPAIRABLE,
                "Reparación no reparable",
                f"El equipo de '{order.request.title}' no pudo repararse.",
                {"order_id": str(order.id)},
            )
            await self.notifications.create(
                order.customer_id,
                NotificationType.REPORT_AVAILABLE,
                "Informe disponible",
                "Ya puedes descargar el informe de reparación.",
                {"order_id": str(order.id)},
            )
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            await self._cleanup_pending_report()
            raise
        return await self._read(
            order.id,
            include_internal=await self._include_internal(order, user),
            can_see_address=True,
        )

    async def cancel(self, order_id: uuid.UUID, user: User, data: OrderCancel) -> OrderRead:
        await self.repo.lock(order_id)
        order = await self._get_or_404(order_id)
        if order.status in TERMINAL_REPAIR_STATUSES:
            raise ConflictError("La reparación ya está cerrada")

        is_customer = order.customer_id == user.id
        is_assigned = await self.access.is_assigned(order, user)
        if is_customer:
            if order.status not in CUSTOMER_CANCELLABLE_STATUSES:
                raise ForbiddenError("La reparación ya inició; contacta al técnico para cancelar")
        elif not is_assigned:
            # El administrador es solo lectura: tampoco puede cancelar.
            raise ForbiddenError("No puedes cancelar esta reparación")

        await self._reject_pending_changes(order, actor_id=user.id)
        order.status = RepairStatus.CANCELLED
        order.result = RepairResult.CANCELLED
        order.completed_at = datetime.now(UTC)
        order.request.status = RequestStatus.CANCELLED
        self._record_event(
            order,
            event_type=OrderEventType.CANCELLED,
            actor_id=user.id,
            new_status=RepairStatus.CANCELLED,
            description=data.reason,
        )
        await self._archive_conversation(order.id)
        recipient = order.technician.user_id if is_customer else order.customer_id
        await self.notifications.create(
            recipient,
            NotificationType.REPAIR_CANCELLED,
            "Reparación cancelada",
            data.reason,
            {"order_id": str(order.id)},
        )
        await self.session.commit()
        return await self._read(
            order.id,
            include_internal=await self._include_internal(order, user),
            can_see_address=True,
        )

    async def _reject_pending_changes(self, order: Order, *, actor_id: uuid.UUID) -> None:
        pending = await self.price_changes.get_pending(order.id)
        if pending is not None:
            pending.status = PriceChangeStatus.REJECTED
            pending.decided_by = actor_id
            pending.decided_at = datetime.now(UTC)
            pending.decided_note = "Rechazado automáticamente al cerrar la reparación"

    async def _assert_can_close(self, order: Order) -> None:
        if order.received_at is None:
            raise BadRequestError("El equipo debe estar recepcionado antes de cerrar")
        if await self.price_changes.get_pending(order.id) is not None:
            raise ConflictError("Hay un cambio de precio pendiente de aprobación del cliente")

    async def _assert_close_data(self, order: Order) -> None:
        if not (order.diagnosis or "").strip():
            raise BadRequestError("Registra el diagnóstico antes de completar")
        if not (order.work_performed or "").strip():
            raise BadRequestError("Registra el trabajo realizado antes de completar")
        if order.final_price is None or order.final_price < 0:
            raise BadRequestError("El precio final es obligatorio")

    async def _assert_approved_final_price(self, order: Order, new_price: Decimal) -> None:
        """El precio final solo puede coincidir con el precio aprobado vigente.

        El único flujo autorizado para mover ``final_price`` es el de cambios de
        precio (una reducción se auto-aprueba; un aumento requiere aprobación
        del cliente). Aceptar aquí un valor arbitrario saltaría ese control, por
        lo que solo se admite el valor aprobado persistido o un cambio APROBADO
        que lo respalde. Se decide con estado de BD, nunca con datos del request.
        """
        if new_price == order.final_price:
            return
        if await self.price_changes.has_approved_price(order.id, new_price):
            return
        raise BadRequestError(
            "El precio final debe coincidir con el precio aprobado; "
            "usa el flujo de cambio de precio para modificarlo"
        )

    async def _archive_conversation(self, order_id: uuid.UUID) -> None:
        conversation: Conversation | None = await self.conversations.get_by_order(order_id)
        if conversation is None or conversation.status != ConversationStatus.OPEN:
            return
        conversation.status = ConversationStatus.ARCHIVED
        conversation.closed_at = datetime.now(UTC)
