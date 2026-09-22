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
from datetime import UTC, datetime

import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from app.core.ratelimit import (
    LoginRateLimiter,
    RegistrationRateLimiter,
    login_identifier,
    registration_identifier,
)
from app.core.redis import get_redis
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    needs_rehash,
    verify_password,
)
from app.domains.auth.schemas import RegisterRequest, TokenPair
from app.domains.geo.service import GeoService
from app.domains.technicians.modality import validate_service_modality
from app.domains.users.repository import RoleRepository, UserRepository
from app.models.customer import CustomerProfile
from app.models.enums import RoleName
from app.models.technician import Technician
from app.models.user import User

settings = get_settings()

INVALID_CREDENTIALS = "Credenciales incorrectas."
# Mensaje unico (tradicional y Google) para correos ya registrados.
EMAIL_ALREADY_REGISTERED_MESSAGE = "Este correo ya ha sido registrado, prueba con otro"
EMAIL_ALREADY_REGISTERED_CODE = "email_already_registered"
PHONE_ALREADY_REGISTERED_MESSAGE = "El teléfono ya está registrado."
PHONE_ALREADY_REGISTERED_CODE = "phone_already_registered"
OAUTH_ACCOUNT_LINKED_CODE = "oauth_account_already_linked"

# Nombres reales de constraints/índices unicos del esquema (ver migraciones).
_USERS_EMAIL_CONSTRAINT = "ix_users_email"
_USERS_PHONE_CONSTRAINT = "ix_users_phone_normalized"
_OAUTH_ACCOUNT_CONSTRAINT = "uq_oauth_accounts_provider_user"


