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

"""Tickets efímeros y de un solo uso para autenticar WebSockets.

Evita enviar el JWT en la query string (registrado en logs). El cliente pide un
ticket autenticado por REST, lo usa una vez para abrir el WebSocket y el
servidor lo consume de forma atómica (GETDEL).
"""

from __future__ import annotations

import uuid

from app.core.redis import get_redis

WS_TICKET_TTL_SECONDS = 60


def _key(ticket: str) -> str:
    return f"ws:ticket:{ticket}"


async def issue_ws_ticket(user_id: uuid.UUID) -> tuple[str, int]:
    ticket = uuid.uuid4().hex
    await get_redis().setex(_key(ticket), WS_TICKET_TTL_SECONDS, str(user_id))
    return ticket, WS_TICKET_TTL_SECONDS


async def consume_ws_ticket(ticket: str | None) -> str | None:
    if not ticket:
        return None
    return await get_redis().getdel(_key(ticket))
