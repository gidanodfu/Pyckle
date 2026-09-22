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

"""Seed de datos demo (logica).

Los literales viven en `app.db.demo_data`; aqui esta la logica de siembra
idempotente de clientes, tecnicos, ordenes completadas y solicitudes abiertas.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.security import hash_password
from app.db.demo_data import (
    DEMO_COMPLETED,
    DEMO_CUSTOMERS,
    DEMO_OPEN,
    DEMO_TECHNICIANS,
)
from app.db.demo_data_lifecycle import DEMO_LIFECYCLE
from app.db.demo_helpers import (
    _ensure_completed_flow,
    _ensure_customer_profile,
    _ensure_lifecycle_repair,
    _ensure_open_request,
    _ensure_report,
    _ensure_technician,
    _get_or_create_demo_user,
    _location_context,
    _refresh_technician_rating,
    district_by_code,
)
from app.models.enums import Modality, QuotationStatus, RepairStatus, RequestStatus, RoleName
from app.models.quotation import Quotation
from app.models.repair import RepairRequest
from app.models.technician import Specialty, Technician
from app.models.user import Role, User

settings = get_settings()
logger = get_logger("seed")


async def seed_demo(session, specialties: list[Specialty]) -> None:
    if not settings.demo_password:
        logger.warning("DEMO_PASSWORD no definido: se omite la data demo")
        return
    customer_role = (
        await session.execute(select(Role).where(Role.name == RoleName.CUSTOMER.value))
    ).scalar_one()
    technician_role = (
        await session.execute(select(Role).where(Role.name == RoleName.TECHNICIAN.value))
    ).scalar_one()
    password_hash = hash_password(settings.demo_password)
    specialty_by_slug = {specialty.slug: specialty for specialty in specialties}

    # --- Datos demo minimos de compatibilidad ------------------------------
    jlo = await district_by_code(session, "140105")
    jlo_location = await _location_context(session, jlo)
    legacy_customer = (
        await session.execute(select(User).where(User.email == "cliente@pyckle.dev"))
    ).scalar_one_or_none()
    if legacy_customer is None:
        legacy_customer = User(
            email="cliente@pyckle.dev",
            hashed_password=password_hash,
            full_name="Cliente Demo",
            phone="+51900000001",
            phone_normalized="+51900000001",
            terms_accepted_at=datetime.now(UTC),
        )
        legacy_customer.roles.append(customer_role)
        session.add(legacy_customer)
        await session.flush()
        await _ensure_customer_profile(
            session, legacy_customer, jlo_location, "Av. Balta 123, José Leonardo Ortiz"
        )
    legacy_technician_user = (
        await session.execute(select(User).where(User.email == "tecnico@pyckle.dev"))
    ).scalar_one_or_none()
    if legacy_technician_user is None:
        legacy_technician_user = User(
            email="tecnico@pyckle.dev",
            hashed_password=password_hash,
            full_name="Técnico Demo",
            phone="+51900000002",
            phone_normalized="+51900000002",
            terms_accepted_at=datetime.now(UTC),
        )
        legacy_technician_user.roles.append(technician_role)
        session.add(legacy_technician_user)
        await session.flush()
        legacy_technician = Technician(
            user_id=legacy_technician_user.id,
            bio="Técnico con 8 años de experiencia en laptops y PCs.",
            experience_years=8,
            is_verified=True,
            offers_home_service=True,
            offers_workshop_service=True,
            workshop_address="Av. Chiclayo 456, José Leonardo Ortiz",
            department_id=jlo_location["department_id"],
            province_id=jlo_location["province_id"],
            district_id=jlo_location["district_id"],
        )
        legacy_technician.specialties.append(specialties[0])
        session.add(legacy_technician)
        await session.flush()
    else:
        legacy_technician = (
            await session.execute(
                select(Technician).where(Technician.user_id == legacy_technician_user.id)
            )
        ).scalar_one()
    legacy_request = (
        await session.execute(
            select(RepairRequest).where(RepairRequest.title == "Laptop no enciende")
        )
    ).scalar_one_or_none()
    if legacy_request is None:
        legacy_request = RepairRequest(
            customer_id=legacy_customer.id,
            specialty_id=specialties[0].id,
            title="Laptop no enciende",
            description="Mi laptop Lenovo no enciende desde ayer, la luz de carga parpadea.",
            address="Av. Balta 123, José Leonardo Ortiz",
            district=jlo_location["district"],
            city=jlo_location["city"],
            department_id=jlo_location["department_id"],
            province_id=jlo_location["province_id"],
            district_id=jlo_location["district_id"],
            modality=Modality.HOME,
            status=RequestStatus.OPEN,
        )
        session.add(legacy_request)
        await session.flush()
        session.add(
            Quotation(
                request_id=legacy_request.id,
                technician_id=legacy_technician.id,
                price=180,
                preliminary_diagnosis="Posible falla en la placa de carga o batería agotada.",
                estimated_days=2,
                status=QuotationStatus.PENDING,
            )
        )

    # --- Clientes y tecnicos distribuidos ----------------------------------
    customers: dict[str, tuple[User, dict, str]] = {}
    for number, name, code, address in DEMO_CUSTOMERS:
        district = await district_by_code(session, code)
        location = await _location_context(session, district)
        user = await _get_or_create_demo_user(
            session,
            email=f"demo.customer.{number}@pyckle.dev",
            full_name=name,
            phone=f"+519100000{number}",
            password_hash=password_hash,
            role=customer_role,
        )
        await _ensure_customer_profile(session, user, location, address)
        customers[number] = (user, location, address)

    technicians: dict[str, Technician] = {}
    technician_locations: dict[str, dict] = {}
    for spec in DEMO_TECHNICIANS:
        district = await district_by_code(session, spec["district"])
        location = await _location_context(session, district)
        user = await _get_or_create_demo_user(
            session,
            email=f"demo.technician.{spec['id']}@pyckle.dev",
            full_name=spec["name"],
            phone=f"+519200000{spec['id']}",
            password_hash=password_hash,
            role=technician_role,
        )
        technicians[spec["id"]] = await _ensure_technician(
            session, user, location, spec, specialty_by_slug
        )
        technician_locations[spec["id"]] = location

    # --- Ordenes completadas con resenas -----------------------------------
    report_targets: list[tuple[object, object]] = []
    for tech_id, customer_id, slug, title, price, rating, comment in DEMO_COMPLETED:
        customer, customer_location, _ = customers[customer_id]
        order = await _ensure_completed_flow(
            session,
            customer=customer,
            technician=technicians[tech_id],
            specialty=specialty_by_slug[slug],
            title=title,
            price=price,
            rating=rating,
            comment=comment,
            location=customer_location,
        )
        report_targets.append((order, technicians[tech_id].user_id))
    for technician in technicians.values():
        await _refresh_technician_rating(session, technician)

    # --- Reparaciones en distintos estados del ciclo tecnico ---------------
    lifecycle = DEMO_LIFECYCLE
    for customer_id, tech_id, slug, title, status, price, result, change in lifecycle:
        customer, customer_location, _ = customers[customer_id]
        order = await _ensure_lifecycle_repair(
            session,
            customer=customer,
            technician=technicians[tech_id],
            specialty=specialty_by_slug[slug],
            title=title,
            status=RepairStatus(status),
            price=price,
            location=customer_location,
            result=result,
            price_change=change,
        )
        if order is not None and result is not None:
            report_targets.append((order, technicians[tech_id].user_id))
    for order, actor_id in report_targets:
        await _ensure_report(session, order, actor_id)

    # --- Solicitudes abiertas con cotizacion pendiente ---------------------
    for customer_id, slug, title, description, price, tech_id, home in DEMO_OPEN:
        customer, customer_location, address = customers[customer_id]
        await _ensure_open_request(
            session,
            customer=customer,
            technician=technicians[tech_id],
            specialty=specialty_by_slug[slug],
            title=title,
            description=description,
            price=price,
            location=customer_location,
            address=address if home else None,
            modality=Modality.HOME if home else Modality.WORKSHOP,
        )

    await session.commit()
    verified = sum(1 for technician in technicians.values() if technician.is_verified)
    logger.info(
        "Data demo lista: %d clientes, %d tecnicos (%d verificados), "
        "%d ordenes completadas, %d solicitudes abiertas",
        len(customers),
        len(technicians),
        verified,
        len(DEMO_COMPLETED),
        len(DEMO_OPEN),
    )
