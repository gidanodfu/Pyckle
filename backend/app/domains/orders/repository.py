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
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.infrastructure.repository import BaseRepository
from app.models.enums import PriceChangeStatus, RepairResult, RepairStatus
from app.models.order import (
    Order,
    OrderCostItem,
    OrderEvent,
    OrderPriceChange,
    RepairReport,
)
from app.models.quotation import Quotation
from app.models.repair import RepairRequest
from app.models.technician import Specialty, Technician


class OrderRepository(BaseRepository[Order]):
    model = Order

    def _detail(self):
        return select(Order).options(
            selectinload(Order.request).selectinload(RepairRequest.specialty),
            selectinload(Order.request).selectinload(RepairRequest.department),
            selectinload(Order.request).selectinload(RepairRequest.province),
            selectinload(Order.request).selectinload(RepairRequest.district_geo),
            selectinload(Order.quotation).selectinload(Quotation.items),
            selectinload(Order.quotation)
            .selectinload(Quotation.technician)
            .selectinload(Technician.user),
            selectinload(Order.quotation)
            .selectinload(Quotation.technician)
            .selectinload(Technician.district_geo),
            selectinload(Order.customer),
            selectinload(Order.technician).selectinload(Technician.user),
            selectinload(Order.technician).selectinload(Technician.district_geo),
            selectinload(Order.events).selectinload(OrderEvent.actor),
            selectinload(Order.price_changes),
            selectinload(Order.cost_items),
            selectinload(Order.reports),
            selectinload(Order.review),
        )

    def _summary(self):
        return select(Order).options(
            selectinload(Order.request).selectinload(RepairRequest.specialty),
            selectinload(Order.request).selectinload(RepairRequest.department),
            selectinload(Order.request).selectinload(RepairRequest.province),
            selectinload(Order.request).selectinload(RepairRequest.district_geo),
            selectinload(Order.customer),
            selectinload(Order.technician).selectinload(Technician.user),
            selectinload(Order.technician).selectinload(Technician.district_geo),
            selectinload(Order.price_changes),
            selectinload(Order.reports),
        )

    async def get_detail(self, order_id: uuid.UUID) -> Order | None:
        stmt = self._detail().where(Order.id == order_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def lock(self, order_id: uuid.UUID) -> None:
        """Bloquea la fila de la orden dentro de la transacción actual."""
        await self.session.execute(select(Order.id).where(Order.id == order_id).with_for_update())

    @staticmethod
    def _filters(
        *,
        status: RepairStatus | None = None,
        result: RepairResult | None = None,
        specialty_id: uuid.UUID | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list:
        conditions: list = []
        if status is not None:
            conditions.append(Order.status == status)
        if result is not None:
            conditions.append(Order.result == result)
        if specialty_id is not None:
            conditions.append(Order.request.has(RepairRequest.specialty_id == specialty_id))
        if from_date is not None:
            conditions.append(Order.created_at >= from_date)
        if to_date is not None:
            conditions.append(Order.created_at <= to_date)
        return conditions

    async def _paginated(self, conditions: list, limit: int, offset: int):
        stmt = self._summary().where(*conditions)
        count_stmt = select(func.count(Order.id)).where(*conditions)
        stmt = stmt.order_by(Order.created_at.desc()).limit(limit).offset(offset)
        items = list((await self.session.execute(stmt)).scalars().unique().all())
        total = int((await self.session.execute(count_stmt)).scalar_one())
        return items, total

    async def list_for_customer(
        self,
        customer_id: uuid.UUID,
        *,
        limit: int = 50,
        offset: int = 0,
        request_id: uuid.UUID | None = None,
        **filters,
    ):
        conditions = [Order.customer_id == customer_id]
        if request_id is not None:
            conditions.append(Order.request_id == request_id)
        conditions.extend(self._filters(**filters))
        return await self._paginated(conditions, limit, offset)

    async def list_for_technician(
        self,
        technician_id: uuid.UUID,
        *,
        limit: int = 50,
        offset: int = 0,
        request_id: uuid.UUID | None = None,
        **filters,
    ):
        conditions = [Order.technician_id == technician_id]
        if request_id is not None:
            conditions.append(Order.request_id == request_id)
        conditions.extend(self._filters(**filters))
        return await self._paginated(conditions, limit, offset)

    async def list_all(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        request_id: uuid.UUID | None = None,
        **filters,
    ):
        conditions: list = []
        if request_id is not None:
            conditions.append(Order.request_id == request_id)
        conditions.extend(self._filters(**filters))
        return await self._paginated(conditions, limit, offset)

    async def count_for_customer(self, customer_id: uuid.UUID, statuses=None) -> int:
        stmt = select(func.count(Order.id)).where(Order.customer_id == customer_id)
        if statuses:
            stmt = stmt.where(Order.status.in_(statuses))
        return int((await self.session.execute(stmt)).scalar_one())

    async def count_for_technician(self, technician_id: uuid.UUID, statuses=None) -> int:
        stmt = select(func.count(Order.id)).where(Order.technician_id == technician_id)
        if statuses:
            stmt = stmt.where(Order.status.in_(statuses))
        return int((await self.session.execute(stmt)).scalar_one())

    async def count_active_for_technician(self, technician_id: uuid.UUID) -> int:
        stmt = select(func.count(Order.id)).where(
            Order.technician_id == technician_id,
            Order.status.notin_([RepairStatus.COMPLETED, RepairStatus.CANCELLED]),
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def count_pending_price_changes_for_technician(self, technician_id: uuid.UUID) -> int:
        stmt = (
            select(func.count(OrderPriceChange.id))
            .select_from(OrderPriceChange)
            .join(Order, OrderPriceChange.order_id == Order.id)
            .where(
                Order.technician_id == technician_id,
                OrderPriceChange.status == PriceChangeStatus.PENDING,
            )
        )
        return int((await self.session.execute(stmt)).scalar_one())

    async def sum_completed_for_technician(self, technician_id: uuid.UUID):
        stmt = select(func.coalesce(func.sum(Order.final_price), 0)).where(
            Order.technician_id == technician_id, Order.result == RepairResult.REPAIRED
        )
        return (await self.session.execute(stmt)).scalar_one()

    async def total_revenue(self):
        stmt = select(func.coalesce(func.sum(Order.final_price), 0)).where(
            Order.result == RepairResult.REPAIRED
        )
        return (await self.session.execute(stmt)).scalar_one()

    async def count_completed(self) -> int:
        stmt = select(func.count(Order.id)).where(Order.result == RepairResult.REPAIRED)
        return int((await self.session.execute(stmt)).scalar_one())

    async def counts_by_status_for_technician(self, technician_id: uuid.UUID) -> dict[str, int]:
        stmt = (
            select(Order.status, func.count())
            .where(Order.technician_id == technician_id)
            .group_by(Order.status)
        )
        return {
            status.value: int(count) for status, count in (await self.session.execute(stmt)).all()
        }

    async def counts_by_specialty_for_technician(
        self, technician_id: uuid.UUID
    ) -> list[tuple[uuid.UUID, str, int]]:
        stmt = (
            select(Specialty.id, Specialty.name, func.count(Order.id))
            .select_from(Order)
            .join(RepairRequest, Order.request_id == RepairRequest.id)
            .join(Specialty, RepairRequest.specialty_id == Specialty.id)
            .where(Order.technician_id == technician_id)
            .group_by(Specialty.id, Specialty.name)
            .order_by(func.count(Order.id).desc())
        )
        return [(row[0], row[1], int(row[2])) for row in (await self.session.execute(stmt)).all()]

    async def count_by_result_for_technician(self, technician_id: uuid.UUID) -> dict[str, int]:
        stmt = (
            select(Order.result, func.count())
            .where(Order.technician_id == technician_id, Order.result.is_not(None))
            .group_by(Order.result)
        )
        return {
            result.value: int(count) for result, count in (await self.session.execute(stmt)).all()
        }


class OrderEventRepository(BaseRepository[OrderEvent]):
    model = OrderEvent

    async def list_for_order(
        self, order_id: uuid.UUID, *, visible_only: bool = False
    ) -> list[OrderEvent]:
        stmt = (
            select(OrderEvent)
            .options(selectinload(OrderEvent.actor))
            .where(OrderEvent.order_id == order_id)
        )
        if visible_only:
            stmt = stmt.where(OrderEvent.visible_to_customer.is_(True))
        stmt = stmt.order_by(OrderEvent.created_at.asc())
        return list((await self.session.execute(stmt)).scalars().all())


class OrderPriceChangeRepository(BaseRepository[OrderPriceChange]):
    model = OrderPriceChange

    async def list_for_order(self, order_id: uuid.UUID) -> list[OrderPriceChange]:
        stmt = (
            select(OrderPriceChange)
            .where(OrderPriceChange.order_id == order_id)
            .order_by(OrderPriceChange.created_at.asc())
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_pending(self, order_id: uuid.UUID) -> OrderPriceChange | None:
        stmt = select(OrderPriceChange).where(
            OrderPriceChange.order_id == order_id,
            OrderPriceChange.status == PriceChangeStatus.PENDING,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def has_approved_price(self, order_id: uuid.UUID, price) -> bool:
        stmt = select(OrderPriceChange.id).where(
            OrderPriceChange.order_id == order_id,
            OrderPriceChange.status == PriceChangeStatus.APPROVED,
            OrderPriceChange.new_price == price,
        )
        return (await self.session.execute(stmt)).first() is not None


class OrderCostItemRepository(BaseRepository[OrderCostItem]):
    model = OrderCostItem

    async def list_for_order(
        self, order_id: uuid.UUID, *, visible_only: bool = False
    ) -> list[OrderCostItem]:
        stmt = select(OrderCostItem).where(OrderCostItem.order_id == order_id)
        if visible_only:
            stmt = stmt.where(OrderCostItem.visible_to_customer.is_(True))
        stmt = stmt.order_by(OrderCostItem.created_at.asc())
        return list((await self.session.execute(stmt)).scalars().all())


class RepairReportRepository(BaseRepository[RepairReport]):
    model = RepairReport

    async def get_latest(self, order_id: uuid.UUID) -> RepairReport | None:
        stmt = (
            select(RepairReport)
            .where(RepairReport.order_id == order_id)
            .order_by(RepairReport.version.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def next_version(self, order_id: uuid.UUID) -> int:
        stmt = select(func.coalesce(func.max(RepairReport.version), 0)).where(
            RepairReport.order_id == order_id
        )
        return int((await self.session.execute(stmt)).scalar_one()) + 1

    async def list_for_order(self, order_id: uuid.UUID) -> list[RepairReport]:
        stmt = (
            select(RepairReport)
            .where(RepairReport.order_id == order_id)
            .order_by(RepairReport.version.desc())
        )
        return list((await self.session.execute(stmt)).scalars().all())
