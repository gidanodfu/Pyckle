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
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base


class BaseRepository[ModelT: Base]:
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, entity_id: uuid.UUID) -> ModelT | None:
        return await self.session.get(self.model, entity_id)

    async def add(self, entity: ModelT) -> ModelT:
        """Persiste y devuelve la entidad con los valores generados por el servidor.

        ``flush`` envía el INSERT para obtener la PK y ``refresh`` recarga los
        defaults calculados en BD; ambos dentro de la transacción abierta.
        """
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: ModelT) -> None:
        await self.session.delete(entity)
        await self.session.flush()

    async def list_all(self, *where: Any, limit: int = 100, offset: int = 0) -> list[ModelT]:
        stmt = select(self.model).where(*where).limit(limit).offset(offset)
        return list((await self.session.execute(stmt)).scalars().all())

    async def count(self, *where: Any) -> int:
        stmt = select(func.count()).select_from(self.model).where(*where)
        return int((await self.session.execute(stmt)).scalar_one())
