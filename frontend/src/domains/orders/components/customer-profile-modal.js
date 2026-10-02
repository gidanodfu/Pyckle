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

import { h } from "../../../components/dom.js";
import { icon } from "../../../components/icons.js";
import { card, modal } from "../../../components/ui/index.js";

export function customerProfileModal(profile) {
  const memberSince = new Date(profile.member_since).toLocaleDateString("es-PE", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
  const location = [profile.district_name, profile.province_name, profile.department_name]
    .filter(Boolean)
    .join(", ");
  return modal(
    "Perfil del cliente",
    h(
      "div",
      { class: "space-y-4" },
      h(
        "div",
        { class: "flex items-center gap-3" },
        h(
          "span",
          { class: "flex h-11 w-11 items-center justify-center rounded-full bg-primary-tint text-primary" },
          icon("user", { size: 20 }),
        ),
        h(
          "div",
          {},
          h("p", { class: "text-lg font-semibold text-foreground" }, profile.full_name),
          h("p", { class: "text-xs text-muted" }, `Miembro desde ${memberSince}`),
        ),
      ),
      h(
        "div",
        { class: "grid gap-3 sm:grid-cols-2" },
        card(
          h("p", { class: "text-xs uppercase tracking-wide text-muted" }, "Reparaciones realizadas"),
          h("p", { class: "mt-1 text-xl font-bold text-success" }, String(profile.completed_repairs)),
        ),
        card(
          h("p", { class: "text-xs uppercase tracking-wide text-muted" }, "Ubicación"),
          h("p", { class: "mt-1 text-sm font-medium text-foreground-secondary" }, location || "-"),
        ),
      ),
      h("p", { class: "text-xs text-muted" }, "La dirección exacta solo se comparte cuando corresponde a una reparación a domicilio aceptada."),
    ),
  );
}
