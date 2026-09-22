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

from fastapi import APIRouter, Request, status
from fastapi.responses import RedirectResponse

from app.core.config import get_settings
from app.core.dependencies import CurrentUser, DbSession, client_ip
from app.core.exceptions import NotFoundError
from app.domains.auth.oauth.base import OAuthError
from app.domains.auth.oauth_service import (
    OAUTH_BIND_COOKIE,
    STATE_TTL_SECONDS,
    OAuthService,
)
from app.domains.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    OAuthCompleteRequest,
    OAuthExchangeRequest,
    OAuthOnboardingRead,
    OAuthOnboardingRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
)
from app.domains.auth.service import AuthService
from app.domains.users.schemas import MeRead, UserRead
from app.domains.users.service import UserService
from app.schemas.common import Message

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, request: Request, session: DbSession) -> UserRead:
    user = await AuthService(session).register(data, client_ip(request))
    return UserRead.model_validate(user)


@router.post("/login", response_model=TokenPair)
async def login(data: LoginRequest, request: Request, session: DbSession) -> TokenPair:
    service = AuthService(session)
    user = await service.authenticate(data.email, data.password, client_ip(request))
    return await service.issue_tokens(user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(data: RefreshRequest, session: DbSession) -> TokenPair:
    return await AuthService(session).refresh(data.refresh_token)


@router.post("/logout", response_model=Message)
async def logout(data: LogoutRequest, session: DbSession) -> Message:
    await AuthService(session).logout(data.refresh_token)
    return Message(detail="Sesión cerrada")


@router.get("/me", response_model=MeRead)
async def me(current_user: CurrentUser, session: DbSession) -> MeRead:
    return await UserService(session).get_me(current_user.id)


@router.get("/providers")
async def oauth_providers() -> dict[str, bool]:
    """Indica al frontend qué proveedores OAuth están disponibles (sin secretos)."""
    return {"google": settings.google_oauth_enabled}


def _oauth_cookie_path() -> str:
    return f"{settings.api_v1_prefix}/auth/google"


@router.get("/google")
async def google_start(session: DbSession, intent: str | None = None) -> RedirectResponse:
    if not settings.google_oauth_enabled:
        raise NotFoundError("El inicio de sesión con Google no está disponible")
    url, bind = await OAuthService(session).begin(intent)
    response = RedirectResponse(url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        OAUTH_BIND_COOKIE,
        bind,
        max_age=STATE_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        path=_oauth_cookie_path(),
    )
    return response


@router.get("/google/callback")
async def google_callback(
    request: Request,
    session: DbSession,
    code: str | None = None,
    state: str | None = None,
) -> RedirectResponse:
    if not settings.google_oauth_enabled:
        raise NotFoundError("El inicio de sesión con Google no está disponible")
    browser_bind = request.cookies.get(OAUTH_BIND_COOKIE)
    try:
        result = await OAuthService(session).handle_callback(code, state, browser_bind)
    except OAuthError as exc:
        # Solo un codigo de error no sensible viaja en la URL (nunca email,
        # tokens, state, nonce ni detalles internos).
        login_url = f"{settings.frontend_url.rstrip('/')}/login?oauth_error={exc.code}"
        response = RedirectResponse(login_url, status_code=status.HTTP_302_FOUND)
        response.delete_cookie(OAUTH_BIND_COOKIE, path=_oauth_cookie_path())
        return response
    response = RedirectResponse(result.redirect_url, status_code=status.HTTP_302_FOUND)
    response.delete_cookie(OAUTH_BIND_COOKIE, path=_oauth_cookie_path())
    return response


@router.post("/oauth/exchange", response_model=TokenPair)
async def oauth_exchange(data: OAuthExchangeRequest, session: DbSession) -> TokenPair:
    return await OAuthService(session).exchange(data.code)


@router.post("/oauth/onboarding", response_model=OAuthOnboardingRead)
async def oauth_onboarding(data: OAuthOnboardingRequest, session: DbSession) -> OAuthOnboardingRead:
    """Peek no consumible: valida el token y devuelve la identidad mínima."""
    return await OAuthService(session).onboarding_identity(data.oauth_token)


@router.post("/oauth/complete", response_model=TokenPair)
async def oauth_complete(
    data: OAuthCompleteRequest, request: Request, session: DbSession
) -> TokenPair:
    return await OAuthService(session).complete_onboarding(data, client_ip(request))
