"""Fixtures de pytest para la suite de tests."""

from __future__ import annotations

import asyncio

import asyncpg
import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.redis import get_redis
from app.db.session import get_db
from app.main import app
from app.models.enums import RoleName
from tests.helpers import (
    auth_header,
    create_user,
    geo_payload,
    get_district,
    login,
    override_get_db,
    register_payload,
    verify_technician,
)
from tests.infra import (
    ADMIN_EMAIL,
    CUSTOMER_EMAIL,
    DATA_TABLES,
    PASSWORD,
    TECHNICIAN_EMAIL,
    TEST_DATABASE_URL,
    TestSession,
    _admin_dsn,
    test_engine,
)


@pytest.fixture(scope="session", autouse=True)
def prepare_database() -> None:
    async def setup() -> None:
        admin, database = await _admin_dsn(TEST_DATABASE_URL)
        connection = await asyncpg.connect(admin)
        exists = await connection.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", database)
        if not exists:
            await connection.execute(f'CREATE DATABASE "{database}"')
        await connection.close()

    asyncio.run(setup())

    config = Config("alembic.ini")
    command.upgrade(config, "head")

    async def seed_reference() -> None:
        from app.db.seed import seed_geo, seed_roles, seed_specialties

        async with TestSession() as session:
            await seed_roles(session)
            await seed_specialties(session)
            await seed_geo(session)

    asyncio.run(seed_reference())


@pytest_asyncio.fixture(autouse=True)
async def clean_data():
    async with test_engine.begin() as connection:
        await connection.execute(
            text(f"TRUNCATE {', '.join(DATA_TABLES)} RESTART IDENTITY CASCADE")
        )
    await get_redis().flushdb()
    yield


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        yield http_client


@pytest_asyncio.fixture
async def session():
    async with TestSession() as db_session:
        yield db_session


@pytest_asyncio.fixture
async def geo() -> dict[str, str]:
    async with TestSession() as db_session:
        district = await get_district(db_session)
        return geo_payload(district)


@pytest_asyncio.fixture
async def customer_token(client: AsyncClient) -> str:
    await create_user(CUSTOMER_EMAIL, PASSWORD, RoleName.CUSTOMER)
    return (await login(client, CUSTOMER_EMAIL, PASSWORD))["access_token"]


@pytest_asyncio.fixture
async def technician_token(client: AsyncClient) -> str:
    await create_user(TECHNICIAN_EMAIL, PASSWORD, RoleName.TECHNICIAN)
    return (await login(client, TECHNICIAN_EMAIL, PASSWORD))["access_token"]


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient) -> str:
    await create_user(ADMIN_EMAIL, PASSWORD, RoleName.ADMIN)
    return (await login(client, ADMIN_EMAIL, PASSWORD))["access_token"]


@pytest_asyncio.fixture
async def technician_ready(client: AsyncClient, geo: dict[str, str]) -> tuple[str, str]:
    """Técnico registrado por API con perfil, ubicación y una especialidad asignada."""
    email = "tech.ready@test.dev"
    response = await client.post(
        "/api/v1/auth/register",
        json=register_payload(
            geo,
            email=email,
            role="technician",
            phone="+51911111112",
            full_name="Técnico Listo",
        ),
    )
    assert response.status_code == 201, response.text
    token = (await login(client, email, PASSWORD))["access_token"]
    specialty_id = (await client.get("/api/v1/specialties")).json()[0]["id"]
    response = await client.patch(
        "/api/v1/technicians/me",
        headers=auth_header(token),
        json={"specialty_ids": [specialty_id]},
    )
    assert response.status_code == 200, response.text
    await verify_technician(email)
    return token, specialty_id
