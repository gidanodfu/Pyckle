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
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict

# Máximo representable por las columnas Numeric(10, 2) de Pyckle.
MAX_MONEY = Decimal("99999999.99")


def _non_blank(value: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError("El campo no puede estar vacío")
    return cleaned


# Cadena que no puede ser vacía ni contener solo espacios; se normaliza con strip.
NonBlankStr = Annotated[str, AfterValidator(_non_blank)]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Message(BaseModel):
    detail: str


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int
    # Zona efectiva de un filtro geografico: district | province | department | all.
    scope: str | None = None
    expanded: bool = False


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None
