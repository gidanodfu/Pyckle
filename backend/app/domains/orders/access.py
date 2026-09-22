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

"""Autorización compartida sobre órdenes/reparaciones."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError
from app.domains.technicians.repository import TechnicianRepository
from app.models.enums import PermissionCode
from app.models.order import Order
from app.models.user import User


class OrderAccess:
    def __init__(self, session: AsyncSession) -> None:
        self.technicians = TechnicianRepository(session)

    @staticmethod
    def is_admin(user: User) -> bool:
        return bool(
            user.permission_codes.intersection(
                {PermissionCode.ORDER_READ_ALL, PermissionCode.ADMIN_ORDERS}
            )
        )

    async def is_assigned(self, order: Order, user: User) -> bool:
        technician = await self.technicians.get_by_user_id(user.id)
        return technician is not None and order.technician_id == technician.id

    async def assert_can_view(self, order: Order, user: User) -> None:
        if order.customer_id == user.id or self.is_admin(user):
            return
        if await self.is_assigned(order, user):
            return
        raise ForbiddenError("No tienes acceso a esta orden")

    async def can_see_address(self, order: Order, user: User) -> bool:
        if order.customer_id == user.id or self.is_admin(user):
            return True
        return await self.is_assigned(order, user)

    async def assert_manage(self, order: Order, user: User) -> None:
        """Solo el técnico asignado gestiona el proceso técnico.

        El administrador es un actor de supervisión de SOLO LECTURA sobre las
        órdenes: puede verlas todas (``is_admin``) pero nunca mutarlas, ni
        siquiera con permisos como ``admin:orders`` o ``order:read_all``.
        """
        if await self.is_assigned(order, user):
            return
        raise ForbiddenError("No puedes gestionar esta reparación")
