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

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Department(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "departments"

    code: Mapped[str] = mapped_column(String(2), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)

    provinces: Mapped[list[Province]] = relationship(
        back_populates="department", cascade="all, delete-orphan"
    )


class Province(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "provinces"

    code: Mapped[str] = mapped_column(String(4), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    department_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    department: Mapped[Department] = relationship(back_populates="provinces")
    districts: Mapped[list[District]] = relationship(
        back_populates="province", cascade="all, delete-orphan"
    )


class District(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "districts"

    code: Mapped[str] = mapped_column(String(6), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    province_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("provinces.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    department_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    province: Mapped[Province] = relationship(back_populates="districts")
    department: Mapped[Department] = relationship()
