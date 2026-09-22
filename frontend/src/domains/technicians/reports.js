/*
 * Copyright (C) 2026 Josue David (gidanodfu)
 * https://github.com/gidanodfu
 *
 * This file is part of Pyckle.
 *
 * Pyckle is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 *
 * Pyckle is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with Pyckle. If not, see <https://www.gnu.org/licenses/>.
 */

import { api } from "../../api/client.js";
import { endpoints } from "../../api/endpoints.js";
import { formatDateTime, formatMoney, h } from "../../components/dom.js";
import { Container } from "../../components/layout/index.js";
import { badge, button, emptyState, pageHeader, table, withBusy } from "../../components/ui/index.js";
import { routes } from "../../lib/paths.js";
import { navigate } from "../../lib/navigation.js";
import { downloadOrderReport } from "../orders/components/report-download.js";
import { technicianNav } from "./components/panel-nav.js";

export async function TechnicianReports() {
  const data = await api.get(endpoints.orders.list({ status: "completed", limit: 50 }));
  const items = data.items.filter((order) => order.has_report);

  const content = items.length
    ? table(
        [
          "Orden",
          "Solicitud",
          { label: "Resultado", align: "center" },
          { label: "Final", align: "right" },
          "Fecha",
          { label: "", align: "right" },
        ],
        items.map((order) => [
          h("span", { class: "font-mono text-xs text-slate-500" }, order.id.slice(0, 8)),
          order.request.title,
          order.result ? badge(order.result) : h("span", { class: "text-xs text-slate-500" }, "-"),
          formatMoney(order.final_price),
          formatDateTime(order.completed_at || order.created_at),
          h(
            "span",
            { class: "inline-flex items-center gap-2" },
            button("Ver", {
              variant: "outline",
              iconName: "eye",
              onClick: () => navigate(routes.orderDetail(order.id)),
            }),
            button("PDF", {
              variant: "ghost",
              iconName: "file-down",
              onClick: (event) =>
                withBusy(event.currentTarget, async () => {
                  try {
                    await downloadOrderReport(order);
                  } catch (error) {
                    window.alert(error.message || "No se pudo descargar el informe");
                  }
                }),
            }),
          ),
        ]),
      )
    : emptyState(
        "Sin informes",
        "Los informes aparecen al completar una reparación.",
        null,
        { iconName: "file-text" },
      );

  return Container(
    pageHeader("Informes de reparación", "Documentos de cierre de tus reparaciones finalizadas."),
    technicianNav("reports"),
    h("div", { class: "mt-6" }, content),
  );
}
