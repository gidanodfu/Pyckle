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

"""Fachada de órdenes/reparaciones: compone lectura, ciclo, costos e informes."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.conversations.repository import ConversationRepository
from app.domains.notifications.service import NotificationService
from app.domains.orders.access import OrderAccess
from app.domains.orders.closure import OrderClosureMixin
from app.domains.orders.costs import OrderCostsMixin
from app.domains.orders.lifecycle import OrderLifecycleMixin
from app.domains.orders.read import OrderReadMixin, build_order_read
from app.domains.orders.reporting import OrderReportsMixin
from app.domains.orders.repository import (
    OrderCostItemRepository,
    OrderEventRepository,
    OrderPriceChangeRepository,
    OrderRepository,
    RepairReportRepository,
)
from app.domains.users.repository import UserRepository
from app.infrastructure.storage import StorageBackend, build_storage


class OrderService(
    OrderReadMixin,
    OrderLifecycleMixin,
    OrderClosureMixin,
    OrderCostsMixin,
    OrderReportsMixin,
):
    def __init__(self, session: AsyncSession, storage: StorageBackend | None = None) -> None:
        self.session = session
        self.repo = OrderRepository(session)
        self.events = OrderEventRepository(session)
        self.price_changes = OrderPriceChangeRepository(session)
        self.costs = OrderCostItemRepository(session)
        self.reports = RepairReportRepository(session)
        self.users = UserRepository(session)
        self.conversations = ConversationRepository(session)
        self.access = OrderAccess(session)
        self.notifications = NotificationService(session)
        self.storage = storage or build_storage()
        self._pending_report_key: str | None = None


__all__ = ["OrderService", "build_order_read"]
