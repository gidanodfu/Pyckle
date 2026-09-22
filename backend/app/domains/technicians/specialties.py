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

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.text import slugify
from app.domains.technicians.repository import SpecialtyRepository
from app.domains.technicians.schemas import SpecialtyCreate, SpecialtyRead, SpecialtyUpdate


class SpecialtyService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = SpecialtyRepository(session)

    async def list_active(self) -> list[SpecialtyRead]:
        specialties = await self.repo.list_active()
        return [SpecialtyRead.model_validate(s) for s in specialties]

    async def list_all(self) -> list[SpecialtyRead]:
        specialties = await self.repo.list_all(limit=500)
        return [SpecialtyRead.model_validate(s) for s in specialties]

    async def create(self, data: SpecialtyCreate) -> SpecialtyRead:
        slug = slugify(data.name)
        if await self.repo.get_by_slug(slug):
            raise ConflictError("La especialidad ya existe")
        specialty = await self.repo.add(
            self.repo.model(
                name=data.name, slug=slug, description=data.description, is_active=data.is_active
            )
        )
        await self.session.commit()
        return SpecialtyRead.model_validate(specialty)

    async def update(self, specialty_id: uuid.UUID, data: SpecialtyUpdate) -> SpecialtyRead:
        specialty = await self.repo.get(specialty_id)
        if specialty is None:
            raise NotFoundError("Especialidad no encontrada")
        payload = data.model_dump(exclude_unset=True)
        if "name" in payload:
            specialty.slug = slugify(payload["name"])
        for field, value in payload.items():
            setattr(specialty, field, value)
        await self.session.commit()
        return SpecialtyRead.model_validate(specialty)

    async def delete(self, specialty_id: uuid.UUID) -> None:
        specialty = await self.repo.get(specialty_id)
        if specialty is None:
            raise NotFoundError("Especialidad no encontrada")
        # Una especialidad en uso no se elimina: el borrado pondría en NULL la
        # especialidad de solicitudes existentes y desactivaría la validación de
        # cotización por especialidad. Se desactiva en su lugar.
        if await self.repo.is_in_use(specialty_id):
            raise ConflictError(
                "La especialidad está en uso por técnicos o solicitudes; "
                "desactívala en lugar de eliminarla"
            )
        await self.repo.delete(specialty)
        await self.session.commit()
