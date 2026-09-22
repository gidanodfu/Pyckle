"""Verifica que la migracion inicial de Alembic sube y baja limpiamente.

Usa una base de datos dedicada para no afectar la base de tests funcional.
"""

from __future__ import annotations

import asyncio
import os
from urllib.parse import urlsplit, urlunsplit

import asyncpg
import pytest
from alembic import command
from alembic.config import Config

from tests.conftest import TEST_DATABASE_URL

pytestmark = pytest.mark.asyncio

MIGRATION_DB = "pyckle_migration_test"


def _replace_database(url: str, database: str, *, strip_driver: bool = False) -> str:
    if strip_driver:
        url = url.replace("+asyncpg", "")
    parts = urlsplit(url)
    return urlunsplit(parts._replace(path=f"/{database}"))


async def _create_database(admin_dsn: str, database: str) -> None:
    connection = await asyncpg.connect(admin_dsn)
    if not await connection.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", database):
        await connection.execute(f'CREATE DATABASE "{database}"')
    await connection.close()


async def _drop_database(admin_dsn: str, database: str) -> None:
    connection = await asyncpg.connect(admin_dsn)
    await connection.execute(
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        "WHERE datname = $1 AND pid <> pg_backend_pid()",
        database,
    )
    await connection.execute(f'DROP DATABASE IF EXISTS "{database}"')
    await connection.close()


async def _count_tables(url: str) -> int:
    connection = await asyncpg.connect(url.replace("+asyncpg", ""))
    count = await connection.fetchval(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name <> 'alembic_version'"
    )
    await connection.close()
    return int(count)


async def test_migrations_upgrade_and_downgrade() -> None:
    admin_dsn = _replace_database(TEST_DATABASE_URL, "postgres", strip_driver=True)
    migration_url = _replace_database(TEST_DATABASE_URL, MIGRATION_DB)

    await _create_database(admin_dsn, MIGRATION_DB)
    previous = os.environ.get("ALEMBIC_DATABASE_URL")
    os.environ["ALEMBIC_DATABASE_URL"] = migration_url
    try:
        config = Config("alembic.ini")
        await asyncio.to_thread(command.upgrade, config, "head")
        assert await _count_tables(migration_url) == 26

        await asyncio.to_thread(command.downgrade, config, "base")
        assert await _count_tables(migration_url) == 0

        await asyncio.to_thread(command.upgrade, config, "head")
        assert await _count_tables(migration_url) == 26
    finally:
        if previous is not None:
            os.environ["ALEMBIC_DATABASE_URL"] = previous
        else:
            os.environ.pop("ALEMBIC_DATABASE_URL", None)
        await _drop_database(admin_dsn, MIGRATION_DB)
