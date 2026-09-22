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

"""Persistencia, versionado y descarga de informes (mixin de OrderService)."""

from __future__ import annotations

import uuid

from app.core.exceptions import NotFoundError
from app.domains.orders.report import build_report_pdf, report_storage_key
from app.models.enums import OrderEventType
from app.models.order import Order, RepairReport
from app.models.user import User


class OrderReportsMixin:
    async def get_report(self, order_id: uuid.UUID, user: User) -> tuple[RepairReport, bytes]:
        order = await self._get_or_404(order_id)
        await self.access.assert_can_view(order, user)
        report = await self.reports.get_latest(order.id)
        if report is None:
            raise NotFoundError("La reparación no tiene informe")
        data = await self.storage.get(report.storage_key)
        return report, data

    async def list_reports(self, order_id: uuid.UUID, user: User) -> list[RepairReport]:
        order = await self._get_or_404(order_id)
        await self.access.assert_can_view(order, user)
        return await self.reports.list_for_order(order.id)

    async def _persist_report(self, order: Order, *, actor_id: uuid.UUID) -> RepairReport:
        """Genera y persiste el PDF; registra la fila de informe (sin commit).

        El ``storage_key`` es determinista por versión para que un reintento
        sobrescriba el mismo objeto en lugar de acumular huérfanos.
        """
        version = await self.reports.next_version(order.id)
        key = report_storage_key(order.id, version)
        data = build_report_pdf(order)
        await self.storage.save_at(data=data, content_type="application/pdf", storage_key=key)
        report = RepairReport(
            order_id=order.id,
            version=version,
            storage_key=key,
            content_type="application/pdf",
            size_bytes=len(data),
            generated_by=actor_id,
        )
        if "reports" in order.__dict__:
            # Refleja el informe en la colección ya cargada para la respuesta.
            order.reports.append(report)
        else:
            self.session.add(report)
        self._record_event(
            order,
            event_type=OrderEventType.REPORT_GENERATED,
            actor_id=actor_id,
            description=f"Informe de reparación v{version} generado",
            metadata={"report_key": key, "version": version},
        )
        self._pending_report_key = key
        return report

    async def _cleanup_pending_report(self) -> None:
        """Borra el PDF si la transacción falló (evita informes huérfanos)."""
        key = self._pending_report_key
        self._pending_report_key = None
        if not key:
            return
        try:
            await self.storage.delete(key)
        except Exception:  # noqa: BLE001 - limpieza best-effort
            pass
