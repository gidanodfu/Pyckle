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

"""Agregador de helpers demo (reexporta los módulos por responsabilidad)."""

from app.db.demo_lifecycle import _STATUS_PATH, _ensure_lifecycle_repair
from app.db.demo_locations import _location_context, district_by_code
from app.db.demo_orders import _ensure_completed_flow, _ensure_open_request
from app.db.demo_reports import _ensure_report
from app.db.demo_users import (
    _ensure_customer_profile,
    _ensure_technician,
    _get_or_create_demo_user,
    _refresh_technician_rating,
)

__all__ = [
    "_STATUS_PATH",
    "_ensure_completed_flow",
    "_ensure_customer_profile",
    "_ensure_lifecycle_repair",
    "_ensure_open_request",
    "_ensure_report",
    "_ensure_technician",
    "_get_or_create_demo_user",
    "_location_context",
    "_refresh_technician_rating",
    "district_by_code",
]
