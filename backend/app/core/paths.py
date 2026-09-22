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

"""Constructores centralizados de paths/URLs internas de Pyckle."""

from __future__ import annotations

import hashlib
import hmac
import time
from urllib.parse import quote

from app.core.config import get_settings

settings = get_settings()

MEDIA_URL_TTL_SECONDS = 300


def api_path(path: str) -> str:
    """Prefija una ruta con la versión de la API."""
    return f"{settings.api_v1_prefix}/{path.lstrip('/')}"


def order_report_path(order_id: object) -> str:
    """Ruta del informe PDF de una reparación (fuente única del path)."""
    return api_path(f"orders/{order_id}/report")


def _media_signature(storage_key: str, expires: int) -> str:
    message = f"{storage_key}:{expires}".encode()
    return hmac.new(settings.secret_key.encode(), message, hashlib.sha256).hexdigest()


def sign_media_url(storage_key: str, ttl: int = MEDIA_URL_TTL_SECONDS) -> str:
    """URL relativa firmada y temporal de una imagen servida por Pyckle.

    La imagen no es accesible solo con conocer ``storage_key``: el backend exige
    una firma válida y vigente generada al serializar el recurso autorizado.
    """
    expires = int(time.time()) + ttl
    signature = _media_signature(storage_key, expires)
    return (
        f"{settings.api_v1_prefix}/media/{quote(storage_key, safe='/')}?e={expires}&s={signature}"
    )


def verify_media_signature(storage_key: str, expires: str, signature: str) -> bool:
    try:
        expires_int = int(expires)
    except (TypeError, ValueError):
        return False
    if expires_int < int(time.time()):
        return False
    expected = _media_signature(storage_key, expires_int)
    return hmac.compare_digest(expected, signature or "")
