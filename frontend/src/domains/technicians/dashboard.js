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
import { PanelShell } from "../../components/layout/index.js";
import {
  alert,
  badge,
  button,
  emptyState,
  pageHeader,
  section,
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
        "flex flex-col gap-2 rounded-lg border border-border p-4 sm:flex-row sm:items-center sm:justify-between",
    },
    h(
      "div",
      {},
      h("p", { class: "font-semibold text-foreground" }, request.title),
      h(
        "p",
        { class: "text-xs text-muted" },
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
                "flex items-center justify-between rounded-lg border border-border px-3 py-2 text-sm",
            },
            h("span", { class: "text-foreground-secondary" }, item.name),
            h("span", { class: "font-semibold text-foreground" }, item.count),
          ),
        ),
      )
    : emptyState("Sin reparaciones", "Aún no tienes reparaciones registradas.");

  return PanelShell(
    {
      header: pageHeader(
        `Panel técnico de ${me.user.full_name.split(" ")[0]}`,
        "Gestiona tus reparaciones, cotizaciones e informes.",
        button("Editar perfil", {
          variant: "outline",
          iconName: "pencil",
          onClick: () => navigate(routes.profileTechnician),
        }),
      ),
      navigation: technicianNav("resumen"),
    },
    h(
      "div",
      { class: "grid gap-4 sm:grid-cols-2 lg:grid-cols-4" },
      statCard("Total reparaciones", summary.total, { iconName: "wrench" }),
      statCard("En proceso", inProgress, { accent: "text-info", iconName: "hammer" }),
      statCard("Esperando", waiting, { accent: "text-warning", iconName: "clock" }),
      statCard("Completadas", byStatus.completed || 0, {
        accent: "text-success",
        iconName: "circle-check",
      }),
    ),
    h(
      "div",
      { class: "grid gap-6 lg:grid-cols-2" },
      section(
        {
          title: "Reparaciones por estado",
          actions: button("Ver todas", {
            variant: "ghost",
            onClick: () => navigate(routes.technicianRepairs),
          }),
        },
        statusCountsList(byStatus),
        summary.pending_price_changes
          ? h(
              "p",
              { class: "text-sm text-warning" },
              `${summary.pending_price_changes} cambio(s) de precio esperando aprobación.`,
            )
          : null,
      ),
      section({ title: "Reparaciones por categoría" }, categoryList),
    ),
    section(
      {
        title: "Solicitudes compatibles",
        actions: button("Ver todas", {
          variant: "ghost",
          onClick: () => navigate(routes.requests),
        }),
      },
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
    section(
      { title: "Tu zona de atención" },
      h(
        "p",
        { class: "text-sm text-foreground-secondary" },
        [profile.district_name, profile.province_name, profile.department_name]
          .filter(Boolean)
          .join(", ") || "Configura tu ubicación para recibir solicitudes de tu zona.",
      ),
    ),
  );
}
