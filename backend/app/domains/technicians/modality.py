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

"""Reglas de modalidad de atención de un técnico: local, domicilio o ambas.

Fuente única de verdad usada al registrar y al editar el perfil. La columna
``workshop_address`` solo se conserva cuando el técnico atiende en taller.
"""

from __future__ import annotations

from app.core.exceptions import BadRequestError

MODALITY_LOCAL = "local"
MODALITY_HOME = "home"
MODALITY_BOTH = "both"


def validate_service_modality(
    *,
    offers_home_service: bool,
    offers_workshop_service: bool,
    workshop_address: str | None,
) -> str | None:
    """Valida la combinación final y normaliza la dirección del taller.

    Debe existir al menos una modalidad. Si atiende en taller, la dirección es
    obligatoria; si no, se descarta (nunca se guarda una dirección huérfana).
    """
    if not offers_home_service and not offers_workshop_service:
        raise BadRequestError("Debes ofrecer atención a domicilio, en taller o ambas")
    if offers_workshop_service:
        cleaned = (workshop_address or "").strip()
        if not cleaned:
            raise BadRequestError("Si atiendes en taller, indica la dirección del local")
        return cleaned
    return None


def modality_of(*, offers_home_service: bool, offers_workshop_service: bool) -> str:
    if offers_home_service and offers_workshop_service:
        return MODALITY_BOTH
    return MODALITY_HOME if offers_home_service else MODALITY_LOCAL
