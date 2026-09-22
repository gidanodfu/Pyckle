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

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, DbSession
from app.domains.orders.schemas import OrderRead
from app.domains.quotations.schemas import QuotationAccept, QuotationCreate, QuotationRead
from app.domains.quotations.service import QuotationService

router = APIRouter(prefix="/quotations", tags=["quotations"])


@router.post("", response_model=QuotationRead, status_code=status.HTTP_201_CREATED)
async def create_quotation(
    data: QuotationCreate, current_user: CurrentUser, session: DbSession
) -> QuotationRead:
    return await QuotationService(session).create(current_user, data)


@router.get("/mine", response_model=list[QuotationRead])
async def my_quotations(current_user: CurrentUser, session: DbSession) -> list[QuotationRead]:
    return await QuotationService(session).list_for_technician(current_user)


@router.get("/request/{request_id}", response_model=list[QuotationRead])
async def quotations_for_request(
    request_id: uuid.UUID, current_user: CurrentUser, session: DbSession
) -> list[QuotationRead]:
    return await QuotationService(session).list_for_request(request_id, current_user)


@router.post("/{quotation_id}/accept", response_model=OrderRead)
async def accept_quotation(
    quotation_id: uuid.UUID,
    data: QuotationAccept,
    current_user: CurrentUser,
    session: DbSession,
) -> OrderRead:
    return await QuotationService(session).accept(quotation_id, current_user, data.note)


@router.post("/{quotation_id}/withdraw", response_model=QuotationRead)
async def withdraw_quotation(
    quotation_id: uuid.UUID, current_user: CurrentUser, session: DbSession
) -> QuotationRead:
    return await QuotationService(session).withdraw(quotation_id, current_user)
