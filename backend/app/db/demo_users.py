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

"""Helpers del seed demo (logica reutilizable)."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models.customer import CustomerProfile
from app.models.review import Review
from app.models.technician import Technician
from app.models.user import Role, User


async def _get_or_create_demo_user(
    session, *, email: str, full_name: str, phone: str, password_hash: str, role: Role
) -> User:
    user = (await session.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is not None:
        return user
    user = User(
        email=email,
        hashed_password=password_hash,
        full_name=full_name,
        phone=phone,
        phone_normalized=phone,
        terms_accepted_at=datetime.now(UTC),
    )
    user.roles.append(role)
    session.add(user)
    await session.flush()
    return user


async def _ensure_customer_profile(session, user: User, location: dict, address: str) -> None:
    existing = (
        await session.execute(select(CustomerProfile).where(CustomerProfile.user_id == user.id))
    ).scalar_one_or_none()
    if existing is not None:
        return
    session.add(
        CustomerProfile(
            user_id=user.id,
            address=address,
            district=location["district"],
            city=location["city"],
            department_id=location["department_id"],
            province_id=location["province_id"],
            district_id=location["district_id"],
        )
    )
    await session.flush()


async def _ensure_technician(
    session, user: User, location: dict, spec: dict, specialty_by_slug: dict
) -> Technician:
    technician = (
        await session.execute(
            select(Technician)
            .options(selectinload(Technician.specialties))
            .where(Technician.user_id == user.id)
        )
    ).scalar_one_or_none()
    if technician is None:
        technician = Technician(
            user_id=user.id,
            bio=(
                f"Técnico con {spec['experience']} años de experiencia "
                "en reparación de dispositivos."
            ),
            experience_years=spec["experience"],
            is_verified=spec["verified"],
            offers_home_service=spec["home"],
            offers_workshop_service=spec["workshop"],
            workshop_address=spec["workshop_address"],
            department_id=location["department_id"],
            province_id=location["province_id"],
            district_id=location["district_id"],
        )
        technician.specialties = [specialty_by_slug[slug] for slug in spec["specialties"]]
        session.add(technician)
        await session.flush()
    elif not technician.specialties:
        technician.specialties = [specialty_by_slug[slug] for slug in spec["specialties"]]
    return technician


async def _refresh_technician_rating(session, technician: Technician) -> None:
    average, count = (
        await session.execute(
            select(func.avg(Review.rating), func.count(Review.id)).where(
                Review.technician_id == technician.id
            )
        )
    ).one()
    technician.rating_avg = (
        Decimal(str(round(float(average), 2))) if average is not None else Decimal("0.00")
    )
    technician.rating_count = int(count or 0)
