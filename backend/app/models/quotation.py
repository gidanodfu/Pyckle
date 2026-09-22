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
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import QuotationStatus

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.repair import RepairRequest
    from app.models.technician import Technician


class Quotation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "quotations"
    __table_args__ = (
        UniqueConstraint("request_id", "technician_id", name="uq_quotations_request_technician"),
    )

    request_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repair_requests.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    technician_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("technicians.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    preliminary_diagnosis: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_days: Mapped[int] = mapped_column(
        Integer, default=1, server_default="1", nullable=False
    )
    status: Mapped[QuotationStatus] = mapped_column(
        Enum(
            QuotationStatus,
            native_enum=False,
            values_callable=lambda cls: [e.value for e in cls],
            length=20,
            create_constraint=True,
            name="quotation_status",
        ),
        default=QuotationStatus.PENDING,
        index=True,
        nullable=False,
    )
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    request: Mapped[RepairRequest] = relationship(back_populates="quotations")
    technician: Mapped[Technician] = relationship(foreign_keys=[technician_id])
    items: Mapped[list[QuotationItem]] = relationship(
        back_populates="quotation", cascade="all, delete-orphan", lazy="selectin"
    )
    order: Mapped[Order | None] = relationship(back_populates="quotation", uselist=False)


class QuotationItem(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "quotation_items"

    quotation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    quotation: Mapped[Quotation] = relationship(back_populates="items")
