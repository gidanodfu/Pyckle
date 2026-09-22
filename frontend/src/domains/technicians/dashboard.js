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
import {
  alert,
  badge,
  button,
  card,
  emptyState,
  pageHeader,
  sectionTitle,
  statCard,
} from "../../components/ui/index.js";
import { routes } from "../../lib/paths.js";
import { navigate } from "../../lib/navigation.js";
import { store } from "../../state/store.js";
import { statusCountsList, technicianNav } from "./components/panel-nav.js";

const SCOPE_LABELS = {
  province: "tu provincia",
  department: "tu departamento",
  all: "todo el país",
};

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

export async function TechnicianDashboard() {
  const me = store.get().me;
  const [profile, summary, available] = await Promise.all([
    api.get(endpoints.technicians.me),
    api.get(endpoints.technicians.summary),
    api.get(endpoints.requests.available({ limit: 5 })),
  ]);

  const byStatus = summary.by_status || {};
  const bySpecialty = summary.by_specialty || [];
  const inProgress = (byStatus.in_repair || 0) + (byStatus.testing || 0);
  const waiting = (byStatus.waiting_customer || 0) + (byStatus.waiting_part || 0);

  const categoryList = bySpecialty.length
    ? h(
        "ul",
        { class: "space-y-2" },
        summary.by_specialty.map((item) =>
          h(
            "li",
            {
              class:
                "flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2 text-sm",
            },
            h("span", { class: "text-slate-700" }, item.name),
            h("span", { class: "font-semibold text-slate-900" }, item.count),
          ),
        ),
      )
    : emptyState("Sin reparaciones", "Aún no tienes reparaciones registradas.");

  return Container(
    pageHeader(
      `Panel técnico de ${me.user.full_name.split(" ")[0]}`,
      "Gestiona tus reparaciones, cotizaciones e informes.",
      button("Editar perfil", {
        variant: "outline",
        iconName: "pencil",
        onClick: () => navigate(routes.profileTechnician),
      }),
    ),
    technicianNav("resumen"),
    h(
      "div",
      { class: "mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4" },
      statCard("Total reparaciones", summary.total, { iconName: "wrench" }),
      statCard("En proceso", inProgress, { accent: "text-cyan-700", iconName: "hammer" }),
      statCard("Esperando", waiting, { accent: "text-amber-700", iconName: "clock" }),
      statCard("Completadas", byStatus.completed || 0, {
        accent: "text-emerald-700",
        iconName: "circle-check",
      }),
    ),
    h(
      "div",
      { class: "mt-8 grid gap-6 lg:grid-cols-2" },
      card(
        sectionTitle(
          "Reparaciones por estado",
          button("Ver todas", { variant: "ghost", onClick: () => navigate(routes.technicianRepairs) }),
        ),
        h("div", { class: "mt-4" }, statusCountsList(byStatus)),
        summary.pending_price_changes
          ? h(
              "p",
              { class: "mt-4 text-sm text-amber-700" },
              `${summary.pending_price_changes} cambio(s) de precio esperando aprobación.`,
            )
          : null,
      ),
      card(
        sectionTitle("Reparaciones por categoría"),
        h("div", { class: "mt-4" }, categoryList),
      ),
    ),
    h(
      "section",
      { class: "mt-8 space-y-3" },
      sectionTitle(
        "Solicitudes compatibles",
        button("Ver todas", { variant: "ghost", onClick: () => navigate(routes.requests) }),
      ),
      available.expanded
        ? alert(
            `Mostrando solicitudes de ${SCOPE_LABELS[available.scope]} porque no hay en tu distrito.`,
            "info",
          )
        : null,
      available.items.length
        ? available.items.map(requestRow)
        : emptyState(
            "Sin solicitudes compatibles",
            "Amplía tus especialidades para recibir más solicitudes.",
            null,
            { iconName: "clipboard-list" },
          ),
    ),
    h(
      "div",
      { class: "mt-8" },
      card(
        h("h3", { class: "text-sm font-semibold text-slate-900" }, "Tu zona de atención"),
        h(
          "p",
          { class: "mt-1 text-sm text-slate-600" },
          [profile.district_name, profile.province_name, profile.department_name]
            .filter(Boolean)
            .join(", ") || "Configura tu ubicación para recibir solicitudes de tu zona.",
        ),
      ),
    ),
  );
}
