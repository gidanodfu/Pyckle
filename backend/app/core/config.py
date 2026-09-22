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

import ipaddress
import re
from functools import lru_cache
from urllib.parse import urlsplit

from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_SECRET_KEYS = frozenset(
    {
        "",
        "dev-insecure-secret-change-me",
        # Placeholder publico de .env.example: nunca debe arrancar produccion.
        "replace-with-openssl-rand-hex-32",
    }
)
MIN_SECRET_KEY_LENGTH = 32
ALLOWED_JWT_ALGORITHMS = frozenset({"HS256", "HS384", "HS512"})
MIN_ADMIN_PASSWORD_LENGTH = 12
# Placeholders públicos (.env.example) y contraseñas débiles conocidas.
INSECURE_PASSWORDS = frozenset(
    {
        "",
        "replace-strong-admin-password",
        "replace-demo-password",
        "changeme",
        "admin",
        "admin123",
        "password",
        "password123",
    }
)

_HOST_LABEL = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


def _is_http_url(value: str, *, allow_path: bool = False) -> bool:
    if not value:
        return False
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return False
    if allow_path:
        return not parts.query and not parts.fragment
    if parts.path not in {"", "/"} or parts.query or parts.fragment:
        return False
    return True


def _is_hostname(value: str) -> bool:
    value = value.strip()
    if not value:
        return False
    if any(char in value for char in ("/", ":", " ")):
        return False
    host = value[2:] if value.startswith("*.") else value
    if not host or "*" in host:
        return False
    return all(bool(_HOST_LABEL.match(label)) for label in host.split("."))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Aplicacion
    app_name: str = "Pyckle"
    environment: str = "development"
    debug: bool = True
    secret_key: str = "dev-insecure-secret-change-me"
    api_v1_prefix: str = "/api/v1"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173"
    trusted_hosts: str = "localhost,127.0.0.1"
    # Proxies de confianza (IP/CIDR) de los que se acepta X-Real-IP. Fuera de
    # estos rangos el header es ignorado y se usa la IP de la conexión directa.
    trusted_proxies: str = ""
    frontend_url: str = "http://localhost:5173"

    # JWT
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Base de datos
    database_url: str = "postgresql+asyncpg://pyckle:pyckle@postgres:5432/pyckle"
    test_database_url: str | None = None
    # Pool: el máximo de conexiones es workers * (db_pool_size + db_max_overflow).
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800

    # Rate limit de login
    login_max_attempts: int = 3
    login_block_seconds: int = 300

    # Rate limit de registro (alta de cuentas, por IP confiable)
    register_max_per_ip: int = 20
    register_window_seconds: int = 3600

    # Redis
    redis_url: str = "redis://redis:6379/0"

    # Almacenamiento
    storage_backend: str = "local"
    storage_local_dir: str = "/app/media"
    supabase_s3_endpoint: str | None = None
    supabase_s3_region: str | None = None
    supabase_s3_access_key_id: str | None = None
    supabase_s3_secret_access_key: str | None = None
    supabase_s3_bucket: str = "pyckle"

    # Subidas
    max_upload_size_mb: int = 5
    max_images_per_request: int = 6
    allowed_image_types: str = "image/jpeg,image/png,image/webp"

    # Seed
    admin_email: str = "admin@pyckle.dev"
    admin_password: str | None = None
    demo_password: str | None = None
    seed_demo_data: bool = False

    # OAuth con Google (server-side; el frontend nunca ve estas credenciales)
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"
    # Ventana maxima para completar el onboarding de una cuenta iniciada con
    # Google (el usuario ya autentico pero aun no crea su User local).
    oauth_onboarding_ttl_seconds: int = 120

    # Despliegue
    domain: str = "fix.example.com"

    @property
    def cors_origins_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def trusted_hosts_list(self) -> list[str]:
        return [item.strip() for item in self.trusted_hosts.split(",") if item.strip()]

    @property
    def trusted_proxies_list(self) -> list[str]:
        return [item.strip() for item in self.trusted_proxies.split(",") if item.strip()]

    @property
    def allowed_image_types_list(self) -> list[str]:
        return [item.strip() for item in self.allowed_image_types.split(",") if item.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    def ensure_production_ready(self) -> None:
        """Falla el arranque en produccion si la configuracion es insegura.

        Valida semánticamente cada variable crítica. No expone valores, solo el
        nombre de la variable que debe corregirse.
        """
        if not self.is_production:
            return

        if self.secret_key in INSECURE_SECRET_KEYS or len(self.secret_key) < MIN_SECRET_KEY_LENGTH:
            raise RuntimeError(
                "Configuración de producción inválida: SECRET_KEY debe ser una clave "
                "aleatoria de al menos 32 caracteres (p.ej. `openssl rand -hex 32`)."
            )

        if self.jwt_algorithm not in ALLOWED_JWT_ALGORITHMS:
            raise RuntimeError(
                "Configuración de producción inválida: JWT_ALGORITHM debe ser HS256, HS384 o HS512"
            )

        # La cuenta administradora se crea con el seed; en producción es
        # obligatoria una contraseña fuerte (nunca el placeholder público).
        if not self.admin_password:
            raise RuntimeError(
                "Configuración de producción inválida: ADMIN_PASSWORD es obligatorio"
            )
        if (
            self.admin_password in INSECURE_PASSWORDS
            or len(self.admin_password) < MIN_ADMIN_PASSWORD_LENGTH
        ):
            raise RuntimeError(
                "Configuración de producción inválida: ADMIN_PASSWORD es débil o es un "
                f"placeholder público (mínimo {MIN_ADMIN_PASSWORD_LENGTH} caracteres)"
            )
        if self.demo_password and (
            self.demo_password in INSECURE_PASSWORDS
            or len(self.demo_password) < MIN_ADMIN_PASSWORD_LENGTH
        ):
            raise RuntimeError(
                "Configuración de producción inválida: DEMO_PASSWORD es débil o es un "
                "placeholder público"
            )

        if self.seed_demo_data:
            raise RuntimeError(
                "Configuración de producción inválida: SEED_DEMO_DATA no puede estar "
                "activo en producción (crearía cuentas demo conocidas)"
            )

        for proxy in self.trusted_proxies_list:
            try:
                ipaddress.ip_network(proxy, strict=False)
            except ValueError as exc:
                raise RuntimeError(
                    "Configuración de producción inválida: TRUSTED_PROXIES contiene "
                    "una IP/CIDR no válida"
                ) from exc

        origins = self.cors_origins_list
        if not origins:
            raise RuntimeError("Configuración de producción inválida: CORS_ORIGINS está vacía")
        if "*" in origins:
            raise RuntimeError(
                "Configuración de producción inválida: CORS_ORIGINS no admite '*' con credenciales"
            )
        if any(not _is_http_url(origin) for origin in origins):
            raise RuntimeError(
                "Configuración de producción inválida: CORS_ORIGINS contiene un origen malformado"
            )

        hosts = self.trusted_hosts_list
        if not hosts:
            raise RuntimeError("Configuración de producción inválida: TRUSTED_HOSTS está vacía")
        if any(not _is_hostname(host) for host in hosts):
            raise RuntimeError(
                "Configuración de producción inválida: TRUSTED_HOSTS contiene un host no válido"
            )

        if not _is_http_url(self.frontend_url):
            raise RuntimeError(
                "Configuración de producción inválida: FRONTEND_URL no es una URL válida"
            )
        if not _is_hostname(self.domain) or self.domain == "fix.example.com":
            raise RuntimeError(
                "Configuración de producción inválida: DOMAIN no es un dominio válido"
            )

        if not self.database_url or not self.database_url.startswith("postgresql+asyncpg://"):
            raise RuntimeError(
                "Configuración de producción inválida: DATABASE_URL debe usar postgresql+asyncpg"
            )
        if not self.redis_url or urlsplit(self.redis_url).scheme not in {"redis", "rediss"}:
            raise RuntimeError("Configuración de producción inválida: REDIS_URL no es válida")

        # En producción el almacenamiento local no es válido: varias instancias
        # en hosts/contenedores distintos no comparten /app/media.
        if self.storage_backend != "s3":
            raise RuntimeError(
                "Configuración de producción inválida: STORAGE_BACKEND debe ser 's3'; "
                "el almacenamiento local no es válido para múltiples instancias "
                "(configura SUPABASE_S3_* y STORAGE_BACKEND=s3)"
            )
        if not self.s3_configured:
            raise RuntimeError(
                "Configuración de producción inválida: faltan parámetros SUPABASE_S3_*"
            )
        if not _is_http_url(self.supabase_s3_endpoint or "", allow_path=True):
            raise RuntimeError(
                "Configuración de producción inválida: SUPABASE_S3_ENDPOINT no es una URL válida"
            )

        if not self.allowed_image_types_list:
            raise RuntimeError(
                "Configuración de producción inválida: ALLOWED_IMAGE_TYPES está vacía"
            )

        partial_google = bool(self.google_client_id) != bool(self.google_client_secret)
        if partial_google:
            raise RuntimeError(
                "Configuración de producción inválida: define GOOGLE_CLIENT_ID y "
                "GOOGLE_CLIENT_SECRET juntos, o ninguno"
            )
        if self.google_oauth_enabled and not _is_http_url(
            self.google_redirect_uri, allow_path=True
        ):
            raise RuntimeError(
                "Configuración de producción inválida: GOOGLE_REDIRECT_URI no es una URL válida"
            )
        if self.oauth_onboarding_ttl_seconds <= 0:
            raise RuntimeError(
                "Configuración de producción inválida: "
                "OAUTH_ONBOARDING_TTL_SECONDS debe ser mayor que cero"
            )
        if self.register_max_per_ip <= 0 or self.register_window_seconds <= 0:
            raise RuntimeError(
                "Configuración de producción inválida: REGISTER_MAX_PER_IP y "
                "REGISTER_WINDOW_SECONDS deben ser mayores que cero"
            )

    @property
    def google_oauth_enabled(self) -> bool:
        return bool(self.google_client_id and self.google_client_secret)

    @property
    def s3_configured(self) -> bool:
        return all(
            [
                self.supabase_s3_endpoint,
                self.supabase_s3_access_key_id,
                self.supabase_s3_secret_access_key,
                self.supabase_s3_bucket,
            ]
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
