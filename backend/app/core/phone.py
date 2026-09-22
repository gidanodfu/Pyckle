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

"""Normalización y validación de teléfonos peruanos.

Formato canónico almacenado: ``+51XXXXXXXXX`` (celular de 9 dígitos).
Todos estos valores representan el mismo número::

    999123456
    999 123 456
    999-123-456
    +51999123456
    +51 999 123 456
"""

from __future__ import annotations

import re

PERU_COUNTRY_CODE = "51"
PHONE_ERROR = "Ingresa un celular peruano válido de 9 dígitos, por ejemplo +51 999 123 456"


def normalize_phone(raw: str | None) -> str | None:
    """Devuelve el teléfono en formato canónico ``+51XXXXXXXXX``.

    Lanza ``ValueError`` si el valor no es un celular peruano válido.
    ``None`` o cadena vacía devuelven ``None``.
    """
    if raw is None:
        return None
    value = raw.strip()
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    if digits.startswith("00"):
        digits = digits[2:]
    if len(digits) > 9 and digits.startswith(PERU_COUNTRY_CODE):
        digits = digits[len(PERU_COUNTRY_CODE) :]
    if len(digits) != 9 or digits[0] != "9":
        raise ValueError(PHONE_ERROR)
    return f"+{PERU_COUNTRY_CODE}{digits}"


def format_phone(raw: str | None) -> str:
    """Formato legible para mostrar: ``+51 999 123 456``."""
    try:
        canonical = normalize_phone(raw)
    except ValueError:
        return raw or ""
    if canonical is None:
        return ""
    national = canonical[len(PERU_COUNTRY_CODE) + 1 :]
    return f"+{PERU_COUNTRY_CODE} {national[:3]} {national[3:6]} {national[6:]}"
