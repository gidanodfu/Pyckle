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

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    true,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.geo import Department, District, Province
    from app.models.user import User

technician_specialties = Table(
    "technician_specialties",
    Base.metadata,
    Column(
        "technician_id",
        UUID(as_uuid=True),
        ForeignKey("technicians.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "specialty_id",
        UUID(as_uuid=True),
        ForeignKey("specialties.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Specialty(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "specialties"

    name: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default=true(), default=True, nullable=False
    )

    technicians: Mapped[list[Technician]] = relationship(
        secondary=technician_specialties, back_populates="specialties"
    )


class Technician(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "technicians"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    bio: Mapped[str | None] = mapped_column(Text)
    experience_years: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    offers_home_service: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=true(), nullable=False
    )
    offers_workshop_service: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    workshop_address: Mapped[str | None] = mapped_column(String(255))
    department_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), index=True
    )
    province_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("provinces.id", ondelete="SET NULL"), index=True
    )
    district_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("districts.id", ondelete="SET NULL"), index=True
    )
    rating_avg: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), default=Decimal("0.00"), server_default="0.00", nullable=False
    )
    rating_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )

    user: Mapped[User] = relationship(back_populates="technician_profile")
    specialties: Mapped[list[Specialty]] = relationship(
        secondary=technician_specialties, back_populates="technicians", lazy="selectin"
    )
    department: Mapped[Department | None] = relationship(foreign_keys=[department_id])
    province: Mapped[Province | None] = relationship(foreign_keys=[province_id])
    district_geo: Mapped[District | None] = relationship(foreign_keys=[district_id])

    @property
    def full_name(self) -> str:
        return self.user.full_name if self.user else ""

    @property
    def email(self) -> str:
        return self.user.email if self.user else ""

    @property
    def department_name(self) -> str | None:
        return self.department.name if self.department else None

    @property
    def province_name(self) -> str | None:
        return self.province.name if self.province else None

    @property
    def district_name(self) -> str | None:
        return self.district_geo.name if self.district_geo else None
