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

"""Casos demo del ciclo de reparación (solo literales)."""

from __future__ import annotations

from app.models.enums import PriceChangeStatus, RepairResult

# (customer_id, tech_id, slug, title, status, price, result, price_change)
DEMO_LIFECYCLE = [
    ("001", "001", "laptops", "[Demo] Cambio de pantalla", "awaiting_receipt", 250, None, None),
    ("002", "002", "celulares", "[Demo] Batería no carga", "diagnosis", 120, None, None),
    (
        "003",
        "002",
        "tablets",
        "[Demo] Tablet con táctil fallando",
        "waiting_part",
        140,
        None,
        None,
    ),
    ("004", "004", "impresoras", "[Demo] Impresora sin color", "in_repair", 90, None, None),
    ("005", "005", "laptops", "[Demo] Laptop se apaga", "testing", 210, None, None),
    ("006", "006", "televisores", "[Demo] TV sin imagen", "ready", 190, None, None),
    (
        "007",
        "007",
        "laptops",
        "[Demo] Laptop con costo adicional",
        "waiting_customer",
        300,
        None,
        {
            "new_price": 420,
            "reason": "Se detectó daño adicional en la placa principal.",
            "status": PriceChangeStatus.PENDING,
        },
    ),
    (
        "005",
        "005",
        "laptops",
        "[Demo] Laptop con costo aprobado",
        "in_repair",
        220,
        None,
        {
            "new_price": 280,
            "reason": "Repuesto importado de mayor costo.",
            "status": PriceChangeStatus.APPROVED,
        },
    ),
    (
        "006",
        "006",
        "televisores",
        "[Demo] TV con costo rechazado",
        "diagnosis",
        190,
        None,
        {
            "new_price": 250,
            "reason": "Cambio de panel adicional.",
            "status": PriceChangeStatus.REJECTED,
        },
    ),
    (
        "010",
        "010",
        "tablets",
        "[Demo] Tablet con daño irreparable",
        "completed",
        130,
        RepairResult.NOT_REPAIRABLE,
        None,
    ),
    (
        "011",
        "011",
        "televisores",
        "[Demo] TV cancelado por el cliente",
        "cancelled",
        150,
        None,
        None,
    ),
]
