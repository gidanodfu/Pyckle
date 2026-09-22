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

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import Modality, RequestStatus

if TYPE_CHECKING:
    from app.models.geo import Department, District, Province
    from app.models.order import Order
    from app.models.quotation import Quotation
    from app.models.technician import Specialty, Technician
    from app.models.user import User


class RepairRequest(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "repair_requests"
    __table_args__ = (Index("ix_repair_requests_status_created_at", "status", "created_at"),)

    customer_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    assigned_technician_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("technicians.id", ondelete="SET NULL"), index=True
    )
    specialty_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("specialties.id", ondelete="SET NULL"), index=True
    )

    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Dirección de servicio: privada hasta que el cliente acepta la cotización.
    address: Mapped[str | None] = mapped_column(String(255))
    # Snapshot legado de la ubicación (fuente de verdad: department_id/province_id/district_id).
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
    modality: Mapped[Modality] = mapped_column(
        Enum(
            Modality,
            native_enum=False,
            values_callable=lambda cls: [e.value for e in cls],
            length=20,
            create_constraint=True,
            name="modality",
        ),
        default=Modality.HOME,
        nullable=False,
    )
    status: Mapped[RequestStatus] = mapped_column(
        Enum(
            RequestStatus,
            native_enum=False,
            values_callable=lambda cls: [e.value for e in cls],
            length=20,
            create_constraint=True,
            name="request_status",
        ),
        default=RequestStatus.OPEN,
        index=True,
        nullable=False,
    )
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    preferred_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    customer: Mapped[User] = relationship(foreign_keys=[customer_id])
    assigned_technician: Mapped[Technician | None] = relationship(
        foreign_keys=[assigned_technician_id]
    )
    specialty: Mapped[Specialty | None] = relationship(foreign_keys=[specialty_id])
    department: Mapped[Department | None] = relationship(foreign_keys=[department_id])
    province: Mapped[Province | None] = relationship(foreign_keys=[province_id])
    district_geo: Mapped[District | None] = relationship(foreign_keys=[district_id])
    images: Mapped[list[RepairRequestImage]] = relationship(
        back_populates="request", cascade="all, delete-orphan", lazy="selectin"
    )
    quotations: Mapped[list[Quotation]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )
    order: Mapped[Order | None] = relationship(back_populates="request", uselist=False)

    @property
    def specialty_name(self) -> str | None:
        return self.specialty.name if self.specialty else None

    @property
    def department_name(self) -> str | None:
        return self.department.name if self.department else None

    @property
    def province_name(self) -> str | None:
        return self.province.name if self.province else None

    @property
    def district_name(self) -> str | None:
        return self.district_geo.name if self.district_geo else None


class RepairRequestImage(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "repair_request_images"

    request_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repair_requests.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # Solo se guarda la clave del objeto; la URL publica se construye de forma centralizada.
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(80), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    request: Mapped[RepairRequest] = relationship(back_populates="images")

    @property
    def url(self) -> str:
        from app.core.paths import sign_media_url

        return sign_media_url(self.storage_key)
