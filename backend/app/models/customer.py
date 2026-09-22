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

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.geo import Department, District, Province
    from app.models.user import User


class CustomerProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "customer_profiles"

    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    # Dirección exacta: privada. Solo se revela al técnico autorizado (ver OrderService).
    address: Mapped[str | None] = mapped_column(String(255))
    # Snapshot legado (fuente de verdad: department_id/province_id/district_id).
    district: Mapped[str | None] = mapped_column(String(120))
    city: Mapped[str] = mapped_column(
        String(120), default="Lima", server_default="Lima", nullable=False
    )
    department_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), index=True
    )
    province_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("provinces.id", ondelete="SET NULL"), index=True
    )
    district_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("districts.id", ondelete="SET NULL"), index=True
    )

    user: Mapped[User] = relationship(back_populates="customer_profile")
    department: Mapped[Department | None] = relationship(foreign_keys=[department_id])
    province: Mapped[Province | None] = relationship(foreign_keys=[province_id])
    district_geo: Mapped[District | None] = relationship(foreign_keys=[district_id])
