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
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.core.config import get_settings

settings = get_settings()
_hasher = PasswordHasher()

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed: str) -> bool:
    try:
        return _hasher.check_needs_rehash(hashed)
    except (InvalidHashError, VerificationError):
        return False


def create_access_token(
    subject: str, extra: dict[str, Any] | None = None, token_version: int = 0
) -> tuple[str, datetime]:
    """Genera un access token de vida corta (claim ``type=access``).

    Incluye ``jti`` y ``tv``; este último es el epoch de revocación por
    usuario y permite invalidar de golpe los access tokens vigentes cuando
    cambia la contraseña.
    """
    now = datetime.now(UTC)
    expires = now + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": ACCESS_TOKEN_TYPE,
        "iat": now,
        "exp": expires,
        "jti": str(uuid.uuid4()),
        # Epoch de revocación por usuario (ver User.token_version).
        "tv": token_version,
    }
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, expires


def create_refresh_token(
    subject: str, version: int = 0, token_version: int = 0
) -> tuple[str, datetime, str]:
    """Genera un refresh token rotativo de un solo uso.

    ``jti`` es la clave que se consume atómicamente al renovar, ``ver`` el
    epoch de revocación en Redis y ``tv`` replica el epoch por usuario.
    """
    now = datetime.now(UTC)
    expires = now + timedelta(days=settings.refresh_token_expire_days)
    jti = str(uuid.uuid4())
    payload: dict[str, Any] = {
        "sub": subject,
        "type": REFRESH_TOKEN_TYPE,
        "iat": now,
        "exp": expires,
        "jti": jti,
        # Epoch de revocación: al cambiar la contraseña se incrementa y todos
        # los refresh tokens con una versión anterior dejan de ser aceptados.
        "ver": version,
        "tv": token_version,
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, expires, jti


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
