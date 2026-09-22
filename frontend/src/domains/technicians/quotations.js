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
import { formatDate, formatMoney, h } from "../../components/dom.js";
import { Container } from "../../components/layout/index.js";
import { badge, button, card, emptyState, pageHeader } from "../../components/ui/index.js";
import { routes } from "../../lib/paths.js";
import { navigate } from "../../lib/navigation.js";
import { technicianNav } from "./components/panel-nav.js";

export async function TechnicianQuotations() {
  const quotations = await api.get(endpoints.quotations.mine);

  const list = quotations.length
    ? h(
        "div",
        { class: "space-y-3" },
        quotations.map((quotation) =>
          card(
            h(
              "div",
              { class: "flex flex-wrap items-center justify-between gap-3" },
              h(
                "div",
                {},
                h("p", { class: "font-semibold text-slate-800" }, formatMoney(quotation.price)),
                h(
                  "p",
                  { class: "text-xs text-slate-500" },
                  `${quotation.estimated_days} día(s) · ${formatDate(quotation.created_at)}`,
                ),
              ),
              h(
                "div",
                { class: "flex items-center gap-2" },
                badge(quotation.status),
                button("Ver solicitud", {
                  variant: "outline",
                  iconName: "eye",
                  onClick: () => navigate(routes.requestDetail(quotation.request_id)),
                }),
              ),
            ),
            h("p", { class: "mt-2 text-sm text-slate-600" }, quotation.preliminary_diagnosis),
          ),
        ),
      )
    : emptyState(
        "Sin cotizaciones",
        "Explora solicitudes disponibles y envía tu primera oferta.",
        null,
        { iconName: "file-text" },
      );

  return Container(
    pageHeader("Mis cotizaciones", "Propuestas enviadas y su estado."),
    technicianNav("quotations"),
    h("div", { class: "mt-6" }, list),
  );
}
