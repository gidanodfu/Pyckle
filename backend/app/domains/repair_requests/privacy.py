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

"""Reglas de visibilidad y privacidad de las solicitudes de reparación."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError
from app.domains.repair_requests.schemas import RepairRequestRead
from app.domains.technicians.repository import TechnicianRepository
from app.models.enums import PermissionCode, RequestStatus
from app.models.repair import RepairRequest
from app.models.user import User


class RepairRequestAccess:
    """Autorización de lectura y enmascarado de la dirección de servicio."""

    def __init__(self, session: AsyncSession) -> None:
        self.technicians = TechnicianRepository(session)

    @staticmethod
    def serialize(request: RepairRequest, *, can_see_address: bool) -> RepairRequestRead:
        read = RepairRequestRead.model_validate(request)
        if not can_see_address:
            read.address = None
        return read

    async def can_see_address(self, request: RepairRequest, user: User) -> bool:
        """Dirección de servicio: dueño, administrador o técnico asignado."""
        if request.customer_id == user.id:
            return True
        if PermissionCode.REPAIR_REQUEST_MODERATE in user.permission_codes:
            return True
        technician = await self.technicians.get_by_user_id(user.id)
        return technician is not None and request.assigned_technician_id == technician.id

    async def assert_can_view(self, request: RepairRequest, user: User) -> None:
        if request.customer_id == user.id:
            return
        if PermissionCode.REPAIR_REQUEST_MODERATE in user.permission_codes:
            return
        technician = await self.technicians.get_by_user_id(user.id)
        if technician is not None:
            if request.assigned_technician_id == technician.id:
                return
            if request.status in {RequestStatus.OPEN, RequestStatus.QUOTED}:
                return
        raise ForbiddenError("No tienes acceso a esta solicitud")
