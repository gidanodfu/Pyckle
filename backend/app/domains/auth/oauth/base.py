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

"""Abstracción de proveedores OAuth (independiente de Google)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.core.exceptions import AppError

# Codigos de error del flujo OAuth (fuente unica, no sensibles).
OAUTH_EMAIL_ALREADY_REGISTERED = "oauth_email_already_registered"
OAUTH_ONBOARDING_EXPIRED = "oauth_onboarding_expired"
OAUTH_ONBOARDING_INVALID = "oauth_onboarding_invalid"
OAUTH_EXCHANGE_EXPIRED = "oauth_exchange_expired"
OAUTH_EXCHANGE_INVALID = "oauth_exchange_invalid"
OAUTH_STATE_INVALID = "oauth_state_invalid"


class OAuthError(AppError):
    """Error controlado del flujo OAuth (nunca 500)."""

    status_code = 400
    code = "oauth_error"


@dataclass(slots=True)
class OAuthIdentity:
    """Identidad normalizada, sin detalles propios del proveedor."""

    provider: str
    provider_user_id: str
    email: str
    email_verified: bool
    name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    picture: str | None = None


class OAuthProvider(Protocol):
    name: str

    def authorization_url(self, *, state: str, nonce: str, code_challenge: str) -> str: ...

    async def exchange_code(self, *, code: str, code_verifier: str) -> dict[str, Any]: ...

    async def get_identity(self, tokens: dict[str, Any], *, nonce: str) -> OAuthIdentity: ...
