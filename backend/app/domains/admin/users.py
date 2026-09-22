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

from fastapi import APIRouter, Query

from app.core.dependencies import DbSession
from app.domains.admin.dependencies import AdminRoles, AdminUsers
from app.domains.users.schemas import AdminUserUpdate, PermissionRead, RoleRead, UserRead
from app.domains.users.service import UserService
from app.schemas.common import Message, Page

router = APIRouter()


@router.get("/users", response_model=Page[UserRead])
async def list_users(
    session: DbSession,
    _: AdminUsers,
    role: str | None = None,
    search: str | None = None,
    is_active: bool | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> Page[UserRead]:
    items, total = await UserService(session).admin_list(
        role=role, search=search, is_active=is_active, limit=limit, offset=offset
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.patch("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID, data: AdminUserUpdate, session: DbSession, _: AdminUsers
) -> UserRead:
    return await UserService(session).admin_update(user_id, data)


@router.delete("/users/{user_id}", response_model=Message)
async def delete_user(user_id: uuid.UUID, current_user: AdminUsers, session: DbSession) -> Message:
    await UserService(session).admin_delete(user_id, current_user.id)
    return Message(detail="Usuario eliminado")


@router.get("/roles", response_model=list[RoleRead])
async def list_roles(session: DbSession, _: AdminRoles) -> list[RoleRead]:
    return await UserService(session).list_roles()


@router.get("/permissions", response_model=list[PermissionRead])
async def list_permissions(session: DbSession, _: AdminRoles) -> list[PermissionRead]:
    return await UserService(session).list_permissions()
