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

from fastapi import APIRouter, Query

from app.core.dependencies import DbSession
from app.domains.admin.dependencies import AdminOrders, Moderate
from app.domains.orders.schemas import OrderListItem
from app.domains.orders.service import OrderService
from app.domains.repair_requests.schemas import RepairRequestRead
from app.domains.repair_requests.service import RepairRequestService
from app.models.enums import RepairResult, RepairStatus, RequestStatus
from app.schemas.common import Message, Page

router = APIRouter()


@router.get("/requests", response_model=Page[RepairRequestRead])
async def list_requests(
    session: DbSession,
    _: Moderate,
    status_filter: RequestStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Page[RepairRequestRead]:
    items, total = await RepairRequestService(session).list_all(
        status=status_filter, limit=limit, offset=offset
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.delete("/requests/{request_id}", response_model=Message)
async def delete_request(request_id: uuid.UUID, session: DbSession, _: Moderate) -> Message:
    await RepairRequestService(session).admin_delete(request_id)
    return Message(detail="Solicitud eliminada")


@router.get("/orders", response_model=Page[OrderListItem])
async def list_orders(
    session: DbSession,
    current_user: AdminOrders,
    status_filter: RepairStatus | None = Query(default=None, alias="status"),
    result: RepairResult | None = None,
    specialty_id: uuid.UUID | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Page[OrderListItem]:
    items, total = await OrderService(session).list_for_user(
        current_user,
        status=status_filter,
        result=result,
        specialty_id=specialty_id,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)
