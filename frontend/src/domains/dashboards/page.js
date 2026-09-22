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
import { formatDate, h } from "../../components/dom.js";
import { icon } from "../../components/icons.js";
import { Container } from "../../components/layout/index.js";
import {
  badge,
  button,
  emptyState,
  pageHeader,
  sectionTitle,
  statCard,
} from "../../components/ui/index.js";
import { navigate } from "../../lib/navigation.js";
import { store } from "../../state/store.js";
import { routes } from "../../lib/paths.js";

function requestRow(request) {
  const location = [request.district_name, request.province_name].filter(Boolean).join(", ");
  return h(
    "div",
    {
      class:
        "flex flex-col gap-2 rounded-lg border border-slate-200 p-4 sm:flex-row sm:items-center sm:justify-between",
    },
    h(
      "div",
      {},
      h("p", { class: "font-semibold text-slate-800" }, request.title),
      h(
        "p",
        { class: "text-xs text-slate-500" },
        `${request.specialty?.name || "General"} · ${formatDate(request.created_at)}${location ? ` · ${location}` : ""}`,
      ),
    ),
    h(
      "div",
      { class: "flex items-center gap-2" },
      badge(request.status),
      button("Ver", {
        variant: "outline",
        iconName: "eye",
        onClick: () => navigate(routes.requestDetail(request.id)),
      }),
    ),
  );
}

export async function CustomerDashboard() {
  const me = store.get().me;
  const [requests, orders] = await Promise.all([
    api.get(endpoints.requests.list({ limit: 5 })),
    api.get(endpoints.orders.list({ limit: 5 })),
  ]);

  const active = requests.items.filter(
    (item) => !["completed", "cancelled"].includes(item.status),
  ).length;
  const completed = orders.items.filter((item) => item.result === "repaired").length;
  const profile = me.customer_profile;
  const location = [profile?.district_name, profile?.province_name].filter(Boolean).join(", ");

  return Container(
    pageHeader(
      `Hola, ${me.user.full_name.split(" ")[0]}`,
      "Resumen de tus solicitudes y reparaciones.",
      button("Nueva solicitud", { iconName: "plus", onClick: () => navigate(routes.requestNew) }),
    ),
    location
      ? h(
          "p",
          { class: "mt-4 inline-flex items-center gap-1.5 text-sm text-slate-500" },
          icon("map-pin", { size: 15 }),
          location,
        )
      : null,
    h(
      "div",
      { class: "mt-6 grid gap-4 sm:grid-cols-3" },
      statCard("Solicitudes activas", active, { iconName: "clipboard-list" }),
      statCard("Reparaciones totales", orders.total, { iconName: "receipt-text" }),
      statCard("Reparaciones completadas", completed, {
        accent: "text-emerald-700",
        iconName: "circle-check",
      }),
    ),
    h(
      "div",
      { class: "mt-8 space-y-3" },
      sectionTitle(
        "Solicitudes recientes",
        button("Ver todas", { variant: "ghost", onClick: () => navigate(routes.requests) }),
      ),
      requests.items.length
        ? requests.items.map(requestRow)
        : emptyState(
            "Aún no tienes solicitudes",
            "Publica tu primer problema y recibe cotizaciones.",
            button("Crear solicitud", {
              iconName: "plus",
              onClick: () => navigate(routes.requestNew),
            }),
            { iconName: "clipboard-list" },
          ),
    ),
  );
}
