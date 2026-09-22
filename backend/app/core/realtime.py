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

import json
from typing import Any

from app.core.logging import get_logger
from app.core.redis import get_redis

logger = get_logger("realtime")


async def _publish(channel: str, event: dict[str, Any]) -> None:
    try:
        await get_redis().publish(channel, json.dumps(event, default=str))
    except Exception:  # noqa: BLE001 - la mensajeria nunca debe romper la operacion
        logger.warning("No se pudo publicar en el canal %s", channel, exc_info=True)


async def publish_user(user_id: Any, event: dict[str, Any]) -> None:
    await _publish(f"user:{user_id}", event)


async def publish_conversation(conversation_id: Any, event: dict[str, Any]) -> None:
    await _publish(f"conversation:{conversation_id}", event)
