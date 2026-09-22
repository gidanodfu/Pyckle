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

"""Datos semilla.

Uso:
    python -m app.db.seed

Crea roles, permisos, especialidades, la geografía del Perú (departamentos,
provincias y distritos) y el usuario administrador. Con SEED_DEMO_DATA=true crea
además datos demo coherentes (clientes, técnicos verificados y no verificados,
solicitudes, cotizaciones, órdenes completadas y reseñas) distribuidos en varias
zonas del Perú. La convención de correos demo es
``demo.customer.NNN@pyckle.dev`` / ``demo.technician.NNN@pyckle.dev``.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.core.security import hash_password
from app.core.text import slugify
from app.db.demo_seed import seed_demo
from app.db.session import SessionLocal
from app.models.enums import PermissionCode, RoleName
from app.models.geo import Department, District, Province
from app.models.technician import Specialty
from app.models.user import Permission, Role, User

settings = get_settings()
logger = get_logger("seed")

GEO_DATA_PATH = Path(__file__).parent / "data" / "ubigeo_peru.json"

ALL_PERMISSIONS = list(PermissionCode)

ROLE_PERMISSIONS: dict[RoleName, list[PermissionCode]] = {
    RoleName.CUSTOMER: [
        PermissionCode.REPAIR_REQUEST_CREATE,
        PermissionCode.REPAIR_REQUEST_READ_OWN,
        PermissionCode.QUOTATION_READ,
        PermissionCode.ORDER_READ_OWN,
        PermissionCode.CHAT_PARTICIPATE,
        PermissionCode.REVIEW_CREATE,
    ],
    RoleName.TECHNICIAN: [
        PermissionCode.REPAIR_REQUEST_READ_AVAILABLE,
        PermissionCode.QUOTATION_CREATE,
        PermissionCode.QUOTATION_READ,
        PermissionCode.ORDER_MANAGE_ASSIGNED,
        PermissionCode.ORDER_READ_OWN,
        PermissionCode.CHAT_PARTICIPATE,
    ],
    # El administrador no participa en el chat: no recibe CHAT_PARTICIPATE,
    # aunque conserve el resto de permisos administrativos.
    RoleName.ADMIN: [code for code in ALL_PERMISSIONS if code != PermissionCode.CHAT_PARTICIPATE],
}

SPECIALTIES = [
    ("Laptops", "Reparación y mantenimiento de laptops y notebooks"),
    ("Celulares", "Reparación de smartphones y teléfonos"),
    ("Tablets", "Reparación de tablets y iPads"),
    ("Computadoras de escritorio", "Armado, mantenimiento y reparación de PCs"),
    ("Consolas", "Reparación de consolas de videojuegos"),
    ("Impresoras", "Mantenimiento y reparación de impresoras"),
    ("Televisores", "Reparación de televisores y monitores"),
]


async def seed_roles(session) -> None:
    existing_permissions = {
        p.code: p for p in (await session.execute(select(Permission))).scalars().all()
    }
    for code in ALL_PERMISSIONS:
        if code.value not in existing_permissions:
            permission = Permission(
                code=code.value, description=code.name.replace("_", " ").title()
            )
            session.add(permission)
            existing_permissions[code.value] = permission
    await session.flush()

    for role_name, codes in ROLE_PERMISSIONS.items():
        role = (
            await session.execute(
                select(Role)
                .options(selectinload(Role.permissions))
                .where(Role.name == role_name.value)
            )
        ).scalar_one_or_none()
        if role is None:
            role = Role(name=role_name.value, description=role_name.name.title())
            session.add(role)
        role.permissions = [existing_permissions[code.value] for code in codes]
    await session.commit()
    logger.info("Roles y permisos listos")


async def seed_specialties(session) -> list[Specialty]:
    result: list[Specialty] = []
    for name, description in SPECIALTIES:
        slug = slugify(name)
        specialty = (
            await session.execute(select(Specialty).where(Specialty.slug == slug))
        ).scalar_one_or_none()
        if specialty is None:
            specialty = Specialty(name=name, slug=slug, description=description)
            session.add(specialty)
            await session.flush()
        result.append(specialty)
    await session.commit()
    logger.info("Especialidades listas: %d", len(result))
    return result


async def seed_geo(session) -> None:
    """Carga el ubigeo del Perú de forma idempotente desde el JSON vendorizado."""
    data = json.loads(GEO_DATA_PATH.read_text(encoding="utf-8"))

    departments = {
        item.code: item for item in (await session.execute(select(Department))).scalars().all()
    }
    for row in data["departments"]:
        if row["code"] not in departments:
            department = Department(code=row["code"], name=row["name"])
            session.add(department)
            departments[row["code"]] = department
    await session.flush()

    provinces = {
        item.code: item for item in (await session.execute(select(Province))).scalars().all()
    }
    for row in data["provinces"]:
        if row["code"] not in provinces:
            province = Province(
                code=row["code"],
                name=row["name"],
                department_id=departments[row["department_code"]].id,
            )
            session.add(province)
            provinces[row["code"]] = province
    await session.flush()

    districts = {
        item.code: item for item in (await session.execute(select(District))).scalars().all()
    }
    for row in data["districts"]:
        if row["code"] not in districts:
            session.add(
                District(
                    code=row["code"],
                    name=row["name"],
                    province_id=provinces[row["province_code"]].id,
                    department_id=departments[row["department_code"]].id,
                )
            )
    await session.commit()
    logger.info(
        "Geografía lista: %d departamentos, %d provincias, %d distritos",
        len(data["departments"]),
        len(data["provinces"]),
        len(data["districts"]),
    )


async def seed_admin(session) -> None:
    if not settings.admin_password:
        logger.warning("ADMIN_PASSWORD no definido: se omite la creación del administrador")
        return
    existing = (
        await session.execute(select(User).where(User.email == settings.admin_email.lower()))
    ).scalar_one_or_none()
    if existing is not None:
        logger.info("El administrador ya existe: %s", settings.admin_email)
        return
    role = (
        await session.execute(select(Role).where(Role.name == RoleName.ADMIN.value))
    ).scalar_one()
    admin = User(
        email=settings.admin_email.lower(),
        hashed_password=hash_password(settings.admin_password),
        full_name="Administrador Pyckle",
        is_verified=True,
    )
    admin.roles.append(role)
    session.add(admin)
    await session.commit()
    logger.info("Administrador creado: %s", settings.admin_email)


async def main() -> None:
    setup_logging()
    if settings.seed_demo_data and settings.is_production:
        # Falla cerrado: el seed CLI no debe crear cuentas demo conocidas en prod.
        raise RuntimeError(
            "SEED_DEMO_DATA no puede estar activo en producción; "
            "desactívalo o ejecuta el seed fuera de producción"
        )
    async with SessionLocal() as session:
        await seed_roles(session)
        specialties = await seed_specialties(session)
        await seed_geo(session)
        await seed_admin(session)
        if settings.seed_demo_data:
            await seed_demo(session, specialties)
    logger.info("Seed completado")


if __name__ == "__main__":
    asyncio.run(main())
