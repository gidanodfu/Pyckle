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

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUser, DbSession
from app.domains.reviews.schemas import ReviewCreate, ReviewPublic, ReviewRead
from app.domains.reviews.service import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
    data: ReviewCreate, current_user: CurrentUser, session: DbSession
) -> ReviewRead:
    return await ReviewService(session).create(current_user, data)


@router.get("/technician/{technician_id}", response_model=list[ReviewPublic])
async def list_reviews(
    technician_id: uuid.UUID,
    session: DbSession,
    limit: int = Query(default=50, ge=1, le=100),
) -> list[ReviewRead]:
    return await ReviewService(session).list_for_technician(technician_id, limit=limit)
