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

from fastapi import APIRouter

from app.core.dependencies import DbSession
from app.domains.technicians.schemas import SpecialtyRead
from app.domains.technicians.specialties import SpecialtyService

router = APIRouter(prefix="/specialties", tags=["specialties"])


@router.get("", response_model=list[SpecialtyRead])
async def list_specialties(session: DbSession) -> list[SpecialtyRead]:
    return await SpecialtyService(session).list_active()
