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

from fastapi import APIRouter, Query

from app.core.dependencies import CurrentUser, DbSession, OptionalUser
from app.domains.reviews.schemas import ReviewPublic
from app.domains.reviews.service import ReviewService
from app.domains.technicians.schemas import (
    TechnicianProfileUpdate,
    TechnicianPublic,
    TechnicianRead,
    TechnicianStats,
    TechnicianSummary,
)
from app.domains.technicians.service import TechnicianService
from app.schemas.common import Page

router = APIRouter(prefix="/technicians", tags=["technicians"])


@router.get("", response_model=Page[TechnicianPublic])
async def list_technicians(
    session: DbSession,
    current_user: OptionalUser,
    specialty_id: uuid.UUID | None = None,
    verified_only: bool = False,
    search: str | None = None,
    department_id: uuid.UUID | None = None,
    province_id: uuid.UUID | None = None,
    district_id: uuid.UUID | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Page[TechnicianPublic]:
    items, total, scope, expanded = await TechnicianService(session).list_public(
        specialty_id=specialty_id,
        verified_only=verified_only,
        search=search,
        viewer=current_user,
        department_id=department_id,
        province_id=province_id,
        district_id=district_id,
        limit=limit,
        offset=offset,
    )
    return Page(
        items=items, total=total, limit=limit, offset=offset, scope=scope, expanded=expanded
    )


@router.get("/me", response_model=TechnicianRead)
async def my_profile(current_user: CurrentUser, session: DbSession) -> TechnicianRead:
    return await TechnicianService(session).get_for_user(current_user.id)


@router.patch("/me", response_model=TechnicianRead)
async def update_my_profile(
    data: TechnicianProfileUpdate, current_user: CurrentUser, session: DbSession
) -> TechnicianRead:
    return await TechnicianService(session).update_profile(current_user.id, data)


@router.get("/me/stats", response_model=TechnicianStats)
async def my_stats(current_user: CurrentUser, session: DbSession) -> TechnicianStats:
    return await TechnicianService(session).stats(current_user.id)


@router.get("/me/summary", response_model=TechnicianSummary)
async def my_summary(current_user: CurrentUser, session: DbSession) -> TechnicianSummary:
    return await TechnicianService(session).summary(current_user.id)


@router.get("/{technician_id}", response_model=TechnicianPublic)
async def get_technician(technician_id: uuid.UUID, session: DbSession) -> TechnicianPublic:
    return await TechnicianService(session).get_public(technician_id)


@router.get("/{technician_id}/reviews", response_model=list[ReviewPublic])
async def technician_reviews(
    technician_id: uuid.UUID, session: DbSession, limit: int = Query(default=50, ge=1, le=100)
) -> list[ReviewPublic]:
    return await ReviewService(session).list_for_technician(technician_id, limit=limit)
