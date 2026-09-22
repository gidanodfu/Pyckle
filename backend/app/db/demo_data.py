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

"""Datos demo del seed (solo literales).

Separado de `app.db.seed` para que la lógica de siembra sea legible.
Convención de correos: demo.customer.NNN@ / demo.technician.NNN@pyckle.dev.
"""

from __future__ import annotations

# --- Datos demo -----------------------------------------------------------
# Convención: demo.customer.NNN@pyckle.dev / demo.technician.NNN@pyckle.dev
# Distribución en 9 departamentos para probar filtros por zona y verificación.

DEMO_CUSTOMERS = [
    ("001", "Ana Quispe Mamani", "150122", "Av. Larco 123, Miraflores"),
    ("002", "Luis Fernando Castillo", "150131", "Calle Los Laureles 456, San Isidro"),
    ("003", "María Fernanda Rojas", "150140", "Av. Benavides 789, Santiago de Surco"),
    ("004", "Jorge Antonio Mendoza", "070101", "Av. Elmer Faucett 220, Callao"),
    ("005", "Carmen Rosa Delgado", "040101", "Calle Mercaderes 310, Arequipa"),
    ("006", "Ricardo Alonso Paredes", "040126", "Av. Ejército 120, Yanahuara"),
    ("007", "Patricia Elena Núñez", "130101", "Av. España 450, Trujillo"),
    ("008", "Miguel Ángel Requejo", "140101", "Av. Balta 620, Chiclayo"),
    ("009", "Rosa Amelia Chávez", "140105", "Av. Chiclayo 890, José Leonardo Ortiz"),
    ("010", "Diego Sebastián Flores", "200101", "Av. Grau 330, Piura"),
    ("011", "Silvia Carolina Vílchez", "200104", "Av. Sánchez Cerro 210, Castilla"),
    ("012", "Óscar Eduardo Salazar", "080108", "Av. El Sol 560, Wanchaq"),
]

DEMO_TECHNICIANS = [
    {
        "id": "001",
        "name": "Carlos Ramírez Ñopo",
        "district": "150122",
        "verified": True,
        "specialties": ["laptops", "computadoras-de-escritorio"],
        "experience": 8,
        "home": True,
        "workshop": True,
        "workshop_address": "Av. Arequipa 2100, Miraflores",
    },
    {
        "id": "002",
        "name": "Lucía Herrera Campos",
        "district": "150131",
        "verified": True,
        "specialties": ["celulares", "tablets"],
        "experience": 6,
        "home": True,
        "workshop": False,
        "workshop_address": None,
    },
    {
        "id": "003",
        "name": "Bruno Salcedo Paredes",
        "district": "150140",
        "verified": False,
        "specialties": ["consolas"],
        "experience": 4,
        "home": True,
        "workshop": False,
        "workshop_address": None,
    },
    {
        "id": "004",
        "name": "Gloria Nakamura Torres",
        "district": "070101",
        "verified": True,
        "specialties": ["impresoras"],
        "experience": 10,
        "home": False,
        "workshop": True,
        "workshop_address": "Av. Argentina 450, Callao",
    },
    {
        "id": "005",
        "name": "Martín Quispe Huamán",
        "district": "040101",
        "verified": True,
        "specialties": ["laptops", "celulares"],
        "experience": 12,
        "home": True,
        "workshop": True,
        "workshop_address": "Calle Mercaderes 220, Arequipa",
    },
    {
        "id": "006",
        "name": "Elena Vargas Zúñiga",
        "district": "040126",
        "verified": False,
        "specialties": ["televisores"],
        "experience": 5,
        "home": True,
        "workshop": False,
        "workshop_address": None,
    },
    {
        "id": "007",
        "name": "Iván Castañeda Loayza",
        "district": "130101",
        "verified": False,
        "specialties": ["laptops"],
        "experience": 3,
        "home": True,
        "workshop": False,
        "workshop_address": None,
    },
    {
        "id": "008",
        "name": "Rosa Elvira Campos",
        "district": "140101",
        "verified": True,
        "specialties": ["impresoras", "computadoras-de-escritorio"],
        "experience": 9,
        "home": False,
        "workshop": True,
        "workshop_address": "Av. Balta 700, Chiclayo",
    },
    {
        "id": "009",
        "name": "Fernando León Dávila",
        "district": "200101",
        "verified": False,
        "specialties": ["celulares"],
        "experience": 4,
        "home": True,
        "workshop": False,
        "workshop_address": None,
    },
    {
        "id": "010",
        "name": "Sofía Mendoza Ríos",
        "district": "080108",
        "verified": True,
        "specialties": ["laptops", "tablets"],
        "experience": 7,
        "home": True,
        "workshop": False,
        "workshop_address": None,
    },
    {
        "id": "011",
        "name": "Hugo Barrientos Cáceres",
        "district": "120101",
        "verified": False,
        "specialties": ["televisores", "consolas"],
        "experience": 6,
        "home": True,
        "workshop": False,
        "workshop_address": None,
    },
    {
        "id": "012",
        "name": "Teresa Alvarado Pinto",
        "district": "160101",
        "verified": False,
        "specialties": ["computadoras-de-escritorio"],
        "experience": 5,
        "home": False,
        "workshop": True,
        "workshop_address": "Calle Próspero 150, Iquitos",
    },
]

