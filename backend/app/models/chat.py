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
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import ConversationStatus

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.repair import RepairRequest
    from app.models.technician import Technician
    from app.models.user import User


class Conversation(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint("request_id", "technician_id", name="uq_conversations_request_technician"),
    )

    request_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repair_requests.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    customer_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    technician_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("technicians.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    order_id: Mapped[UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), unique=True
    )
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(
            ConversationStatus,
            native_enum=False,
            values_callable=lambda cls: [e.value for e in cls],
            length=20,
            create_constraint=True,
            name="conversation_status",
        ),
        default=ConversationStatus.OPEN,
        server_default=ConversationStatus.OPEN.value,
        index=True,
        nullable=False,
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    request: Mapped[RepairRequest] = relationship(foreign_keys=[request_id])
    customer: Mapped[User] = relationship(foreign_keys=[customer_id])
    technician: Mapped[Technician] = relationship(foreign_keys=[technician_id])
    order: Mapped[Order | None] = relationship(back_populates="conversation")
    messages: Mapped[list[Message]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_conversation_created_at", "conversation_id", "created_at"),
    )

    conversation_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    sender_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
    sender: Mapped[User] = relationship(foreign_keys=[sender_id])
