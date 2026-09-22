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

import { api } from "../../../api/client.js";
import { endpoints } from "../../../api/endpoints.js";
import { h } from "../../../components/dom.js";
import { alert, button, card, field, select, stars, textarea } from "../../../components/ui/index.js";
import { routes } from "../../../lib/paths.js";
import { navigate } from "../../../lib/navigation.js";

export function reviewForm(orderId) {
  const form = h(
    "form",
    { class: "space-y-3" },
    h("div", { "data-error": "true" }),
    field("Calificación", select("rating", [5, 4, 3, 2, 1].map((value) => ({ value, label: `${value} estrellas` })))),
    field("Comentario", textarea({ name: "comment", rows: 3, placeholder: "Cuenta tu experiencia" })),
    button("Enviar reseña", { type: "submit", variant: "success", class: "w-full", iconName: "send" }),
  );
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const errorBox = form.querySelector("[data-error]");
    const data = new FormData(form);
    try {
      await api.post(endpoints.reviews.create, {
        order_id: orderId,
        rating: Number(data.get("rating")),
        comment: data.get("comment") || null,
      });
      navigate(routes.orderDetail(orderId));
    } catch (error) {
      errorBox.replaceChildren(alert(error.message || "No se pudo enviar la reseña"));
    }
  });
  return card(
    h("h3", { class: "mb-3 text-lg font-semibold text-slate-900" }, "Califica el servicio"),
    h("div", { class: "mb-3" }, stars(5)),
    form,
  );
}
