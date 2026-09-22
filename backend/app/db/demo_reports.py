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

"""Helpers del seed demo (logica reutilizable)."""

from __future__ import annotations

from sqlalchemy import select

from app.domains.orders.report import build_report_pdf, report_storage_key
from app.infrastructure.storage import build_storage
from app.models.order import (
    Order,
    RepairReport,
)


async def _ensure_report(session, order: Order, actor_id) -> None:
    from app.domains.orders.repository import OrderRepository

    existing = (
        (await session.execute(select(RepairReport).where(RepairReport.order_id == order.id)))
        .scalars()
        .first()
    )
    if existing is not None:
        return
    detail = await OrderRepository(session).get_detail(order.id)
    if detail is None:
        return
    data = build_report_pdf(detail)
    key = report_storage_key(detail.id, 1)
    storage = build_storage()
    try:
        await storage.save_at(data=data, content_type="application/pdf", storage_key=key)
    except Exception:  # noqa: BLE001 - el seed no debe romper por el storage
        return
    session.add(
        RepairReport(
            order_id=detail.id,
            version=1,
            storage_key=key,
            content_type="application/pdf",
            size_bytes=len(data),
            generated_by=actor_id,
        )
    )
    await session.flush()
