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

"""Repositorio de cuentas OAuth vinculadas."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select

from app.infrastructure.repository import BaseRepository
from app.models.oauth import OAuthAccount


class OAuthAccountRepository(BaseRepository[OAuthAccount]):
    model = OAuthAccount

    async def get_by_provider_user(
        self, provider: str, provider_user_id: str
    ) -> OAuthAccount | None:
        stmt = select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_user_id == provider_user_id,
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def count_for_user(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count(OAuthAccount.id)).where(OAuthAccount.user_id == user_id)
        return int((await self.session.execute(stmt)).scalar_one())
