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

"""Helpers del seed demo (logica reutilizable)."""

from __future__ import annotations

from sqlalchemy import select

from app.models.geo import Department, District


async def district_by_code(session, code: str) -> District:
    district = (
        await session.execute(select(District).where(District.code == code))
    ).scalar_one_or_none()
    if district is None:
        raise RuntimeError(f"Distrito de ubigeo no encontrado: {code}")
    return district


async def _location_context(session, district: District) -> dict:
    department = await session.get(Department, district.department_id)
    return {
        "department_id": district.department_id,
        "province_id": district.province_id,
        "district_id": district.id,
        "district": district.name,
        "city": department.name,
        "address": None,
    }
