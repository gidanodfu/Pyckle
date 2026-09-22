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

import ipaddress
import uuid
from typing import Annotated

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import UnauthorizedError
from app.core.security import ACCESS_TOKEN_TYPE, decode_token
from app.db.session import get_db
from app.domains.users.repository import UserRepository
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db)]


def _subject_uuid(payload: dict) -> uuid.UUID | None:
    try:
        return uuid.UUID(payload["sub"])
    except (KeyError, TypeError, ValueError):
        return None


def _is_revoked(payload: dict, user: User) -> bool:
    """El claim ``tv`` debe coincidir con el epoch del usuario.

    Cambiar la contraseña incrementa ``User.token_version`` y deja fuera tanto
    access como refresh tokens emitidos antes del cambio. Los tokens previos a
    esta columna no traen ``tv`` y se tratan como versión 0.
    """
    return int(payload.get("tv", 0)) != user.token_version


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: DbSession,
) -> User:
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Token de acceso requerido")
    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Token inválido o expirado") from exc
    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise UnauthorizedError("Tipo de token inválido")
    subject = _subject_uuid(payload)
    if subject is None:
        raise UnauthorizedError("Token inválido o expirado")
    user = await UserRepository(session).get_with_roles(subject)
    if user is None:
        raise UnauthorizedError("Usuario no encontrado")
    if not user.is_active:
        raise UnauthorizedError("La cuenta está desactivada")
    if _is_revoked(payload, user):
        raise UnauthorizedError("Token inválido o expirado")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_optional_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: DbSession,
) -> User | None:
    if credentials is None or not credentials.credentials:
        return None
    try:
        payload = decode_token(credentials.credentials)
    except jwt.PyJWTError:
        return None
    if payload.get("type") != ACCESS_TOKEN_TYPE:
        return None
    subject = _subject_uuid(payload)
    if subject is None:
        return None
    user = await UserRepository(session).get_with_roles(subject)
    if user is None or not user.is_active or _is_revoked(payload, user):
        return None
    return user


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


def _is_trusted_proxy(request: Request) -> bool:
    proxies = get_settings().trusted_proxies_list
    peer = request.client.host if request.client else None
    if not proxies or not peer:
        return False
    try:
        address = ipaddress.ip_address(peer)
    except ValueError:
        return False
    for entry in proxies:
        try:
            if address in ipaddress.ip_network(entry, strict=False):
                return True
        except ValueError:
            continue
    return False


def client_ip(request: Request) -> str:
    """IP real del cliente detrás de un proxy de confianza.

    ``X-Real-IP`` solo se acepta cuando la conexión directa proviene de un
    proxy incluido en ``TRUSTED_PROXIES`` (Nginx). Fuera de ese rango el header
    es ignorado y se usa la IP del peer, de modo que un cliente que alcance el
    backend directamente no pueda falsificar la identidad del rate limit.
    ``X-Forwarded-For`` nunca se usa: un cliente puede enviarlo arbitrariamente.
    """
    if _is_trusted_proxy(request):
        real = request.headers.get("x-real-ip")
        if real:
            return real.strip()
    return request.client.host if request.client else "unknown"


async def get_user_from_token(token: str, session: AsyncSession) -> User | None:
    try:
        payload = decode_token(token)
    except jwt.PyJWTError:
        return None
    if payload.get("type") != ACCESS_TOKEN_TYPE:
        return None
    subject = _subject_uuid(payload)
    if subject is None:
        return None
    user = await UserRepository(session).get_with_roles(subject)
    if user is None or not user.is_active or _is_revoked(payload, user):
        return None
    return user
