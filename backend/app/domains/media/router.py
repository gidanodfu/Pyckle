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

from fastapi import APIRouter, Query, Response

from app.core.dependencies import DbSession
from app.core.exceptions import UnauthorizedError
from app.core.paths import verify_media_signature
from app.domains.media.service import MediaService

router = APIRouter(prefix="/media", tags=["media"])


@router.get("/{storage_key:path}")
async def get_media(
    storage_key: str,
    session: DbSession,
    e: str = Query(default=""),
    s: str = Query(default=""),
) -> Response:
    if not verify_media_signature(storage_key, e, s):
        raise UnauthorizedError("Enlace de imagen inválido o expirado")
    data, content_type = await MediaService(session).fetch(storage_key)
    return Response(
        content=data,
        media_type=content_type,
        headers={"Cache-Control": "private, max-age=300, must-revalidate"},
    )
