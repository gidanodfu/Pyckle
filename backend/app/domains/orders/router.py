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

import uuid
from datetime import datetime

from fastapi import APIRouter, Query, Response, status

from app.core.dependencies import CurrentUser, DbSession
from app.core.paths import order_report_path
from app.domains.orders.pricing import PriceChangeService
from app.domains.orders.schemas import (
    CostItemCreate,
    CostItemRead,
    OrderCancel,
    OrderComplete,
    OrderListItem,
    OrderNotRepairable,
    OrderRead,
    OrderStatusUpdate,
    PriceChangeCreate,
    PriceChangeDecision,
    PriceChangeRead,
    RepairDetailsUpdate,
    ReportRead,
)
from app.domains.orders.service import OrderService
from app.domains.users.schemas import CustomerPublicProfile
from app.models.enums import RepairResult, RepairStatus
from app.schemas.common import Page

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=Page[OrderListItem])
async def list_orders(
    current_user: CurrentUser,
    session: DbSession,
    status_filter: RepairStatus | None = Query(default=None, alias="status"),
    result: RepairResult | None = None,
    specialty_id: uuid.UUID | None = None,
    request_id: uuid.UUID | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Page[OrderListItem]:
    items, total = await OrderService(session).list_for_user(
        current_user,
        status=status_filter,
        result=result,
        specialty_id=specialty_id,
        request_id=request_id,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: uuid.UUID, current_user: CurrentUser, session: DbSession
) -> OrderRead:
    return await OrderService(session).get_for_user(order_id, current_user)


@router.get("/{order_id}/customer-profile", response_model=CustomerPublicProfile)
async def customer_profile(
    order_id: uuid.UUID, current_user: CurrentUser, session: DbSession
) -> CustomerPublicProfile:
    return await OrderService(session).customer_profile(order_id, current_user)


@router.patch("/{order_id}/status", response_model=OrderRead)
async def update_order_status(
    order_id: uuid.UUID,
    data: OrderStatusUpdate,
    current_user: CurrentUser,
    session: DbSession,
) -> OrderRead:
    return await OrderService(session).transition_status(
        order_id, current_user, data.status, data.note
    )


@router.put("/{order_id}/repair-details", response_model=OrderRead)
async def update_repair_details(
    order_id: uuid.UUID,
    data: RepairDetailsUpdate,
    current_user: CurrentUser,
    session: DbSession,
) -> OrderRead:
    return await OrderService(session).update_details(order_id, current_user, data)


@router.post("/{order_id}/complete", response_model=OrderRead)
async def complete_order(
    order_id: uuid.UUID,
    data: OrderComplete,
    current_user: CurrentUser,
    session: DbSession,
) -> OrderRead:
    return await OrderService(session).complete(order_id, current_user, data)


@router.post("/{order_id}/not-repairable", response_model=OrderRead)
async def not_repairable_order(
    order_id: uuid.UUID,
    data: OrderNotRepairable,
    current_user: CurrentUser,
    session: DbSession,
) -> OrderRead:
    return await OrderService(session).not_repairable(order_id, current_user, data)


@router.post("/{order_id}/cancel", response_model=OrderRead)
async def cancel_order(
    order_id: uuid.UUID,
    data: OrderCancel,
    current_user: CurrentUser,
    session: DbSession,
) -> OrderRead:
    return await OrderService(session).cancel(order_id, current_user, data)


@router.get("/{order_id}/price-changes", response_model=list[PriceChangeRead])
async def list_price_changes(
    order_id: uuid.UUID, current_user: CurrentUser, session: DbSession
) -> list[PriceChangeRead]:
    return await PriceChangeService(session).list_for_user(order_id, current_user)


@router.post(
    "/{order_id}/price-changes",
    response_model=PriceChangeRead,
    status_code=status.HTTP_201_CREATED,
)
async def propose_price_change(
    order_id: uuid.UUID,
    data: PriceChangeCreate,
    current_user: CurrentUser,
    session: DbSession,
) -> PriceChangeRead:
    return await PriceChangeService(session).propose(order_id, current_user, data)


@router.post("/{order_id}/price-changes/{change_id}/approve", response_model=PriceChangeRead)
async def approve_price_change(
    order_id: uuid.UUID,
    change_id: uuid.UUID,
    data: PriceChangeDecision,
    current_user: CurrentUser,
    session: DbSession,
) -> PriceChangeRead:
    return await PriceChangeService(session).approve(order_id, change_id, current_user, data)


@router.post("/{order_id}/price-changes/{change_id}/reject", response_model=PriceChangeRead)
async def reject_price_change(
    order_id: uuid.UUID,
    change_id: uuid.UUID,
    data: PriceChangeDecision,
    current_user: CurrentUser,
    session: DbSession,
) -> PriceChangeRead:
    return await PriceChangeService(session).reject(order_id, change_id, current_user, data)


@router.get("/{order_id}/costs", response_model=list[CostItemRead])
async def list_costs(
    order_id: uuid.UUID, current_user: CurrentUser, session: DbSession
) -> list[CostItemRead]:
    items = await OrderService(session).list_costs(order_id, current_user)
    return [CostItemRead.model_validate(item) for item in items]


@router.post("/{order_id}/costs", response_model=CostItemRead, status_code=status.HTTP_201_CREATED)
async def add_cost(
    order_id: uuid.UUID,
    data: CostItemCreate,
    current_user: CurrentUser,
    session: DbSession,
) -> CostItemRead:
    item = await OrderService(session).add_cost_item(order_id, current_user, data)
    return CostItemRead.model_validate(item)


@router.get("/{order_id}/reports", response_model=list[ReportRead])
async def list_reports(
    order_id: uuid.UUID, current_user: CurrentUser, session: DbSession
) -> list[ReportRead]:
    reports = await OrderService(session).list_reports(order_id, current_user)
    return [
        ReportRead(
            id=report.id,
            version=report.version,
            content_type=report.content_type,
            size_bytes=report.size_bytes,
            generated_at=report.generated_at,
            download_url=order_report_path(order_id),
        )
        for report in reports
    ]


@router.get("/{order_id}/report")
async def download_report(
    order_id: uuid.UUID, current_user: CurrentUser, session: DbSession
) -> Response:
    report, data = await OrderService(session).get_report(order_id, current_user)
    filename = f"informe-reparacion-{str(order_id)[:8]}-v{report.version}.pdf"
    return Response(
        content=data,
        media_type=report.content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "private, no-store",
        },
    )
