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

"""Gestión de imágenes de las solicitudes de reparación."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import BadRequestError
from app.domains.repair_requests.repository import RepairRequestRepository
from app.infrastructure.storage import StorageBackend, build_storage, validate_image
from app.models.repair import RepairRequest, RepairRequestImage

settings = get_settings()


class RepairRequestMediaService:
    def __init__(
        self,
        session: AsyncSession,
        storage: StorageBackend | None = None,
        repo: RepairRequestRepository | None = None,
    ) -> None:
        self.session = session
        self.repo = repo or RepairRequestRepository(session)
        self.storage = storage or build_storage()

    async def add_image(self, request: RepairRequest, data: bytes, content_type: str) -> None:
        validate_image(data, content_type, settings)
        if await self.repo.count_images(request.id) >= settings.max_images_per_request:
            raise BadRequestError(
                f"Máximo {settings.max_images_per_request} imágenes por solicitud"
            )
        stored = await self.storage.save(
            data=data, content_type=content_type, folder=f"requests/{request.id}"
        )
        request.images.append(
            RepairRequestImage(
                storage_key=stored.storage_key,
                content_type=content_type,
                size_bytes=len(data),
            )
        )
        try:
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            try:
                await self.storage.delete(stored.storage_key)
            except Exception:  # noqa: BLE001 - limpieza best-effort
                pass
            raise

    async def delete_images(self, request: RepairRequest) -> None:
        for image in request.images:
            await self.storage.delete(image.storage_key)
