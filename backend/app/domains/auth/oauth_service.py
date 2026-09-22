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

"""Orquestación del flujo OAuth server-side (independiente del proveedor)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import ConflictError
from app.core.ratelimit import RegistrationRateLimiter, registration_identifier
from app.core.redis import get_redis
from app.core.security import hash_password
from app.domains.auth.oauth import registry
from app.domains.auth.oauth.base import (
    OAUTH_EMAIL_ALREADY_REGISTERED,
    OAUTH_EXCHANGE_EXPIRED,
    OAUTH_EXCHANGE_INVALID,
    OAUTH_ONBOARDING_EXPIRED,
    OAUTH_ONBOARDING_INVALID,
    OAUTH_STATE_INVALID,
    OAuthError,
    OAuthIdentity,
)
from app.domains.auth.repository import OAuthAccountRepository
from app.domains.auth.schemas import (
    OAuthCompleteRequest,
    OAuthOnboardingRead,
    TokenPair,
)
from app.domains.auth.service import (
    EMAIL_ALREADY_REGISTERED_CODE,
    EMAIL_ALREADY_REGISTERED_MESSAGE,
    PHONE_ALREADY_REGISTERED_CODE,
    PHONE_ALREADY_REGISTERED_MESSAGE,
    AuthService,
    translate_integrity_error,
)
from app.domains.geo.service import GeoService
from app.domains.technicians.modality import validate_service_modality
from app.domains.users.repository import RoleRepository, UserRepository
from app.models.customer import CustomerProfile
from app.models.enums import RoleName
from app.models.oauth import OAuthAccount
from app.models.technician import Technician
from app.models.user import User

settings = get_settings()

# El state (CSRF/PKCE) y el codigo de intercambio conservan su ventana propia;
# el TTL del onboarding (120 s) vive en settings.oauth_onboarding_ttl_seconds.
STATE_TTL_SECONDS = 600
EXCHANGE_TTL_SECONDS = 60
ALLOWED_ROLES = {RoleName.CUSTOMER.value, RoleName.TECHNICIAN.value}
# Cookie efímera que ata el state OAuth al navegador que inició el flujo.
OAUTH_BIND_COOKIE = "pyckle_oauth_bind"


def _bind_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass(slots=True)
class CallbackResult:
    kind: str
    redirect_url: str


class OAuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.accounts = OAuthAccountRepository(session)
        self.users = UserRepository(session)
        self.roles = RoleRepository(session)
        self.geo = GeoService(session)

    # ------------------------------------------------------------------ inicio

    async def begin(self, intent: str | None = None) -> tuple[str, str]:
        """Inicia el flujo y devuelve (url_de_google, valor_de_binding).

        ``intent`` es solo una pista de UI (login/register) del frontend; la
        resolucion de la cuenta depende exclusivamente de la identidad y del
        estado en BD, nunca del valor enviado por el cliente, por lo que no se
        persiste ni influye en la politica de acceso.
        """
        _ = intent
        provider = registry.get_provider("google")
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(16)
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )
        # Binding al navegador: se guarda solo el hash en Redis y el valor
        # crudo viaja en una cookie HttpOnly. Un tercero que robe/reciba el
        # state+code no tiene la cookie y no puede completar el callback.
        bind = secrets.token_urlsafe(32)
        payload = {
            "provider": provider.name,
            "nonce": nonce,
            "code_verifier": code_verifier,
            "bind": _bind_hash(bind),
        }
        await get_redis().setex(f"oauth:state:{state}", STATE_TTL_SECONDS, json.dumps(payload))
        url = provider.authorization_url(state=state, nonce=nonce, code_challenge=code_challenge)
        return url, bind

    # ---------------------------------------------------------------- callback

    async def handle_callback(
        self, code: str | None, state: str | None, browser_bind: str | None = None
    ) -> CallbackResult:
        if not code or not state:
            raise OAuthError("Respuesta de Google incompleta")
        raw = await get_redis().getdel(f"oauth:state:{state}")
        if raw is None:
            raise OAuthError(
                "El estado de autenticación es inválido o expiró", code=OAUTH_STATE_INVALID
            )
        data = json.loads(raw)
        expected_bind = data.get("bind")
        if (
            not expected_bind
            or not browser_bind
            or not hmac.compare_digest(_bind_hash(browser_bind), expected_bind)
        ):
            # El flujo no lo inició este navegador (posible login CSRF).
            raise OAuthError(
                "El estado de autenticación es inválido o expiró", code=OAUTH_STATE_INVALID
            )
        provider = registry.get_provider(data["provider"])
        tokens = await provider.exchange_code(code=code, code_verifier=data["code_verifier"])
        identity = await provider.get_identity(tokens, nonce=data["nonce"])
        return await self._resolve_identity(identity)

    async def _resolve_identity(self, identity: OAuthIdentity) -> CallbackResult:
        account = await self.accounts.get_by_provider_user(
            identity.provider, identity.provider_user_id
        )
        if account is not None:
            return await self._login_existing(account)

        existing = await self.users.get_by_email(identity.email)
        if existing is not None:
            # Nunca vincular por email de forma silenciosa (riesgo de takeover).
            raise OAuthError(EMAIL_ALREADY_REGISTERED_MESSAGE, code=OAUTH_EMAIL_ALREADY_REGISTERED)

        token = secrets.token_urlsafe(32)
        await get_redis().setex(
            f"oauth:onboarding:{token}",
            get_settings().oauth_onboarding_ttl_seconds,
            json.dumps(
                {
                    "provider": identity.provider,
                    "provider_user_id": identity.provider_user_id,
                    "email": identity.email,
                    "email_verified": identity.email_verified,
                    "name": identity.name,
                    "given_name": identity.given_name,
                    "family_name": identity.family_name,
                    "picture": identity.picture,
                }
            ),
        )
        return CallbackResult(
            kind="onboarding",
            redirect_url=self._frontend(f"/register?oauth_token={token}"),
        )

    async def _login_existing(self, account: OAuthAccount) -> CallbackResult:
        user = await self.users.get_with_roles(account.user_id)
        if user is None or not user.is_active:
            raise OAuthError("La cuenta no está disponible")
        if RoleName.ADMIN.value in user.role_names:
            raise OAuthError("El acceso con Google no está disponible para administradores")
        tokens = await AuthService(self.session).issue_tokens(user)
        return CallbackResult(kind="login", redirect_url=await self._issue_exchange(tokens))

    # ---------------------------------------------------------------- intercambio

    async def _issue_exchange(self, tokens: TokenPair) -> str:
        otp = secrets.token_urlsafe(32)
        await get_redis().setex(
            f"oauth:exchange:{otp}",
            EXCHANGE_TTL_SECONDS,
            tokens.model_dump_json(),
        )
        return self._frontend(f"/auth/callback?code={otp}")

    async def exchange(self, code: str | None) -> TokenPair:
        if not code:
            raise OAuthError(
                "El código de intercambio es inválido o expiró", code=OAUTH_EXCHANGE_INVALID
            )
        raw = await get_redis().getdel(f"oauth:exchange:{code}")
        if raw is None:
            raise OAuthError(
                "El código de intercambio es inválido o expiró", code=OAUTH_EXCHANGE_EXPIRED
            )
        try:
            return TokenPair.model_validate_json(raw)
        except ValueError as exc:
            raise OAuthError(
                "El código de intercambio es inválido o expiró", code=OAUTH_EXCHANGE_INVALID
            ) from exc

    # ---------------------------------------------------------------- onboarding

    async def onboarding_identity(self, token: str) -> OAuthOnboardingRead:
        """Peek no consumible de la identidad pendiente de onboarding.

        Devuelve solo lo mínimo para mostrar el formulario; nunca tokens,
        códigos ni secretos. El token permanece en Redis hasta completar.
        """
        payload = await self._read_onboarding(token)
        return OAuthOnboardingRead(
            email=payload["email"],
            full_name=payload.get("name"),
            provider=payload["provider"],
        )

    async def _read_onboarding(self, token: str) -> dict:
        raw = await get_redis().get(f"oauth:onboarding:{token}")
        if raw is None:
            raise OAuthError(
                "El registro con Google expiró. Intenta nuevamente.",
                code=OAUTH_ONBOARDING_EXPIRED,
            )
        try:
            payload = json.loads(raw)
        except (TypeError, ValueError) as exc:
            raise OAuthError(
                "El registro con Google es inválido. Intenta nuevamente.",
                code=OAUTH_ONBOARDING_INVALID,
            ) from exc
        if not payload.get("email") or not payload.get("provider_user_id"):
            raise OAuthError(
                "El registro con Google es inválido. Intenta nuevamente.",
                code=OAUTH_ONBOARDING_INVALID,
            )
        return payload

    async def complete_onboarding(self, data: OAuthCompleteRequest, client_ip: str) -> TokenPair:
        # Rate limit de alta de cuentas por IP confiable. Es independiente del
        # TTL de onboarding (``oauth:onboarding:{token}``, 120 s, un solo uso):
        # aquí solo se acota cuántas altas puede originar una misma conexión.
        await RegistrationRateLimiter().reserve(registration_identifier(client_ip))
        # 1) Leer sin consumir: un error de validación corregible no debe quemar
        #    el token ni obligar a repetir Google.
        payload = await self._read_onboarding(data.oauth_token)
        if data.role not in ALLOWED_ROLES:
            raise OAuthError("El rol seleccionado no está permitido")
        identity = OAuthIdentity(
            provider=payload["provider"],
            provider_user_id=payload["provider_user_id"],
            email=payload["email"],
            email_verified=bool(payload.get("email_verified")),
            name=payload.get("name"),
            given_name=payload.get("given_name"),
            family_name=payload.get("family_name"),
            picture=payload.get("picture"),
        )
        if await self.users.get_by_email(identity.email):
            raise ConflictError(
                EMAIL_ALREADY_REGISTERED_MESSAGE, code=EMAIL_ALREADY_REGISTERED_CODE
            )
        if data.phone and await self.users.get_by_phone(data.phone):
            raise ConflictError(
                PHONE_ALREADY_REGISTERED_MESSAGE, code=PHONE_ALREADY_REGISTERED_CODE
            )
        district = await self.geo.resolve(data.department_id, data.province_id, data.district_id)
        role = await self.roles.get_by_name(data.role)
        if role is None:
            raise OAuthError("Rol inválido")
        workshop_address = None
        if data.role == RoleName.TECHNICIAN.value:
            workshop_address = validate_service_modality(
                offers_home_service=data.offers_home_service,
                offers_workshop_service=data.offers_workshop_service,
                workshop_address=data.workshop_address,
            )

        # 2) Consumo atómico (GETDEL): ocurre solo cuando todo está validado y
        #    listo para crear la cuenta. Dos requests concurrentes: solo uno
        #    obtiene el token; el otro recibe expirado/inválido.
        consumed = await get_redis().getdel(f"oauth:onboarding:{data.oauth_token}")
        if consumed is None:
            raise OAuthError(
                "El registro con Google expiró. Intenta nuevamente.",
                code=OAUTH_ONBOARDING_EXPIRED,
            )

        user = User(
            email=identity.email,
            # Hash aleatorio inutilizable: la cuenta se gestiona vía Google.
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            full_name=(data.full_name or identity.name or "Usuario Pyckle").strip(),
            phone=data.phone,
            phone_normalized=data.phone,
            terms_accepted_at=datetime.now(UTC),
        )
        user.roles.append(role)
        self.session.add(user)
        try:
            await self.session.flush()

            if data.role == RoleName.TECHNICIAN.value:
                self.session.add(
                    Technician(
                        user_id=user.id,
                        offers_home_service=data.offers_home_service,
                        offers_workshop_service=data.offers_workshop_service,
                        workshop_address=workshop_address,
                        department_id=district.department_id,
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
                        city=district.department.name,
                        department_id=district.department_id,
                        province_id=district.province_id,
                        district_id=district.id,
                    )
                )
            self.session.add(
                OAuthAccount(
                    user_id=user.id,
                    provider=identity.provider,
                    provider_user_id=identity.provider_user_id,
                    email=identity.email,
                )
            )
            await self.session.commit()
        except IntegrityError as exc:
            # Condicion de carrera entre el chequeo previo y la insercion: la
            # constraint UNIQUE es la ultima barrera y se traduce a dominio.
            await self.session.rollback()
            raise translate_integrity_error(exc) from exc

        user = await self.users.get_with_roles(user.id)
        if user is None:
            raise OAuthError("No se pudo crear la cuenta")
        return await AuthService(self.session).issue_tokens(user)

    # --------------------------------------------------------------------- utils

    @staticmethod
    def _frontend(path: str) -> str:
        return f"{settings.frontend_url.rstrip('/')}{path}"
