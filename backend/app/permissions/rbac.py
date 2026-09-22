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

from collections.abc import Callable
from typing import Any

from app.core.dependencies import CurrentUser
from app.core.exceptions import ForbiddenError


def require_permissions(*codes: str) -> Callable[..., Any]:
    async def dependency(current_user: CurrentUser) -> Any:
        missing = [code for code in codes if code not in current_user.permission_codes]
        if missing:
            raise ForbiddenError(f"Permisos requeridos: {', '.join(missing)}")
        return current_user

    return dependency


def require_roles(*roles: str) -> Callable[..., Any]:
    async def dependency(current_user: CurrentUser) -> Any:
        if not current_user.role_names.intersection(roles):
            raise ForbiddenError(f"Roles requeridos: {', '.join(roles)}")
        return current_user

    return dependency
