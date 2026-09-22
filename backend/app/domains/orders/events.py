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

"""Registro de eventos append-only de una reparación."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import OrderEventType, RepairStatus
from app.models.order import Order, OrderEvent


def record_event(
    session: AsyncSession,
    order: Order,
    *,
    event_type: OrderEventType,
    actor_id: uuid.UUID | None,
    old_status: RepairStatus | None = None,
    new_status: RepairStatus | None = None,
    description: str | None = None,
    visible_to_customer: bool = True,
    metadata: dict[str, Any] | None = None,
) -> OrderEvent:
    event = OrderEvent(
        order_id=order.id,
        actor_id=actor_id,
        event_type=event_type,
        old_status=old_status,
        new_status=new_status,
        description=description,
        visible_to_customer=visible_to_customer,
        event_metadata=metadata,
    )
    if "events" in order.__dict__:
        # Mantiene sincronizada la colección ya cargada para la respuesta.
        order.events.append(event)
    else:
        session.add(event)
    return event
