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

from typing import Annotated

from fastapi import Depends

from app.models.enums import PermissionCode
from app.models.user import User
from app.permissions.rbac import require_permissions

AdminUsers = Annotated[User, Depends(require_permissions(PermissionCode.ADMIN_USERS))]
AdminRoles = Annotated[User, Depends(require_permissions(PermissionCode.ADMIN_ROLES))]
AdminReports = Annotated[User, Depends(require_permissions(PermissionCode.ADMIN_REPORTS))]
AdminOrders = Annotated[User, Depends(require_permissions(PermissionCode.ADMIN_ORDERS))]
AdminSpecialties = Annotated[User, Depends(require_permissions(PermissionCode.ADMIN_SPECIALTIES))]
AdminVerify = Annotated[User, Depends(require_permissions(PermissionCode.ADMIN_TECHNICIANS_VERIFY))]
Moderate = Annotated[User, Depends(require_permissions(PermissionCode.REPAIR_REQUEST_MODERATE))]
