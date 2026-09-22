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

from app.core.dependencies import DbSession
from app.domains.admin.dependencies import AdminVerify
from app.domains.technicians.schemas import TechnicianPublic, TechnicianRead
from app.domains.technicians.service import TechnicianService
from app.schemas.common import Page

router = APIRouter()


@router.get("/technicians", response_model=Page[TechnicianPublic])
async def list_technicians(
    session: DbSession,
    _: AdminVerify,
    verified_only: bool = False,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Page[TechnicianPublic]:
    items, total, _, _ = await TechnicianService(session).list_public(
        verified_only=verified_only, limit=limit, offset=offset
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.patch("/technicians/{technician_id}/verify", response_model=TechnicianRead)
async def verify_technician(
    technician_id: uuid.UUID,
    session: DbSession,
    _: AdminVerify,
    verified: bool = True,
) -> TechnicianRead:
    return await TechnicianService(session).verify(technician_id, verified)
