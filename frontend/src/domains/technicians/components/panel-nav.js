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

import { h, statusLabel } from "../../../components/dom.js";
import { button } from "../../../components/ui/index.js";
import { routes } from "../../../lib/paths.js";
import { navigate } from "../../../lib/navigation.js";

const LINKS = [
  { key: "resumen", label: "Resumen", path: routes.technicianDashboard, iconName: "layout-dashboard" },
  { key: "repairs", label: "Reparaciones", path: routes.technicianRepairs, iconName: "wrench" },
  {
    key: "quotations",
    label: "Cotizaciones",
    path: routes.technicianQuotations,
    iconName: "file-text",
  },
  { key: "reports", label: "Informes", path: routes.technicianReports, iconName: "file-down" },
];

export function technicianNav(active) {
  return h(
    "nav",
    { class: "mt-4 flex flex-wrap gap-2" },
    LINKS.map((link) =>
      button(link.label, {
        variant: active === link.key ? "primary" : "ghost",
        iconName: link.iconName,
        onClick: () => navigate(link.path),
      }),
    ),
  );
}

const STATUS_ORDER = [
  "awaiting_receipt",
  "received",
  "diagnosis",
  "waiting_customer",
  "waiting_part",
  "in_repair",
  "testing",
  "ready",
  "completed",
  "cancelled",
];

export function statusCountsList(byStatus) {
  const entries = STATUS_ORDER.filter((status) => byStatus[status]);
  if (!entries.length) return h("p", { class: "text-sm text-slate-500" }, "Sin reparaciones aún.");
  return h(
    "ul",
    { class: "grid gap-2 sm:grid-cols-2" },
    entries.map((status) =>
      h(
        "li",
        { class: "flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2 text-sm" },
        h("span", { class: "text-slate-700" }, statusLabel(status)),
        h("span", { class: "font-semibold text-slate-900" }, byStatus[status]),
      ),
    ),
  );
}
