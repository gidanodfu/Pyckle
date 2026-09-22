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

"""Lectura y serialización role-aware de órdenes (mixin de OrderService)."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.paths import order_report_path
from app.domains.orders.schemas import (
    CostItemRead,
    OrderEventRead,
    OrderListItem,
    OrderRead,
    PriceChangeRead,
    ReportRead,
)
from app.domains.users.schemas import CustomerPublicProfile
from app.models.enums import PriceChangeStatus, RepairResult, RepairStatus
from app.models.order import Order
from app.models.user import User


def build_order_read(order: Order, *, can_see_address: bool = False) -> OrderRead:
    """Vista de orden para el cliente propietario (sin datos internos)."""
    return _serialize(order, include_internal=False, can_see_address=can_see_address)


def _report_read(order: Order) -> ReportRead | None:
    latest = order.reports[-1] if order.reports else None
    if latest is None:
        return None
    return ReportRead(
        id=latest.id,
        version=latest.version,
        content_type=latest.content_type,
        size_bytes=latest.size_bytes,
        generated_at=latest.generated_at,
        download_url=order_report_path(order.id),
    )


def _serialize(order: Order, *, include_internal: bool, can_see_address: bool) -> OrderRead:
    read = OrderRead.model_validate(order)
    read.service_address = order.request.address if can_see_address else None
    read.technician_notes = order.technician_notes if include_internal else None
    read.events = [
        OrderEventRead.model_validate(event)
        for event in order.events
        if include_internal or event.visible_to_customer
    ]
    read.price_changes = [PriceChangeRead.model_validate(c) for c in order.price_changes]
    read.cost_items = [
        CostItemRead.model_validate(item)
        for item in order.cost_items
        if include_internal or item.visible_to_customer
    ]
    read.report_versions = len(order.reports)
    read.report = _report_read(order)
    read.has_pending_price_change = any(
        change.status == PriceChangeStatus.PENDING for change in order.price_changes
    )
    read.has_review = order.review is not None
    return read


class OrderReadMixin:
    async def list_for_user(
        self,
        user: User,
        *,
        status: RepairStatus | None = None,
        result: RepairResult | None = None,
        specialty_id: uuid.UUID | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        request_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[OrderListItem], int]:
        filters = {
            "status": status,
            "result": result,
            "specialty_id": specialty_id,
            "from_date": from_date,
            "to_date": to_date,
        }
        if self.access.is_admin(user):
            items, total = await self.repo.list_all(
                limit=limit, offset=offset, request_id=request_id, **filters
            )
        else:
            technician = await self._technician_for(user)
            if technician is not None:
                items, total = await self.repo.list_for_technician(
                    technician.id, limit=limit, offset=offset, request_id=request_id, **filters
                )
            else:
                items, total = await self.repo.list_for_customer(
                    user.id, limit=limit, offset=offset, request_id=request_id, **filters
                )
        return [self._to_list_item(order) for order in items], total

    async def get_for_user(self, order_id: uuid.UUID, user: User) -> OrderRead:
        order = await self._get_or_404(order_id)
        await self.access.assert_can_view(order, user)
        include_internal = await self._include_internal(order, user)
        can_see_address = await self.access.can_see_address(order, user)
        return _serialize(order, include_internal=include_internal, can_see_address=can_see_address)

    async def customer_profile(self, order_id: uuid.UUID, user: User) -> CustomerPublicProfile:
        """Perfil público del cliente para el técnico asignado o un administrador."""
        order = await self._get_or_404(order_id)
        if not (self.access.is_admin(user) or await self.access.is_assigned(order, user)):
            raise ForbiddenError("No tienes acceso al perfil de este cliente")
        customer = await self.users.get_me(order.customer_id)
        if customer is None:
            raise NotFoundError("Cliente no encontrado")
        completed = await self.repo.count_for_customer(customer.id, [RepairStatus.COMPLETED])
        profile = customer.customer_profile
        return CustomerPublicProfile(
            id=customer.id,
            full_name=customer.full_name,
            member_since=customer.created_at,
            completed_repairs=completed,
            department_name=profile.department.name if profile and profile.department else None,
            province_name=profile.province.name if profile and profile.province else None,
            district_name=(profile.district_geo.name if profile and profile.district_geo else None),
        )

    async def _technician_for(self, user: User):
        from app.domains.technicians.repository import TechnicianRepository

        return await TechnicianRepository(self.session).get_by_user_id(user.id)

    async def _include_internal(self, order: Order, user: User) -> bool:
        return self.access.is_admin(user) or await self.access.is_assigned(order, user)

    async def _get_or_404(self, order_id: uuid.UUID) -> Order:
        order = await self.repo.get_detail(order_id)
        if order is None:
            raise NotFoundError("Orden no encontrada")
        return order

    async def _read(
        self, order_id: uuid.UUID, *, include_internal: bool, can_see_address: bool
    ) -> OrderRead:
        order = await self._get_or_404(order_id)
        return _serialize(order, include_internal=include_internal, can_see_address=can_see_address)

    def _to_list_item(self, order: Order) -> OrderListItem:
        read = OrderListItem.model_validate(order)
        read.has_pending_price_change = any(
            change.status == PriceChangeStatus.PENDING for change in order.price_changes
        )
        read.has_report = bool(order.reports)
        return read