def translate_integrity_error(exc: IntegrityError) -> ConflictError:
    """Traduce una violacion de unicidad a un error de dominio controlado.

    Depende del nombre real de la constraint; cualquier otra violacion se
    reporta como conflicto generico (nunca como email duplicado).
    """
    orig = getattr(exc, "orig", None)
    name = getattr(orig, "constraint_name", None)
    if not name:
        # Compatibilidad con drivers que no exponen ``constraint_name``: se
        # busca el nombre exacto dentro del texto del error.
        text = str(exc)
        for candidate in (
            _USERS_EMAIL_CONSTRAINT,
            _USERS_PHONE_CONSTRAINT,
            _OAUTH_ACCOUNT_CONSTRAINT,
        ):
            if candidate in text:
                name = candidate
                break
    if name == _USERS_EMAIL_CONSTRAINT:
        return ConflictError(EMAIL_ALREADY_REGISTERED_MESSAGE, code=EMAIL_ALREADY_REGISTERED_CODE)
    if name == _USERS_PHONE_CONSTRAINT:
        return ConflictError(PHONE_ALREADY_REGISTERED_MESSAGE, code=PHONE_ALREADY_REGISTERED_CODE)
    if name == _OAUTH_ACCOUNT_CONSTRAINT:
        return ConflictError(
            "Esta cuenta de Google ya está vinculada.", code=OAUTH_ACCOUNT_LINKED_CODE
        )
    return ConflictError("La operación entra en conflicto con el estado actual.")


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.roles = RoleRepository(session)
        self.geo = GeoService(session)

    async def register(self, data: RegisterRequest, client_ip: str) -> User:
        # Reserva antes de hashear: acota el abuso de Argon2 y de altas por IP.
        # El principal es la IP confiable (el email es trivial de variar).
        await RegistrationRateLimiter().reserve(registration_identifier(client_ip))
        if await self.users.get_by_email(data.email):
            raise ConflictError(
                EMAIL_ALREADY_REGISTERED_MESSAGE, code=EMAIL_ALREADY_REGISTERED_CODE
            )
        if data.phone and await self.users.get_by_phone(data.phone):
            raise ConflictError(
                PHONE_ALREADY_REGISTERED_MESSAGE, code=PHONE_ALREADY_REGISTERED_CODE
            )

        role = await self.roles.get_by_name(data.role)
        if role is None:
            raise ConflictError("Rol inválido")

        district = await self.geo.resolve(data.department_id, data.province_id, data.district_id)
        department = district.department

        user = User(
            email=data.email.lower(),
            hashed_password=hash_password(data.password),
            full_name=data.full_name.strip(),
            phone=data.phone,
            phone_normalized=data.phone,
            terms_accepted_at=datetime.now(UTC),
        )
        user.roles.append(role)
        self.session.add(user)
        try:
            await self.session.flush()

            if data.role == RoleName.TECHNICIAN:
                workshop_address = validate_service_modality(
                    offers_home_service=data.offers_home_service,
                    offers_workshop_service=data.offers_workshop_service,
                    workshop_address=data.workshop_address,
                )
                self.session.add(
                    Technician(
                        user_id=user.id,
                        offers_home_service=data.offers_home_service,
                        offers_workshop_service=data.offers_workshop_service,
                        workshop_address=workshop_address,
                        department_id=department.id,
                        province_id=district.province_id,
                        district_id=district.id,
                    )
                )
            else:
                self.session.add(
                    CustomerProfile(
                        user_id=user.id,
                        address=data.address,
                        district=district.name,
                        city=department.name,
                        department_id=department.id,
                        province_id=district.province_id,
                        district_id=district.id,
                    )
                )

            await self.session.commit()
        except IntegrityError as exc:
            # La constraint UNIQUE es la ultima barrera ante una condicion de
            # carrera; la sesion debe quedar recuperable tras el rollback.
            await self.session.rollback()
            raise translate_integrity_error(exc) from exc
        return await self._reload(user.id)

    async def authenticate(self, email: str, password: str, client_ip: str) -> User:
        limiter = LoginRateLimiter()
        identifier = login_identifier(email, client_ip)
        # Reserva atómica del intento antes de verificar: evita que una ráfaga
        # concurrente supere el máximo de intentos.
        await limiter.reserve(identifier)

        user = await self.users.get_by_email(email)
        if user is None or not verify_password(password, user.hashed_password):
            raise UnauthorizedError(INVALID_CREDENTIALS)

        await limiter.reset(identifier)
        if not user.is_active:
            raise ForbiddenError("La cuenta está desactivada")
        if needs_rehash(user.hashed_password):
            user.hashed_password = hash_password(password)
            await self.session.commit()
        return user

    @staticmethod
    def _version_key(user_id: object) -> str:
        return f"refresh:version:{user_id}"

    async def _refresh_version(self, user_id: object) -> int:
        raw = await get_redis().get(self._version_key(user_id))
        try:
            return int(raw) if raw is not None else 0
        except (TypeError, ValueError):
            return 0

    async def revoke_all_refresh_tokens(self, user_id: object) -> None:
        """Invalida todos los refresh tokens del usuario.

        Incrementa un epoch versionado en Redis que viaja en cada refresh token:
        cualquier token emitido antes del cambio queda rechazado en el próximo
        ``refresh`` sin necesidad de enumerar sus JTIs. No expira; si Redis se
        vacía, los ``refresh:{jti}`` también desaparecen y el refresh falla.
        """
        await get_redis().incr(self._version_key(user_id))

    async def issue_tokens(self, user: User) -> TokenPair:
        access_token, _ = create_access_token(
            str(user.id), {"roles": sorted(user.role_names)}, user.token_version
        )
        version = await self._refresh_version(user.id)
        refresh_token, _, jti = create_refresh_token(str(user.id), version, user.token_version)
        await get_redis().setex(
            f"refresh:{jti}", settings.refresh_token_expire_days * 86400, str(user.id)
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def refresh(self, refresh_token: str) -> TokenPair:
        payload = self._decode_refresh(refresh_token)
        jti = payload["jti"]
        # GETDEL atómico: un refresh token solo puede consumirse una vez.
        stored = await get_redis().getdel(f"refresh:{jti}")
        if stored is None:
            raise UnauthorizedError("Refresh token revocado o expirado")
        subject = payload.get("sub")
        if stored != subject:
            raise UnauthorizedError("Refresh token inválido")
        try:
            user_id = uuid.UUID(subject)
        except (TypeError, ValueError) as exc:
            raise UnauthorizedError("Refresh token inválido") from exc
        # Epoch de revocación: un token emitido antes de un cambio de contraseña
        # trae una versión anterior y se rechaza aunque su JTI siga existiendo.
        if int(payload.get("ver", 0)) != await self._refresh_version(user_id):
            raise UnauthorizedError("Refresh token revocado o expirado")
        user = await self.users.get_with_roles(user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Usuario no válido")
        # Epoch de revocación: un token emitido antes de un cambio de contraseña
        # (o de otra revocación masiva) se rechaza aunque su JTI siga existiendo.
        if int(payload.get("tv", 0)) != user.token_version:
            raise UnauthorizedError("Refresh token revocado o expirado")
        return await self.issue_tokens(user)

    async def logout(self, refresh_token: str) -> None:
        payload = self._decode_refresh(refresh_token)
        await get_redis().delete(f"refresh:{payload['jti']}")

    def _decode_refresh(self, token: str) -> dict:
        try:
            payload = decode_token(token)
        except jwt.PyJWTError as exc:
            raise UnauthorizedError("Refresh token inválido") from exc
        if payload.get("type") != "refresh":
            raise UnauthorizedError("Tipo de token inválido")
        return payload

    async def _reload(self, user_id: uuid.UUID) -> User:
        user = await self.users.get_with_roles(user_id)
        if user is None:
            raise NotFoundError("Usuario no encontrado")
        return user
