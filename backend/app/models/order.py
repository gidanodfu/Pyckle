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
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import (
    CostKind,
    OrderEventType,
    PriceChangeStatus,
    RepairResult,
    RepairStatus,
)

if TYPE_CHECKING:
    from app.models.chat import Conversation
    from app.models.quotation import Quotation
    from app.models.repair import RepairRequest
    from app.models.review import Review
    from app.models.technician import Technician
    from app.models.user import User


def _enum_column(enum_cls, name: str, *, length: int = 30):
    return Enum(
        enum_cls,
        native_enum=False,
        values_callable=lambda cls: [e.value for e in cls],
        length=length,
        create_constraint=False,
        name=name,
    )


class Order(UUIDMixin, TimestampMixin, Base):
    """Orden = reparación aceptada y su proceso técnico."""

    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_customer_status", "customer_id", "status"),
        Index("ix_orders_technician_status", "technician_id", "status"),
    )

    request_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repair_requests.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    quotation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("quotations.id", ondelete="RESTRICT"),
        unique=True,
        nullable=False,
    )
    customer_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    technician_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("technicians.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    status: Mapped[RepairStatus] = mapped_column(
        _enum_column(RepairStatus, "repair_status", length=20),
        default=RepairStatus.AWAITING_RECEIPT,
        index=True,
        nullable=False,
    )
    result: Mapped[RepairResult | None] = mapped_column(
        _enum_column(RepairResult, "repair_result", length=20), index=True
    )
    # Precio efectivamente cobrado al cliente (la cotización inicial es inmutable).
    final_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Proceso técnico.
    diagnosis: Mapped[str | None] = mapped_column(Text)
    work_performed: Mapped[str | None] = mapped_column(Text)
    tests_performed: Mapped[str | None] = mapped_column(Text)
    # Notas internas: nunca se exponen al cliente.
    technician_notes: Mapped[str | None] = mapped_column(Text)
    not_repairable_reason: Mapped[str | None] = mapped_column(Text)

    request: Mapped[RepairRequest] = relationship(back_populates="order")
    quotation: Mapped[Quotation] = relationship(back_populates="order")
    customer: Mapped[User] = relationship(foreign_keys=[customer_id])
    technician: Mapped[Technician] = relationship(foreign_keys=[technician_id])
    events: Mapped[list[OrderEvent]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderEvent.created_at",
    )
    price_changes: Mapped[list[OrderPriceChange]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderPriceChange.created_at",
    )
    cost_items: Mapped[list[OrderCostItem]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderCostItem.created_at",
    )
    reports: Mapped[list[RepairReport]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="RepairReport.version",
    )
    conversation: Mapped[Conversation | None] = relationship(back_populates="order", uselist=False)
    review: Mapped[Review | None] = relationship(back_populates="order", uselist=False)


class OrderEvent(UUIDMixin, TimestampMixin, Base):
    """Historial append-only de una reparación."""

    __tablename__ = "order_events"

    order_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False
    )
    actor_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    event_type: Mapped[OrderEventType] = mapped_column(
        _enum_column(OrderEventType, "order_event_type", length=40),
        default=OrderEventType.NOTE,
        nullable=False,
    )
    old_status: Mapped[RepairStatus | None] = mapped_column(
        _enum_column(RepairStatus, "order_event_old_status", length=30)
    )
    new_status: Mapped[RepairStatus | None] = mapped_column(
        _enum_column(RepairStatus, "order_event_new_status", length=30)
    )
    description: Mapped[str | None] = mapped_column(Text)
    event_metadata: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB)
    visible_to_customer: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False, index=True
    )

    order: Mapped[Order] = relationship(back_populates="events")
    actor: Mapped[User | None] = relationship(foreign_keys=[actor_id])


class OrderPriceChange(UUIDMixin, TimestampMixin, Base):
    """Propuesta de cambio de precio (aumento requiere aprobación del cliente)."""

    __tablename__ = "order_price_changes"

    order_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False
    )
    previous_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    new_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    requested_by: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    status: Mapped[PriceChangeStatus] = mapped_column(
        _enum_column(PriceChangeStatus, "price_change_status", length=20),
        default=PriceChangeStatus.PENDING,
        index=True,
        nullable=False,
    )
    decided_by: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_note: Mapped[str | None] = mapped_column(Text)

    order: Mapped[Order] = relationship(back_populates="price_changes")
    requester: Mapped[User | None] = relationship(foreign_keys=[requested_by])
    decider: Mapped[User | None] = relationship(foreign_keys=[decided_by])


class OrderCostItem(UUIDMixin, TimestampMixin, Base):
    """Línea de costo. ``visible_to_customer`` controla el desglose del cliente."""

    __tablename__ = "order_cost_items"

    order_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[CostKind] = mapped_column(
        _enum_column(CostKind, "cost_kind", length=20),
        default=CostKind.OTHER,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    visible_to_customer: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    created_by: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    order: Mapped[Order] = relationship(back_populates="cost_items")
    creator: Mapped[User | None] = relationship(foreign_keys=[created_by])


class RepairReport(UUIDMixin, TimestampMixin, Base):
    """Informe de reparación persistido (una fila por versión)."""

    __tablename__ = "repair_reports"
    __table_args__ = (
        UniqueConstraint("order_id", "version", name="uq_repair_reports_order_version"),
    )

    order_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1", nullable=False)
    storage_key: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(
        String(80), default="application/pdf", server_default="application/pdf", nullable=False
    )
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_by: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    order: Mapped[Order] = relationship(back_populates="reports")
    generator: Mapped[User | None] = relationship(foreign_keys=[generated_by])
