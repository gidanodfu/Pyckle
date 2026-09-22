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

from fastapi import APIRouter

from app.core.dependencies import DbSession
from app.domains.admin.dependencies import AdminSpecialties
from app.domains.technicians.schemas import SpecialtyCreate, SpecialtyRead, SpecialtyUpdate
from app.domains.technicians.specialties import SpecialtyService
from app.schemas.common import Message

router = APIRouter()


@router.get("/specialties", response_model=list[SpecialtyRead])
async def list_specialties(session: DbSession, _: AdminSpecialties) -> list[SpecialtyRead]:
    return await SpecialtyService(session).list_all()


@router.post("/specialties", response_model=SpecialtyRead)
async def create_specialty(
    data: SpecialtyCreate, session: DbSession, _: AdminSpecialties
) -> SpecialtyRead:
    return await SpecialtyService(session).create(data)


@router.patch("/specialties/{specialty_id}", response_model=SpecialtyRead)
async def update_specialty(
    specialty_id: uuid.UUID,
    data: SpecialtyUpdate,
    session: DbSession,
    _: AdminSpecialties,
) -> SpecialtyRead:
    return await SpecialtyService(session).update(specialty_id, data)


@router.delete("/specialties/{specialty_id}", response_model=Message)
async def delete_specialty(
    specialty_id: uuid.UUID, session: DbSession, _: AdminSpecialties
) -> Message:
    await SpecialtyService(session).delete(specialty_id)
    return Message(detail="Especialidad eliminada")
