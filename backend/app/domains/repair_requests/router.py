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

from fastapi import APIRouter, File, Query, UploadFile, status

from app.core.config import get_settings
from app.core.dependencies import CurrentUser, DbSession
from app.domains.repair_requests.schemas import (
    RepairRequestCreate,
    RepairRequestRead,
    RepairRequestUpdate,
)
from app.domains.repair_requests.service import RepairRequestService
from app.models.enums import RequestStatus
from app.schemas.common import Page

router = APIRouter(prefix="/repair-requests", tags=["repair-requests"])
settings = get_settings()


@router.post("", response_model=RepairRequestRead, status_code=status.HTTP_201_CREATED)
async def create_request(
    data: RepairRequestCreate, current_user: CurrentUser, session: DbSession
) -> RepairRequestRead:
    return await RepairRequestService(session).create(current_user, data)


@router.get("", response_model=Page[RepairRequestRead])
async def list_my_requests(
    current_user: CurrentUser,
    session: DbSession,
    status_filter: RequestStatus | None = Query(default=None, alias="status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Page[RepairRequestRead]:
    items, total = await RepairRequestService(session).list_for_customer(
        current_user.id, status=status_filter, limit=limit, offset=offset
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.get("/available", response_model=Page[RepairRequestRead])
async def list_available_requests(
    current_user: CurrentUser,
    session: DbSession,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Page[RepairRequestRead]:
    items, total, scope, expanded = await RepairRequestService(session).list_available(
        current_user, limit=limit, offset=offset
    )
    return Page(
        items=items, total=total, limit=limit, offset=offset, scope=scope, expanded=expanded
    )


@router.get("/{request_id}", response_model=RepairRequestRead)
async def get_request(
    request_id: uuid.UUID, current_user: CurrentUser, session: DbSession
) -> RepairRequestRead:
    return await RepairRequestService(session).get_for_user(request_id, current_user)


@router.patch("/{request_id}", response_model=RepairRequestRead)
async def update_request(
    request_id: uuid.UUID,
    data: RepairRequestUpdate,
    current_user: CurrentUser,
    session: DbSession,
) -> RepairRequestRead:
    return await RepairRequestService(session).update(request_id, current_user, data)


@router.post("/{request_id}/cancel", response_model=RepairRequestRead)
async def cancel_request(
    request_id: uuid.UUID, current_user: CurrentUser, session: DbSession
) -> RepairRequestRead:
    return await RepairRequestService(session).cancel(request_id, current_user)


@router.post("/{request_id}/images", response_model=RepairRequestRead)
async def upload_image(
    request_id: uuid.UUID,
    current_user: CurrentUser,
    session: DbSession,
    file: UploadFile = File(...),
) -> RepairRequestRead:
    content = await file.read(settings.max_upload_size_bytes + 1)
    return await RepairRequestService(session).add_image(
        request_id, current_user, content, file.content_type or ""
    )
