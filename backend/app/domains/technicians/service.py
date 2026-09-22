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
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.domains.geo.repository import GeoRepository
from app.domains.geo.service import GeoService
from app.domains.orders.repository import OrderRepository
from app.domains.quotations.repository import QuotationRepository
from app.domains.technicians.modality import validate_service_modality
from app.domains.technicians.repository import SpecialtyRepository, TechnicianRepository
from app.domains.technicians.schemas import (
    SpecialtyCount,
    SpecialtyRead,
    TechnicianProfileUpdate,
    TechnicianPublic,
    TechnicianRead,
    TechnicianStats,
    TechnicianSummary,
)
from app.domains.users.repository import UserRepository
from app.domains.users.schemas import UserBrief
from app.models.enums import RepairStatus
from app.models.technician import Technician
from app.models.user import User


class TechnicianService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.technicians = TechnicianRepository(session)
        self.specialties = SpecialtyRepository(session)
        self.orders = OrderRepository(session)
        self.quotations = QuotationRepository(session)
        self.users = UserRepository(session)
        self.geo = GeoRepository(session)

    async def list_public(
        self,
        *,
        specialty_id: uuid.UUID | None = None,
        verified_only: bool = False,
        search: str | None = None,
        viewer: User | None = None,
        department_id: uuid.UUID | None = None,
        province_id: uuid.UUID | None = None,
        district_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TechnicianPublic], int, str, bool]:
        target = await self._target_location(viewer, department_id, province_id, district_id)
        if target is None:
            items, total = await self.technicians.list_public(
                specialty_id=specialty_id,
                verified_only=verified_only,
                search=search,
                limit=limit,
                offset=offset,
            )
            return [self._to_public(item) for item in items], total, "all", False

        levels = self._location_levels(*target)
        for index, (scope, filters) in enumerate(levels):
            items, total = await self.technicians.list_public(
                specialty_id=specialty_id,
                verified_only=verified_only,
                search=search,
                limit=limit,
                offset=offset,
                **filters,
            )
            if total > 0:
                return [self._to_public(item) for item in items], total, scope, index > 0
        scope = levels[-1][0] if levels else "all"
        return [], 0, scope, len(levels) > 1

    async def get_public(self, technician_id: uuid.UUID) -> TechnicianPublic:
        technician = await self.technicians.get_detail(technician_id)
        if technician is None:
            raise NotFoundError("Técnico no encontrado")
        return self._to_public(technician)

    async def get_for_user(self, user_id: uuid.UUID) -> TechnicianRead:
        technician = await self.technicians.get_by_user_id(user_id)
        if technician is None:
            raise ForbiddenError("El usuario no tiene perfil de técnico")
        return self._to_read(technician)

    async def update_profile(
        self, user_id: uuid.UUID, data: TechnicianProfileUpdate
    ) -> TechnicianRead:
        technician = await self.technicians.get_by_user_id(user_id)
        if technician is None:
            raise ForbiddenError("El usuario no tiene perfil de técnico")
        payload = data.model_dump(exclude_unset=True)
        specialty_ids = payload.pop("specialty_ids", None)
        modality_fields = ("offers_home_service", "offers_workshop_service", "workshop_address")
        modality = {field: payload.pop(field) for field in modality_fields if field in payload}
        if any(
            payload.get(field) is not None
            for field in ("department_id", "province_id", "district_id")
        ):
            district = await GeoService(self.session).resolve(
                payload.get("department_id"),
                payload.get("province_id"),
                payload.get("district_id"),
            )
            technician.department_id = district.department_id
            technician.province_id = district.province_id
            technician.district_id = district.id
        for field in ("department_id", "province_id", "district_id"):
            payload.pop(field, None)
        for field, value in payload.items():
            setattr(technician, field, value)
        technician.offers_home_service = modality.get(
            "offers_home_service", technician.offers_home_service
        )
        technician.offers_workshop_service = modality.get(
            "offers_workshop_service", technician.offers_workshop_service
        )
        technician.workshop_address = validate_service_modality(
            offers_home_service=technician.offers_home_service,
            offers_workshop_service=technician.offers_workshop_service,
            workshop_address=modality.get("workshop_address", technician.workshop_address),
        )
        if specialty_ids is not None:
            technician.specialties = await self.specialties.list_by_ids(specialty_ids)
        await self.session.commit()
        return self._to_read(await self.technicians.get_by_user_id(user_id))

    async def verify(self, technician_id: uuid.UUID, verified: bool) -> TechnicianRead:
        technician = await self.technicians.get_detail(technician_id)
        if technician is None:
            raise NotFoundError("Técnico no encontrado")
        technician.is_verified = verified
        await self.session.commit()
        return self._to_read(technician)

    async def stats(self, user_id: uuid.UUID) -> TechnicianStats:
        technician = await self.technicians.get_by_user_id(user_id)
        if technician is None:
            raise ForbiddenError("El usuario no tiene perfil de técnico")
        active = await self.orders.count_active_for_technician(technician.id)
        completed = await self.orders.count_for_technician(technician.id, [RepairStatus.COMPLETED])
        earnings = await self.orders.sum_completed_for_technician(technician.id)
        pending = await self.quotations.count_pending_for_technician(technician.id)
        return TechnicianStats(
            active_orders=active,
            completed_orders=completed,
            total_earnings=Decimal(earnings),
            pending_quotations=pending,
        )

    async def summary(self, user_id: uuid.UUID) -> TechnicianSummary:
        technician = await self.technicians.get_by_user_id(user_id)
        if technician is None:
            raise ForbiddenError("El usuario no tiene perfil de técnico")
        by_status = await self.orders.counts_by_status_for_technician(technician.id)
        by_result = await self.orders.count_by_result_for_technician(technician.id)
        by_specialty = await self.orders.counts_by_specialty_for_technician(technician.id)
        pending_changes = await self.orders.count_pending_price_changes_for_technician(
            technician.id
        )
        return TechnicianSummary(
            total=sum(by_status.values()),
            by_status=by_status,
            by_result=by_result,
            by_specialty=[
                SpecialtyCount(specialty_id=specialty_id, name=name, count=count)
                for specialty_id, name, count in by_specialty
            ],
            pending_price_changes=pending_changes,
        )

    async def _target_location(
        self,
        viewer: User | None,
        department_id: uuid.UUID | None,
        province_id: uuid.UUID | None,
        district_id: uuid.UUID | None,
    ) -> tuple[uuid.UUID | None, uuid.UUID | None, uuid.UUID | None] | None:
        if district_id is not None:
            district = await self.geo.get_district(district_id)
            if district is not None:
                return district.department_id, district.province_id, district.id
        if province_id is not None:
            province = await self.geo.get_province(province_id)
            if province is not None:
                return province.department_id, province.id, None
        if department_id is not None:
            return department_id, None, None
        if viewer is None:
            return None
        user = await self.users.get_me(viewer.id)
        profile = user.customer_profile if user else None
        if profile is None or profile.district_id is None:
            return None
        return profile.department_id, profile.province_id, profile.district_id

    @staticmethod
    def _location_levels(
        department_id: uuid.UUID | None,
        province_id: uuid.UUID | None,
        district_id: uuid.UUID | None,
    ) -> list[tuple[str, dict]]:
        levels: list[tuple[str, dict]] = []
        if district_id is not None:
            levels.append(("district", {"district_id": district_id}))
        if province_id is not None:
            levels.append(("province", {"province_id": province_id}))
        if department_id is not None:
            levels.append(("department", {"department_id": department_id}))
        return levels

    @staticmethod
    def _location_names(technician: Technician) -> dict[str, str | None]:
        return {
            "department_name": technician.department.name if technician.department else None,
            "province_name": technician.province.name if technician.province else None,
            "district_name": (technician.district_geo.name if technician.district_geo else None),
        }

    def _to_public(self, technician: Technician) -> TechnicianPublic:
        return TechnicianPublic(
            id=technician.id,
            full_name=technician.full_name,
            bio=technician.bio,
            experience_years=technician.experience_years,
            is_verified=technician.is_verified,
            offers_home_service=technician.offers_home_service,
            offers_workshop_service=technician.offers_workshop_service,
            rating_avg=technician.rating_avg,
            rating_count=technician.rating_count,
            specialties=[SpecialtyRead.model_validate(s) for s in technician.specialties],
            **self._location_names(technician),
        )

    def _to_read(self, technician: Technician) -> TechnicianRead:
        return TechnicianRead(
            id=technician.id,
            user=UserBrief.model_validate(technician.user),
            bio=technician.bio,
            experience_years=technician.experience_years,
            is_verified=technician.is_verified,
            offers_home_service=technician.offers_home_service,
            offers_workshop_service=technician.offers_workshop_service,
            workshop_address=technician.workshop_address,
            department_id=technician.department_id,
            province_id=technician.province_id,
            district_id=technician.district_id,
            rating_avg=technician.rating_avg,
            rating_count=technician.rating_count,
            specialties=[SpecialtyRead.model_validate(s) for s in technician.specialties],
            created_at=technician.created_at,
            **self._location_names(technician),
        )
