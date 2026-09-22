"""Infraestructura de tests: entorno, engine, sesión y constantes."""

from __future__ import annotations

import os
from urllib.parse import urlsplit, urlunsplit

# La configuracion debe fijarse ANTES de importar la app (get_settings esta cacheada).
os.environ["ENVIRONMENT"] = "test"
os.environ["TRUSTED_HOSTS"] = "testserver,localhost,127.0.0.1,backend"
os.environ["SEED_DEMO_DATA"] = "false"
os.environ["STORAGE_BACKEND"] = "local"
os.environ["REDIS_URL"] = "redis://redis:6379/15"
os.environ.setdefault("SECRET_KEY", "test-secret-key-only-for-tests-0123456789")
# Valores deterministas de test: se asignan sin setdefault porque el contenedor
# de desarrollo puede inyectar credenciales reales via .env.dev, lo que haria
# que la suite dependa del entorno local en lugar de ser reproducible.
os.environ["GOOGLE_CLIENT_ID"] = "test-google-client"
os.environ["GOOGLE_CLIENT_SECRET"] = "test-google-secret"
os.environ["GOOGLE_REDIRECT_URI"] = "http://localhost:8000/api/v1/auth/google/callback"
# El cliente de tests se conecta desde 127.0.0.1; se declara proxy de confianza
# para que X-Real-IP se acepte solo desde ese peer.
os.environ["TRUSTED_PROXIES"] = "127.0.0.1,::1"

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

from app.core.config import get_settings  # noqa: E402

get_settings.cache_clear()
settings = get_settings()


def _derive_test_database_url() -> str:
    """Usa TEST_DATABASE_URL o deriva ``<db>_test`` para no tocar la base de la app."""
    if settings.test_database_url:
        return settings.test_database_url
    parts = urlsplit(settings.database_url.replace("+asyncpg", ""))
    database = parts.path.lstrip("/")
    derived = urlunsplit(parts._replace(path=f"/{database}_test"))
    return derived.replace("postgresql://", "postgresql+asyncpg://", 1)


async def _admin_dsn(url: str) -> tuple[str, str]:
    parts = urlsplit(url.replace("+asyncpg", ""))
    database = parts.path.lstrip("/")
    admin = urlunsplit(parts._replace(path="/postgres"))
    return admin, database


TEST_DATABASE_URL = _derive_test_database_url()
if TEST_DATABASE_URL == settings.database_url and settings.is_production:
    raise RuntimeError("TEST_DATABASE_URL debe apuntar a una base distinta a la de la aplicacion")
os.environ["ALEMBIC_DATABASE_URL"] = TEST_DATABASE_URL

test_engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)

DATA_TABLES = [
    "order_events",
    "order_price_changes",
    "order_cost_items",
    "repair_reports",
    "messages",
    "conversations",
    "reviews",
    "orders",
    "quotation_items",
    "quotations",
    "repair_request_images",
    "repair_requests",
    "technicians",
    "customer_profiles",
    "notifications",
    "oauth_accounts",
    "user_roles",
    "users",
]

CUSTOMER_EMAIL = "customer@test.dev"
TECHNICIAN_EMAIL = "technician@test.dev"
ADMIN_EMAIL = "admin@test.dev"
PASSWORD = "password12345"
