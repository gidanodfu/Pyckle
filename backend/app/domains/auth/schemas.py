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

from pydantic import EmailStr, Field, field_validator

from app.core.phone import normalize_phone
from app.schemas.common import NonBlankStr, ORMModel


def _normalize_phone_or_error(value: str) -> str:
    normalized = normalize_phone(value)
    if not normalized:
        raise ValueError("Teléfono inválido")
    return normalized


class RegisterRequest(ORMModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: NonBlankStr = Field(min_length=2, max_length=150)
    phone: str = Field(min_length=6, max_length=30)
    role: str = Field(default="customer", pattern="^(customer|technician)$")
    department_id: uuid.UUID
    province_id: uuid.UUID
    district_id: uuid.UUID
    # Dirección del cliente (privada) o del taller del técnico.
    address: str | None = Field(default=None, max_length=255)
    offers_home_service: bool = True
    offers_workshop_service: bool = False
    workshop_address: str | None = Field(default=None, max_length=255)
    accept_terms: bool

    @field_validator("accept_terms")
    @classmethod
    def validate_accept_terms(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Debes aceptar los Términos y Condiciones")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        normalized = normalize_phone(value)
        if not normalized:
            raise ValueError("Teléfono inválido")
        return normalized

    @field_validator("address", "workshop_address")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class LoginRequest(ORMModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(ORMModel):
    refresh_token: str


class LogoutRequest(ORMModel):
    refresh_token: str


class TokenPair(ORMModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class OAuthExchangeRequest(ORMModel):
    code: str = Field(min_length=1, max_length=200)


class OAuthOnboardingRequest(ORMModel):
    """Consulta (peek) de la identidad Google pendiente de completar registro."""

    oauth_token: str = Field(min_length=1, max_length=200)


class OAuthOnboardingRead(ORMModel):
    """Datos minimos para mostrar el onboarding; nunca secretos ni tokens."""

    email: EmailStr
    full_name: str | None = None
    provider: str


class OAuthCompleteRequest(ORMModel):
    """Onboarding de un usuario nuevo autenticado con Google (sin contraseña)."""

    oauth_token: str = Field(min_length=1, max_length=200)
    full_name: NonBlankStr = Field(min_length=2, max_length=150)
    phone: str = Field(min_length=6, max_length=30)
    role: str = Field(default="customer", pattern="^(customer|technician)$")
    department_id: uuid.UUID
    province_id: uuid.UUID
    district_id: uuid.UUID
    address: str | None = Field(default=None, max_length=255)
    offers_home_service: bool = True
    offers_workshop_service: bool = False
    workshop_address: str | None = Field(default=None, max_length=255)
    accept_terms: bool

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return _normalize_phone_or_error(value)

    @field_validator("accept_terms")
    @classmethod
    def validate_accept_terms(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Debes aceptar los Términos y Condiciones")
        return value

    @field_validator("address", "workshop_address")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None
