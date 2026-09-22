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
import { button, card, stars, verifiedBadge } from "../../../components/ui/index.js";
import { routes } from "../../../lib/paths.js";
import { navigate } from "../../../lib/navigation.js";

export function technicianCard(technician) {
  const location = [technician.district_name, technician.province_name].filter(Boolean).join(", ");
  return card(
    h(
      "div",
      { class: "flex items-start justify-between gap-3" },
      h(
        "div",
        {},
        h(
          "p",
          { class: "inline-flex items-center gap-1.5 text-lg font-semibold text-slate-900" },
          technician.full_name,
          verifiedBadge(technician.is_verified),
        ),
        h("p", { class: "text-xs text-slate-500" }, `${technician.experience_years} años de experiencia`),
        location
          ? h("p", { class: "mt-1 inline-flex items-center gap-1 text-xs text-slate-500" }, icon("map-pin", { size: 13 }), location)
          : null,
      ),
    ),
    h("p", { class: "mt-3 line-clamp-3 text-sm text-slate-600" }, technician.bio || "Técnico sin descripción."),
    h(
      "div",
      { class: "mt-3 flex flex-wrap gap-2" },
      (technician.specialties || []).map((specialty) =>
        h("span", { class: "rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600" }, specialty.name),
      ),
    ),
    h(
      "div",
      { class: "mt-4 flex items-center justify-between gap-3" },
      h(
        "span",
        { class: "inline-flex items-center gap-2" },
        stars(technician.rating_avg, { showValue: true }),
        h("span", { class: "text-xs text-slate-500" }, `(${technician.rating_count})`),
      ),
      button("Ver perfil", { variant: "outline", iconName: "user", onClick: () => navigate(routes.technicianProfile(technician.id)) }),
    ),
  );
}
