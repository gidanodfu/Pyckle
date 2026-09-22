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

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.domains.geo.repository import GeoRepository
from app.domains.geo.service import GeoService
from app.domains.repair_requests.media import RepairRequestMediaService
from app.domains.repair_requests.privacy import RepairRequestAccess
from app.domains.repair_requests.repository import RepairRequestRepository
from app.domains.repair_requests.schemas import (
    RepairRequestCreate,
    RepairRequestRead,
    RepairRequestUpdate,
)
from app.domains.technicians.repository import SpecialtyRepository, TechnicianRepository
from app.domains.users.repository import UserRepository
from app.infrastructure.storage import StorageBackend, build_storage
from app.models.customer import CustomerProfile
from app.models.enums import Modality, RequestStatus
from app.models.repair import RepairRequest
from app.models.user import User

EDITABLE_STATUSES = {RequestStatus.OPEN, RequestStatus.QUOTED}


class RepairRequestService:
    def __init__(self, session: AsyncSession, storage: StorageBackend | None = None) -> None:
        self.session = session
        self.repo = RepairRequestRepository(session)
        self.specialties = SpecialtyRepository(session)
        self.technicians = TechnicianRepository(session)
        self.users = UserRepository(session)
        self.geo = GeoService(session)
        self.geo_repo = GeoRepository(session)
        self.storage = storage or build_storage()
        self.access = RepairRequestAccess(session)
        self.media = RepairRequestMediaService(session, self.storage, self.repo)

    async def create(self, customer: User, data: RepairRequestCreate) -> RepairRequestRead:
        if data.specialty_id and await self.specialties.get(data.specialty_id) is None:
            raise BadRequestError("Especialidad inexistente")
        if data.budget_min is not None and data.budget_max is not None:
            if data.budget_min > data.budget_max:
                raise BadRequestError("El presupuesto mínimo no puede superar al máximo")

        profile = await self._customer_profile(customer.id)
        district = await self._resolve_location(
            data.department_id, data.province_id, data.district_id, profile
        )
        address = data.address or (profile.address if profile else None)
        if data.modality == Modality.HOME and not address:
            raise BadRequestError("Las solicitudes a domicilio requieren una dirección")

        request = RepairRequest(
            customer_id=customer.id,
            title=data.title,
            description=data.description,
            specialty_id=data.specialty_id,
            modality=data.modality,
            address=address,
            district=district.name if district else None,
            city=district.department.name if district else "Lima",
            department_id=district.department_id if district else None,
            province_id=district.province_id if district else None,
            district_id=district.id if district else None,
            budget_min=data.budget_min,
            budget_max=data.budget_max,
            preferred_date=data.preferred_date,
        )
        await self.repo.add(request)
        await self.session.commit()
        return await self._read(request.id, customer)

    async def list_for_customer(
        self,
        customer_id: uuid.UUID,
        *,
        status: RequestStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[RepairRequestRead], int]:
        items, total = await self.repo.list_for_customer(
            customer_id, status=status, limit=limit, offset=offset
        )
        return [self.access.serialize(item, can_see_address=True) for item in items], total

    async def list_available(
        self, user: User, *, limit: int = 50, offset: int = 0
    ) -> tuple[list[RepairRequestRead], int, str, bool]:
        technician = await self.technicians.get_by_user_id(user.id)
        if technician is None:
            raise ForbiddenError("El usuario no tiene perfil de técnico")
        specialty_ids = [s.id for s in technician.specialties]

        levels: list[tuple[str, dict]] = []
        if technician.district_id is not None:
            levels.append(("district", {"district_id": technician.district_id}))
        if technician.province_id is not None:
            levels.append(("province", {"province_id": technician.province_id}))
        if technician.department_id is not None:
            levels.append(("department", {"department_id": technician.department_id}))

        if not levels:
            items, total = await self.repo.list_available(
                specialty_ids=specialty_ids, customer_id=user.id, limit=limit, offset=offset
            )
            masked = [self.access.serialize(i, can_see_address=False) for i in items]
            return masked, total, "all", False

        for index, (scope, filters) in enumerate(levels):
            items, total = await self.repo.list_available(
                specialty_ids=specialty_ids,
                customer_id=user.id,
                limit=limit,
                offset=offset,
                **filters,
            )
            if total > 0:
                return (
                    [self.access.serialize(i, can_see_address=False) for i in items],
                    total,
                    scope,
                    index > 0,
                )
        return [], 0, levels[-1][0], len(levels) > 1

    async def list_all(
        self, *, status: RequestStatus | None = None, limit: int = 50, offset: int = 0
    ) -> tuple[list[RepairRequestRead], int]:
        items, total = await self.repo.list_all(status=status, limit=limit, offset=offset)
        return [self.access.serialize(item, can_see_address=True) for item in items], total

    async def get_for_user(self, request_id: uuid.UUID, user: User) -> RepairRequestRead:
        request = await self._get_or_404(request_id)
        await self.access.assert_can_view(request, user)
        can_see = await self.access.can_see_address(request, user)
        return self.access.serialize(request, can_see_address=can_see)

    async def update(
        self, request_id: uuid.UUID, user: User, data: RepairRequestUpdate
    ) -> RepairRequestRead:
        request = await self._get_or_404(request_id)
        self._assert_owner(request, user)
        if request.status not in EDITABLE_STATUSES:
            raise BadRequestError("La solicitud ya no se puede editar")
        payload = data.model_dump(exclude_unset=True)
        if (
            payload.get("specialty_id")
            and await self.specialties.get(payload["specialty_id"]) is None
        ):
            raise BadRequestError("Especialidad inexistente")
        if any(
            payload.get(field) is not None
            for field in ("department_id", "province_id", "district_id")
        ):
            district = await self.geo.resolve(
                payload.get("department_id"),
                payload.get("province_id"),
                payload.get("district_id"),
            )
            request.department_id = district.department_id
            request.province_id = district.province_id
            request.district_id = district.id
            request.district = district.name
            request.city = district.department.name
        for field in ("department_id", "province_id", "district_id"):
            payload.pop(field, None)
        for field, value in payload.items():
            setattr(request, field, value)
        if (
            request.budget_min is not None
            and request.budget_max is not None
            and request.budget_min > request.budget_max
        ):
            raise BadRequestError("El presupuesto mínimo no puede superar al máximo")
        if request.modality == Modality.HOME and not (request.address or "").strip():
            raise BadRequestError("Las solicitudes a domicilio requieren una dirección")
        await self.session.commit()
        return await self._read(request_id, user)

    async def cancel(self, request_id: uuid.UUID, user: User) -> RepairRequestRead:
        request = await self._get_or_404(request_id)
        self._assert_owner(request, user)
        if request.status in {RequestStatus.COMPLETED, RequestStatus.CANCELLED}:
            raise BadRequestError("La solicitud no se puede cancelar")
        request.status = RequestStatus.CANCELLED
        await self.session.commit()
        return await self._read(request_id, user)

    async def add_image(
        self, request_id: uuid.UUID, user: User, data: bytes, content_type: str
    ) -> RepairRequestRead:
        request = await self._get_or_404(request_id)
        self._assert_owner(request, user)
        if request.status not in EDITABLE_STATUSES:
            raise BadRequestError("La solicitud ya no admite imágenes")
        await self.media.add_image(request, data, content_type)
        return await self._read(request_id, user)

    async def admin_delete(self, request_id: uuid.UUID) -> None:
        request = await self._get_or_404(request_id)
        await self.media.delete_images(request)
        await self.repo.delete(request)
        await self.session.commit()

    async def _customer_profile(self, user_id: uuid.UUID) -> CustomerProfile | None:
        user = await self.users.get_me(user_id)
        return user.customer_profile if user else None

    async def _resolve_location(
        self,
        department_id: uuid.UUID | None,
        province_id: uuid.UUID | None,
        district_id: uuid.UUID | None,
        profile: CustomerProfile | None,
    ):
        if any(item is not None for item in (department_id, province_id, district_id)):
            return await self.geo.resolve(department_id, province_id, district_id)
        if profile is not None and profile.district_id is not None:
            return await self.geo_repo.get_district(profile.district_id)
        return None

    async def _read(self, request_id: uuid.UUID, user: User) -> RepairRequestRead:
        request = await self._get_or_404(request_id)
        can_see = await self.access.can_see_address(request, user)
        return self.access.serialize(request, can_see_address=can_see)

    async def _get_or_404(self, request_id: uuid.UUID) -> RepairRequest:
        request = await self.repo.get_detail(request_id)
        if request is None:
            raise NotFoundError("Solicitud no encontrada")
        return request

    @staticmethod
    def _assert_owner(request: RepairRequest, user: User) -> None:
        if request.customer_id != user.id:
            raise ForbiddenError("No eres el propietario de esta solicitud")
