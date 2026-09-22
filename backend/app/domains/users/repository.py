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

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.infrastructure.repository import BaseRepository
from app.models.user import Permission, Role, User


class UserRepository(BaseRepository[User]):
    model = User

    def _with_roles(self):
        return select(User).options(selectinload(User.roles).selectinload(Role.permissions))

    async def get_by_email(self, email: str) -> User | None:
        stmt = self._with_roles().where(func.lower(User.email) == email.lower())
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_by_phone(self, phone_normalized: str) -> User | None:
        stmt = self._with_roles().where(User.phone_normalized == phone_normalized)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_with_roles(self, user_id: uuid.UUID) -> User | None:
        stmt = self._with_roles().where(User.id == user_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def get_me(self, user_id: uuid.UUID) -> User | None:
        from app.models.customer import CustomerProfile

        stmt = (
            self._with_roles()
            .options(
                selectinload(User.customer_profile).selectinload(CustomerProfile.department),
                selectinload(User.customer_profile).selectinload(CustomerProfile.province),
                selectinload(User.customer_profile).selectinload(CustomerProfile.district_geo),
                selectinload(User.technician_profile),
            )
            .where(User.id == user_id)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_paginated(
        self,
        *,
        role: str | None = None,
        search: str | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[User], int]:
        stmt = self._with_roles()
        count_stmt = select(func.count(func.distinct(User.id))).select_from(User)
        conditions = []
        if search:
            like = f"%{search.lower()}%"
            conditions.append(
                or_(func.lower(User.email).like(like), func.lower(User.full_name).like(like))
            )
        if is_active is not None:
            conditions.append(User.is_active.is_(is_active))
        if role:
            stmt = stmt.join(User.roles).where(Role.name == role)
            count_stmt = count_stmt.join(User.roles).where(Role.name == role)
        if conditions:
            stmt = stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)
        stmt = stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)
        users = list((await self.session.execute(stmt)).scalars().unique().all())
        total = int((await self.session.execute(count_stmt)).scalar_one())
        return users, total

    async def count_by_role(self, role_name: str) -> int:
        stmt = (
            select(func.count(func.distinct(User.id)))
            .select_from(User)
            .join(User.roles)
            .where(Role.name == role_name)
        )
        return int((await self.session.execute(stmt)).scalar_one())


class RoleRepository(BaseRepository[Role]):
    model = Role

    async def get_by_name(self, name: str) -> Role | None:
        stmt = select(Role).options(selectinload(Role.permissions)).where(Role.name == name)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_all_ordered(self) -> list[Role]:
        stmt = select(Role).options(selectinload(Role.permissions)).order_by(Role.name)
        return list((await self.session.execute(stmt)).scalars().all())


class PermissionRepository(BaseRepository[Permission]):
    model = Permission

    async def list_all_ordered(self) -> list[Permission]:
        stmt = select(Permission).order_by(Permission.code)
        return list((await self.session.execute(stmt)).scalars().all())
