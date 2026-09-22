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

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.domains.users.schemas import (
    ChangePasswordRequest,
    CustomerProfileRead,
    CustomerProfileUpdate,
    MeRead,
    UserRead,
    UserUpdate,
)
from app.domains.users.service import UserService
from app.schemas.common import Message

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=MeRead)
async def get_me(current_user: CurrentUser, session: DbSession) -> MeRead:
    return await UserService(session).get_me(current_user.id)


@router.patch("/me", response_model=UserRead)
async def update_me(data: UserUpdate, current_user: CurrentUser, session: DbSession) -> UserRead:
    return await UserService(session).update_me(current_user.id, data)


@router.post("/me/change-password", response_model=Message)
async def change_password(
    data: ChangePasswordRequest, current_user: CurrentUser, session: DbSession
) -> Message:
    await UserService(session).change_password(
        current_user.id, data.current_password, data.new_password
    )
    return Message(detail="Contraseña actualizada")


@router.patch("/me/customer-profile", response_model=CustomerProfileRead)
async def update_customer_profile(
    data: CustomerProfileUpdate, current_user: CurrentUser, session: DbSession
) -> CustomerProfileRead:
    return await UserService(session).update_customer_profile(current_user.id, data)
