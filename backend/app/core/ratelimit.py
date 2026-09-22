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

"""Rate limit de ventana fija con reservas atómicas en Redis.

Regla común: hasta ``max_attempts`` reservas por ventana; al superar el máximo
se escribe una clave de bloqueo con TTL. El identificador debe derivarse de
datos que el cliente no pueda variar para esquivar el límite (en particular la
IP confiable, nunca un valor del cuerpo de la petición).

Políticas:
- Login: ``email + IP`` (hash), para no permitir enumeración de usuarios ni
  bloqueos dirigidos de una cuenta desde otra IP.
- Registro: solo ``IP`` confiable. El email no sirve como principal porque un
  atacante puede variarlo en cada intento; la IP es lo que realmente acota el
  abuso de Argon2 y de escrituras. Es independiente del TTL de onboarding OAuth:
  aquél acota la ventana para completar un registro ya iniciado con Google.
"""

from __future__ import annotations

import hashlib

from app.core.config import get_settings
from app.core.exceptions import TooManyRequestsError
from app.core.redis import get_redis

settings = get_settings()


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:40]


def login_identifier(email: str, client_ip: str) -> str:
    return _digest(f"{email.strip().lower()}|{client_ip}")


def registration_identifier(client_ip: str) -> str:
    return _digest(client_ip.strip().lower())


class WindowRateLimiter:
    """Ventana fija con reserva atómica de intentos en Redis.

    ``reserve`` ejecuta ``INCR`` + ``EXPIRE ... NX`` en una única transacción,
    de modo que N peticiones concurrentes reciben valores distintos y solo
    ``max_attempts`` pueden continuar. Esto elimina el check-then-act que
    permitía superar el límite con una ráfaga.
    """

    def __init__(self, *, prefix: str, max_attempts: int, block_seconds: int) -> None:
        self.prefix = prefix
        self.max_attempts = max_attempts
        self.block_seconds = block_seconds

    def _attempts_key(self, identifier: str) -> str:
        return f"{self.prefix}:attempts:{identifier}"

    def _blocked_key(self, identifier: str) -> str:
        return f"{self.prefix}:blocked:{identifier}"

    @property
    def blocked_message(self) -> str:
        minutes = max(1, round(self.block_seconds / 60))
        return (
            "Demasiados intentos. "
            f"Intenta nuevamente en {minutes} minuto{'s' if minutes != 1 else ''}."
        )

    async def reserve(self, identifier: str) -> int:
        redis = get_redis()
        attempts_key = self._attempts_key(identifier)
        async with redis.pipeline(transaction=True) as pipe:
            pipe.incr(attempts_key)
            # El TTL se fija únicamente en el primer incremento de la ventana.
            pipe.expire(attempts_key, self.block_seconds, nx=True)
            results = await pipe.execute()
        attempts = int(results[0])
        if attempts > self.max_attempts:
            await redis.setex(self._blocked_key(identifier), self.block_seconds, "1")
            raise TooManyRequestsError(self.blocked_message)
        return attempts

    async def reset(self, identifier: str) -> None:
        redis = get_redis()
        await redis.delete(self._attempts_key(identifier), self._blocked_key(identifier))


class LoginRateLimiter(WindowRateLimiter):
    def __init__(
        self,
        *,
        max_attempts: int | None = None,
        block_seconds: int | None = None,
    ) -> None:
        super().__init__(
            prefix="login",
            max_attempts=max_attempts or settings.login_max_attempts,
            block_seconds=block_seconds or settings.login_block_seconds,
        )

    @property
    def blocked_message(self) -> str:
        minutes = max(1, round(self.block_seconds / 60))
        return (
            "Demasiados intentos fallidos. "
            f"Intenta nuevamente en {minutes} minuto{'s' if minutes != 1 else ''}."
        )


class RegistrationRateLimiter(WindowRateLimiter):
    """Protege el alta de cuentas (Argon2 + escrituras) contra abuso por IP."""

    def __init__(
        self,
        *,
        max_attempts: int | None = None,
        block_seconds: int | None = None,
    ) -> None:
        super().__init__(
            prefix="register",
            max_attempts=max_attempts or settings.register_max_per_ip,
            block_seconds=block_seconds or settings.register_window_seconds,
        )

    @property
    def blocked_message(self) -> str:
        minutes = max(1, round(self.block_seconds / 60))
        return (
            "Demasiados registros desde tu conexión. "
            f"Intenta nuevamente en {minutes} minuto{'s' if minutes != 1 else ''}."
        )
