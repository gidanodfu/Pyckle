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

"""Proveedor OAuth de Google. Encapsula todas las peculiaridades de Google."""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.parse import urlencode

import httpx
import jwt
from jwt.algorithms import RSAAlgorithm

from app.core.config import Settings, get_settings
from app.domains.auth.oauth.base import OAuthError, OAuthIdentity

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}
JWKS_TTL_SECONDS = 3600


class GoogleOAuthProvider:
    name = "google"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._jwks: dict[str, Any] | None = None
        self._jwks_at = 0.0

    def authorization_url(self, *, state: str, nonce: str, code_challenge: str) -> str:
        params = {
            "client_id": self.settings.google_client_id,
            "redirect_uri": self.settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "access_type": "online",
            "prompt": "select_account",
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, *, code: str, code_verifier: str) -> dict[str, Any]:
        payload = {
            "code": code,
            "client_id": self.settings.google_client_id,
            "client_secret": self.settings.google_client_secret,
            "redirect_uri": self.settings.google_redirect_uri,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(GOOGLE_TOKEN_URL, data=payload)
        if response.status_code != 200:
            raise OAuthError("No se pudo validar la cuenta de Google")
        return response.json()

    async def _get_jwks(self) -> dict[str, Any]:
        # La caché evita consultar el JWKS en cada login; pasado el TTL se
        # vuelve a descargar para recoger rotaciones de claves de Google.
        now = time.time()
        if self._jwks is not None and now - self._jwks_at < JWKS_TTL_SECONDS:
            return self._jwks
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(GOOGLE_JWKS_URL)
        if response.status_code != 200:
            raise OAuthError("No se pudo validar la cuenta de Google")
        self._jwks = response.json()
        self._jwks_at = now
        return self._jwks

    async def get_identity(self, tokens: dict[str, Any], *, nonce: str) -> OAuthIdentity:
        id_token = tokens.get("id_token")
        if not id_token:
            raise OAuthError("Respuesta de Google incompleta")
        jwks = await self._get_jwks()
        try:
            header = jwt.get_unverified_header(id_token)
            key_data = next(
                (key for key in jwks.get("keys", []) if key.get("kid") == header.get("kid")),
                None,
            )
            if key_data is None:
                raise OAuthError("No se pudo verificar la cuenta de Google")
            key = RSAAlgorithm.from_jwk(json.dumps(key_data))
            # Verificación criptográfica completa: firma RS256, audiencia
            # (client_id), emisor y expiración. Decodificar sin validar la
            # firma permitiría aceptar un id_token ajeno.
            claims = jwt.decode(
                id_token,
                key,
                algorithms=["RS256"],
                audience=self.settings.google_client_id,
                issuer=list(GOOGLE_ISSUERS),
            )
        except jwt.PyJWTError as exc:
            raise OAuthError("Token de Google inválido") from exc

        if claims.get("nonce") != nonce:
            raise OAuthError("Nonce de Google inválido")
        email = claims.get("email")
        provider_user_id = claims.get("sub")
        if not provider_user_id or not email:
            raise OAuthError("Identidad de Google incompleta")
        if not claims.get("email_verified"):
            raise OAuthError("El correo de Google no está verificado")
        return OAuthIdentity(
            provider=self.name,
            provider_user_id=str(provider_user_id),
            email=str(email).lower(),
            email_verified=True,
            name=claims.get("name"),
            given_name=claims.get("given_name"),
            family_name=claims.get("family_name"),
            picture=claims.get("picture"),
        )
