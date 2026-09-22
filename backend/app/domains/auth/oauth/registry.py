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

"""Registro de proveedores OAuth soportados."""

from __future__ import annotations

from app.domains.auth.oauth.base import OAuthError, OAuthProvider
from app.domains.auth.oauth.google import GoogleOAuthProvider

_PROVIDERS: dict[str, OAuthProvider] = {}


def get_provider(name: str) -> OAuthProvider:
    if name not in _PROVIDERS:
        if name == "google":
            _PROVIDERS[name] = GoogleOAuthProvider()
        else:
            raise OAuthError(f"Proveedor OAuth no soportado: {name}")
    return _PROVIDERS[name]
