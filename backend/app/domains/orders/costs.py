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

"""Costos internos/visibles de una reparación (mixin de OrderService)."""

from __future__ import annotations

import uuid

from app.core.exceptions import ConflictError
from app.domains.orders.schemas import CostItemCreate
from app.models.enums import TERMINAL_REPAIR_STATUSES
from app.models.order import OrderCostItem
from app.models.user import User


class OrderCostsMixin:
    async def add_cost_item(self, order_id: uuid.UUID, user: User, data: CostItemCreate):
        await self.repo.lock(order_id)
        order = await self._get_or_404(order_id)
        await self.access.assert_manage(order, user)
        if order.status in TERMINAL_REPAIR_STATUSES:
            raise ConflictError("La reparación ya está cerrada")
        item = OrderCostItem(
            order_id=order.id,
            kind=data.kind,
            description=data.description,
            amount=data.amount,
            visible_to_customer=data.visible_to_customer,
            created_by=user.id,
        )
        self.session.add(item)
        await self.session.commit()
        return item

    async def list_costs(self, order_id: uuid.UUID, user: User):
        order = await self._get_or_404(order_id)
        await self.access.assert_can_view(order, user)
        include_internal = await self._include_internal(order, user)
        return await self.costs.list_for_order(order.id, visible_only=not include_internal)
