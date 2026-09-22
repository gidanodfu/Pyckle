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

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.domains.conversations.repository import ConversationRepository
from app.domains.geo.service import GeoService
from app.domains.orders.repository import OrderRepository
from app.domains.quotations.repository import QuotationRepository
from app.domains.repair_requests.repository import RepairRequestRepository
from app.domains.reviews.repository import ReviewRepository
from app.domains.users.repository import PermissionRepository, RoleRepository, UserRepository
from app.domains.users.schemas import (
    AdminUserUpdate,
    CustomerProfileRead,
    CustomerProfileUpdate,
    MeRead,
    PermissionRead,
    RoleRead,
    UserRead,
    UserUpdate,
)
from app.models.customer import CustomerProfile
from app.models.user import User


def build_customer_profile_read(profile: CustomerProfile) -> CustomerProfileRead:
    return CustomerProfileRead(
        id=profile.id,
        address=profile.address,
        district=profile.district,
        city=profile.city,
        department_id=profile.department_id,
        province_id=profile.province_id,
        district_id=profile.district_id,
        department_name=profile.department.name if profile.department else None,
        province_name=profile.province.name if profile.province else None,
        district_name=profile.district_geo.name if profile.district_geo else None,
    )


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.roles = RoleRepository(session)
        self.permissions = PermissionRepository(session)

    async def get_me(self, user_id: uuid.UUID) -> MeRead:
        user = await self.users.get_me(user_id)
        if user is None:
            raise NotFoundError("Usuario no encontrado")
        technician = user.technician_profile
        customer_profile = (
            build_customer_profile_read(user.customer_profile) if user.customer_profile else None
        )
        return MeRead(
            user=UserRead.model_validate(user),
            customer_profile=customer_profile,
            technician_id=technician.id if technician else None,
            permissions=sorted(user.permission_codes),
        )

    async def _assert_phone_available(
        self, phone_normalized: str | None, current_user_id: uuid.UUID | None = None
    ) -> None:
        if not phone_normalized:
            return
        existing = await self.users.get_by_phone(phone_normalized)
        if existing is not None and existing.id != current_user_id:
            raise ConflictError("El teléfono ya está registrado")

    async def update_me(self, user_id: uuid.UUID, data: UserUpdate) -> UserRead:
        user = await self.users.get_with_roles(user_id)
        if user is None:
            raise NotFoundError("Usuario no encontrado")
        payload = data.model_dump(exclude_unset=True)
        if "phone" in payload:
            await self._assert_phone_available(payload["phone"], user_id)
            user.phone = payload.pop("phone")
            user.phone_normalized = user.phone
        for field, value in payload.items():
            setattr(user, field, value)
        await self.session.commit()
        return UserRead.model_validate(user)

    async def update_customer_profile(
        self, user_id: uuid.UUID, data: CustomerProfileUpdate
    ) -> CustomerProfileRead:
        user = await self.users.get_me(user_id)
        if user is None or user.customer_profile is None:
            raise NotFoundError("Perfil de cliente no encontrado")
        profile = user.customer_profile
        payload = data.model_dump(exclude_unset=True)
        if any(
            payload.get(field) is not None
            for field in ("department_id", "province_id", "district_id")
        ):
            district = await GeoService(self.session).resolve(
                payload.get("department_id"),
                payload.get("province_id"),
                payload.get("district_id"),
            )
            profile.department_id = district.department_id
            profile.province_id = district.province_id
            profile.district_id = district.id
            profile.district = district.name
            profile.city = district.department.name
        if "address" in payload:
            profile.address = payload["address"]
        await self.session.commit()
        return build_customer_profile_read(profile)

    async def change_password(
        self, user_id: uuid.UUID, current_password: str, new_password: str
    ) -> None:
        user = await self.users.get(user_id)
        if user is None:
            raise NotFoundError("Usuario no encontrado")
        if not verify_password(current_password, user.hashed_password):
            raise BadRequestError("La contraseña actual no es correcta")
        user.hashed_password = hash_password(new_password)
        # Revoca de inmediato los access tokens vigentes (claim ``tv``) en el
        # mismo commit; el refresh se invalida además por el epoch de Redis.
        user.token_version += 1
        await self.session.commit()
        # Revoca todas las sesiones de refresh previas: una credencial robada
        # deja de poder renovarse tras el cambio de contraseña.
        from app.domains.auth.service import AuthService

        await AuthService(self.session).revoke_all_refresh_tokens(user.id)

    async def list_roles(self) -> list[RoleRead]:
        return [RoleRead.model_validate(role) for role in await self.roles.list_all_ordered()]

    async def list_permissions(self) -> list[PermissionRead]:
        permissions = await self.permissions.list_all_ordered()
        return [PermissionRead.model_validate(permission) for permission in permissions]

    async def admin_list(
        self,
        *,
        role: str | None = None,
        search: str | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[UserRead], int]:
        users, total = await self.users.list_paginated(
            role=role, search=search, is_active=is_active, limit=limit, offset=offset
        )
        return [UserRead.model_validate(user) for user in users], total

    async def admin_update(self, user_id: uuid.UUID, data: AdminUserUpdate) -> UserRead:
        user = await self.users.get_with_roles(user_id)
        if user is None:
            raise NotFoundError("Usuario no encontrado")
        payload = data.model_dump(exclude_unset=True)
        if "phone" in payload:
            await self._assert_phone_available(payload["phone"], user_id)
            user.phone = payload.pop("phone")
            user.phone_normalized = user.phone
        role_names = payload.pop("roles", None)
        for field, value in payload.items():
            setattr(user, field, value)
        if role_names is not None:
            roles = []
            for name in role_names:
                role = await self.roles.get_by_name(name)
                if role is None:
                    raise BadRequestError(f"Rol inexistente: {name}")
                roles.append(role)
            user.roles = roles
        await self.session.commit()
        return UserRead.model_validate(await self.users.get_with_roles(user_id))

    async def admin_delete(self, user_id: uuid.UUID, current_user_id: uuid.UUID) -> None:
        if user_id == current_user_id:
            raise ConflictError("No puedes eliminar tu propia cuenta")
        user = await self.users.get_me(user_id)
        if user is None:
            raise NotFoundError("Usuario no encontrado")
        if await self._has_operational_footprint(user):
            raise ConflictError(
                "No se puede eliminar un usuario con actividad registrada; "
                "desactiva la cuenta en su lugar."
            )
        await self.users.delete(user)
        await self.session.commit()

    async def _has_operational_footprint(self, user: User) -> bool:
        """Un usuario solo se borra en duro si no participa en ningún registro
        operativo. Esas tablas referencian a ``users`` con ON DELETE CASCADE, por
        lo que borrarlo destruiría solicitudes, cotizaciones, conversaciones y
        reseñas (incluso de terceros). Ante cualquier huella se exige desactivar.
        """
        orders = OrderRepository(self.session)
        if await orders.count_for_customer(user.id) > 0:
            return True
        technician = user.technician_profile
        if technician is not None and await orders.count_for_technician(technician.id) > 0:
            return True
        if await RepairRequestRepository(self.session).count_for_customer(user.id) > 0:
            return True
        if await ReviewRepository(self.session).count_for_customer(user.id) > 0:
            return True
        if technician is not None:
            if await QuotationRepository(self.session).count_for_technician(technician.id) > 0:
                return True
            if await ReviewRepository(self.session).count_for_technician(technician.id) > 0:
                return True
        conversations = ConversationRepository(self.session)
        if (
            await conversations.count_for_participant(
                user.id, technician.id if technician else None
            )
            > 0
        ):
            return True
        return False
