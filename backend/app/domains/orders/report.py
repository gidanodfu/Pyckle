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

"""Generación del informe de reparación en PDF.

Usa ``reportlab`` (programático, sin HTML→PDF). El PDF se arma a partir de
datos reales de la orden; nunca inventa campos.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models.enums import CostKind, RepairResult
from app.models.order import Order

RESULT_LABELS = {
    RepairResult.REPAIRED: "Reparado",
    RepairResult.NOT_REPAIRABLE: "No reparable",
    RepairResult.CANCELLED: "Cancelado",
}

COST_LABELS = {
    CostKind.PART: "Repuestos",
    CostKind.LABOR: "Servicio técnico",
    CostKind.OTHER: "Otros",
}


def report_storage_key(order_id: uuid.UUID, version: int) -> str:
    return f"reports/{order_id}/report-v{version}.pdf"


def _fmt_date(value: datetime | None) -> str:
    return value.strftime("%d/%m/%Y %H:%M") if value else "-"


def _money(value: Decimal | int | float | None) -> str:
    if value is None:
        return "-"
    return f"S/ {Decimal(str(value)):.2f}"


def build_report_pdf(order: Order) -> bytes:
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=18, spaceAfter=2)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12, spaceBefore=10, spaceAfter=4)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=10, leading=14)
    # Celda de tabla con ajuste de línea: las descripciones largas crecen en
    # vertical dentro de su columna en lugar de invadir la del monto.
    cell = ParagraphStyle("cell", parent=styles["Normal"], fontSize=9, leading=11)

    def p(text: str | None) -> Paragraph:
        return Paragraph(escape(text or "-").replace("\n", "<br/>"), body)

    story: list = []

    # Encabezado: solo el título del documento, con la línea azul de marca.
    story.append(
        Table(
            [[Paragraph("Informe de reparación", ParagraphStyle("brand", parent=h1, leading=22))]],
            colWidths=[170 * mm],
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.8, colors.HexColor("#1d4ed8")),
                ]
            ),
        )
    )
    story.append(Spacer(1, 6))

    story.append(Paragraph("Identificación de la reparación", h2))
    story.append(
        Table(
            [
                ["Código de reparación", str(order.id)],
                ["Fecha de recepción", _fmt_date(order.received_at)],
                ["Fecha de finalización", _fmt_date(order.completed_at)],
            ],
            colWidths=[55 * mm, 115 * mm],
            style=TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#475569")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            ),
        )
    )

    story.append(Paragraph("Información del dispositivo", h2))
    specialty = order.request.specialty.name if order.request.specialty else "General"
    story.append(
        Table(
            [["Categoría", specialty], ["Dispositivo / servicio", order.request.title]],
            colWidths=[55 * mm, 115 * mm],
            style=TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#475569")),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            ),
        )
    )

    story.append(Paragraph("Problema reportado", h2))
    story.append(p(order.request.description))

    story.append(Paragraph("Diagnóstico técnico", h2))
    story.append(p(order.diagnosis))

    story.append(Paragraph("Trabajo realizado", h2))
    story.append(p(order.work_performed))

    story.append(Paragraph("Pruebas realizadas", h2))
    story.append(p(order.tests_performed))

    if order.not_repairable_reason:
        story.append(Paragraph("Motivo de no reparable / observación", h2))
        story.append(p(order.not_repairable_reason))

    visible_costs = [item for item in order.cost_items if item.visible_to_customer]
    story.append(Paragraph("Costos", h2))
    if visible_costs:
        rows = [["Concepto", "Monto"]]
        for item in visible_costs:
            label = COST_LABELS.get(item.kind, "Otros")
            rows.append(
                [Paragraph(escape(f"{label}: {item.description}"), cell), _money(item.amount)]
            )
        rows.append(["Precio final", _money(order.final_price)])
        table = Table(rows, colWidths=[125 * mm, 45 * mm])
        table.setStyle(
            TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#c7d2fe")),
                    ("LINEABOVE", (0, 1), (-1, 1), 0.5, colors.HexColor("#c7d2fe")),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.append(table)
    else:
        story.append(p(f"Precio final: {_money(order.final_price)}"))

    story.append(Paragraph("Resultado", h2))
    result_label = RESULT_LABELS.get(order.result, "-") if order.result else "Pendiente"
    story.append(p(result_label))

    story.append(Spacer(1, 10))
    technician_name = order.technician.full_name if order.technician else "-"
    story.append(
        Table(
            [
                ["Técnico responsable", technician_name],
                ["Fecha de emisión", _fmt_date(datetime.now(UTC))],
            ],
            colWidths=[55 * mm, 115 * mm],
            style=TableStyle(
                [
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#475569")),
                    ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.HexColor("#cbd5e1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                ]
            ),
        )
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title="Informe de reparación - Pyckle",
        author="Pyckle",
    )
    doc.build(story)
    return buffer.getvalue()
