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
import { formatDate, h, statusLabel } from "../../components/dom.js";
import { Container } from "../../components/layout/index.js";
import { alert, badge, button, emptyState, pageHeader, table } from "../../components/ui/index.js";
import { routes } from "../../lib/paths.js";
import { navigate } from "../../lib/navigation.js";
import { store } from "../../state/store.js";

const SCOPE_LABELS = {
  province: "tu provincia",
  department: "tu departamento",
  all: "todo el país",
};

function expansionNotice(scope, expanded) {
  if (!expanded || !SCOPE_LABELS[scope]) return null;
  return alert(`No hay solicitudes en tu distrito; mostrando solicitudes de ${SCOPE_LABELS[scope]}.`, "info");
}

export async function RequestsList() {
  const me = store.get().me;
  const roles = me.user.roles.map((role) => role.name);

  if (roles.includes("admin")) {
    const data = await api.get(endpoints.admin.requests({ limit: 50 }));
    return Container(
      pageHeader("Solicitudes", "Moderación de todas las solicitudes del marketplace."),
      h("div", { class: "mt-6" }, requestsTable(data.items, { admin: true })),
    );
  }

  if (roles.includes("technician")) {
    const [available, mine] = await Promise.all([
      api.get(endpoints.requests.available({ limit: 50 })),
      api.get(endpoints.requests.list({ limit: 50 })),
    ]);
    const notice = expansionNotice(available.scope, available.expanded);
    return Container(
      pageHeader("Solicitudes", "Solicitudes compatibles con tus especialidades y tu zona."),
      notice ? h("div", { class: "mt-6" }, notice) : null,
      h("h2", { class: "mt-6 mb-3 text-lg font-semibold text-slate-900" }, "Disponibles"),
      h("div", { class: "mb-8" }, requestsTable(available.items)),
      h("h2", { class: "mb-3 text-lg font-semibold text-slate-900" }, "Mis solicitudes asignadas"),
      requestsTable(mine.items),
    );
  }

  const data = await api.get(endpoints.requests.list({ limit: 50 }));
  return Container(
    pageHeader(
      "Mis solicitudes",
      "Historial de solicitudes de reparación.",
      button("Nueva solicitud", { iconName: "plus", onClick: () => navigate(routes.requestNew) }),
    ),
    h(
      "div",
      { class: "mt-6" },
      data.items.length
        ? requestsTable(data.items)
        : emptyState(
            "Sin solicitudes",
            "Publica tu primer problema para recibir cotizaciones.",
            button("Crear solicitud", { iconName: "plus", onClick: () => navigate(routes.requestNew) }),
            { iconName: "clipboard-list" },
          ),
    ),
  );
}

function requestsTable(items, { admin = false } = {}) {
  if (!items.length) return emptyState("Sin resultados", "No hay solicitudes para mostrar.");
  const columns = [
    "Título",
    "Ubicación",
    "Especialidad",
    { label: "Estado", align: "center" },
    { label: "Modalidad", align: "center" },
    "Fecha",
    { label: admin ? "Cliente" : "", align: "center" },
    { label: "", align: "right" },
  ];
  return table(
    columns,
    items.map((request) => {
      const location = [request.district_name || request.district, request.province_name, request.department_name]
        .filter(Boolean)
        .join(", ");
      return [
        h("span", { class: "font-medium text-slate-800" }, request.title),
        location || "-",
        request.specialty?.name || "General",
        badge(request.status),
        statusLabel(request.modality),
        formatDate(request.created_at),
        admin ? request.customer?.full_name || "-" : null,
        button("Detalle", { variant: "outline", iconName: "eye", onClick: () => navigate(routes.requestDetail(request.id)) }),
      ];
    }),
  );
}
