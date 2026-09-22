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

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.domains.repair_requests.repository import RepairRequestImageRepository
from app.infrastructure.storage import StorageBackend, build_storage


class MediaService:
    """Sirve imagenes registradas en Pyckle desde el backend de almacenamiento."""

    def __init__(self, session: AsyncSession, storage: StorageBackend | None = None) -> None:
        self.session = session
        self.images = RepairRequestImageRepository(session)
        self.storage = storage or build_storage()

    async def fetch(self, storage_key: str) -> tuple[bytes, str]:
        # Defensa adicional (además del confinamiento del storage): se rechazan
        # claves con separadores o segmentos relativos antes de consultarlas.
        if (
            not storage_key
            or storage_key.startswith("/")
            or storage_key.startswith(".")
            or ".." in storage_key
            or "\\" in storage_key
        ):
            raise BadRequestError("Ruta de imagen inválida")
        image = await self.images.get_by_storage_key(storage_key)
        if image is None:
            raise NotFoundError("Imagen no encontrada")
        data = await self.storage.get(image.storage_key)
        return data, image.content_type
