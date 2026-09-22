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
import { Container } from "../../components/layout/index.js";
import { card, emptyState, pageHeader, stars, verifiedBadge } from "../../components/ui/index.js";

export async function TechnicianProfile({ id }) {
  const [technician, reviews] = await Promise.all([
    api.get(endpoints.technicians.byId(id), { auth: false }),
    api.get(endpoints.technicians.reviews(id), { auth: false }),
  ]);

  return Container(
    h(
      "div",
      { class: "mx-auto max-w-3xl" },
      pageHeader(
        h(
          "span",
          { class: "inline-flex items-center gap-2" },
          technician.full_name,
          verifiedBadge(technician.is_verified, { size: 20 }),
        ),
        technician.bio || "Técnico de Pyckle",
      ),
      h(
        "div",
        { class: "mt-6 grid gap-4 sm:grid-cols-3" },
        card(
          h("p", { class: "text-sm text-slate-500" }, "Experiencia"),
          h("p", { class: "text-xl font-bold text-blue-800" }, `${technician.experience_years} años`),
        ),
        card(
          h("p", { class: "text-sm text-slate-500" }, "Calificación"),
          h("div", { class: "mt-1" }, stars(technician.rating_avg, { size: 18, showValue: true })),
          h("p", { class: "text-xs text-slate-500" }, `${technician.rating_count} reseñas`),
        ),
        card(
          h("p", { class: "text-sm text-slate-500" }, "Servicios"),
          h(
            "p",
            { class: "text-sm font-medium text-slate-700" },
            [technician.offers_home_service ? "Domicilio" : null, technician.offers_workshop_service ? "Taller" : null]
              .filter(Boolean)
              .join(" y ") || "-",
          ),
        ),
      ),
      h("h2", { class: "mt-8 text-lg font-semibold text-slate-900" }, "Especialidades"),
      h(
        "div",
        { class: "mt-3 flex flex-wrap gap-2" },
        (technician.specialties || []).length
          ? technician.specialties.map((specialty) =>
              h("span", { class: "rounded-full border border-slate-200 px-3 py-1 text-sm" }, specialty.name),
            )
          : h("p", { class: "text-sm text-slate-500" }, "Sin especialidades registradas."),
      ),
      h("h2", { class: "mt-8 text-lg font-semibold text-slate-900" }, `Reseñas (${reviews.length})`),
      h(
        "div",
        { class: "mt-3 space-y-3" },
        reviews.length
          ? reviews.map((review) =>
              card(
                h(
                  "div",
                  { class: "flex items-center justify-between gap-2" },
                  h("p", { class: "font-medium text-slate-800" }, review.customer_name),
                  stars(review.rating),
                ),
                review.comment ? h("p", { class: "mt-2 text-sm text-slate-600" }, review.comment) : null,
                h("p", { class: "mt-1 text-xs text-slate-500" }, formatDate(review.created_at)),
              ),
            )
          : emptyState("Sin reseñas", "Este técnico aún no tiene calificaciones.", null, { iconName: "star" }),
      ),
    ),
  );
}