# Órdenes completadas con reseñas reales; el rating del técnico se recalcula.
# rating 0 => orden completada sin reseña (técnico verificado sin calificación).
DEMO_COMPLETED = [
    (
        "001",
        "001",
        "laptops",
        "[Demo] Laptop con pantalla intermitente",
        180,
        5,
        "Excelente servicio, muy puntual.",
    ),
    (
        "001",
        "002",
        "laptops",
        "[Demo] Notebook no carga la batería",
        150,
        5,
        "Diagnóstico claro y rápido.",
    ),
    (
        "001",
        "003",
        "computadoras-de-escritorio",
        "[Demo] PC se reinicia al jugar",
        220,
        4,
        "Buen trabajo, tardó un día más.",
    ),
    ("002", "002", "celulares", "[Demo] Celular no enciende", 120, 5, "Muy amable y rápido."),
    (
        "002",
        "003",
        "tablets",
        "[Demo] Tablet con pantalla táctil fallando",
        140,
        4,
        "Resolvió el problema.",
    ),
    (
        "004",
        "004",
        "impresoras",
        "[Demo] Impresora no imprime a color",
        90,
        4,
        "Servicio correcto.",
    ),
    ("005", "005", "laptops", "[Demo] Laptop se sobrecalienta", 200, 5, "Muy profesional."),
    (
        "005",
        "006",
        "celulares",
        "[Demo] Celular con batería inflada",
        110,
        5,
        "Cambio de batería perfecto.",
    ),
    (
        "005",
        "005",
        "laptops",
        "[Demo] Teclado de laptop no responde",
        130,
        5,
        "Excelente atención.",
    ),
    ("010", "012", "laptops", "[Demo] Laptop lenta tras actualización", 160, 0, None),
]

# Solicitudes abiertas con una cotización pendiente del técnico de la misma zona.
DEMO_OPEN = [
    (
        "001",
        "laptops",
        "[Demo] Laptop con pantalla rota",
        "Se cayó la laptop y la pantalla quedó con líneas.",
        250,
        "001",
        True,
    ),
    (
        "004",
        "impresoras",
        "[Demo] Impresora atascada",
        "La impresora deja de imprimir y muestra un error.",
        80,
        "004",
        False,
    ),
    (
        "005",
        "celulares",
        "[Demo] Celular con pantalla agrietada",
        "Necesito el cambio de pantalla del celular.",
        160,
        "005",
        True,
    ),
    (
        "006",
        "televisores",
        "[Demo] Televisor sin imagen",
        "El televisor enciende pero no muestra imagen.",
        190,
        "006",
        True,
    ),
    (
        "008",
        "computadoras-de-escritorio",
        "[Demo] PC no da video",
        "La computadora enciende pero no muestra imagen.",
        140,
        "008",
        False,
    ),
    (
        "010",
        "celulares",
        "[Demo] Celular no carga",
        "El celular dejó de cargar desde ayer.",
        90,
        "009",
        True,
    ),
    (
        "012",
        "tablets",
        "[Demo] Tablet no carga",
        "La tablet no carga ni enciende.",
        120,
        "010",
        True,
    ),
]
