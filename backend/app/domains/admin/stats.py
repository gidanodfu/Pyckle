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

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.admin.schemas import DashboardStats
from app.domains.orders.repository import OrderRepository
from app.domains.repair_requests.repository import RepairRequestRepository
from app.domains.users.repository import UserRepository
from app.models.enums import RequestStatus, RoleName


class StatsService:
    def __init__(self, session: AsyncSession) -> None:
        self.users = UserRepository(session)
        self.orders = OrderRepository(session)
        self.requests = RepairRequestRepository(session)

    async def dashboard(self) -> DashboardStats:
        by_status = await self.requests.count_by_status()
        return DashboardStats(
            total_users=await self.users.count(),
            total_customers=await self.users.count_by_role(RoleName.CUSTOMER),
            total_technicians=await self.users.count_by_role(RoleName.TECHNICIAN),
            total_requests=await self.requests.count(),
            open_requests=by_status.get(RequestStatus.OPEN.value, 0),
            total_orders=await self.orders.count(),
            completed_orders=await self.orders.count_completed(),
            total_revenue=Decimal(await self.orders.total_revenue()),
            requests_by_status=by_status,
        )
