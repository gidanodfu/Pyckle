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
import { formatDate, formatMoney, h } from "../../../components/dom.js";
import { icon } from "../../../components/icons.js";
import { alert, badge, button, card, field, input, stars, textarea, verifiedBadge, withBusy } from "../../../components/ui/index.js";
import { routes } from "../../../lib/paths.js";
import { navigate } from "../../../lib/navigation.js";

export function quotationCard(quotation, { isOwner }) {
  const canAccept = isOwner && quotation.status === "pending";
  const technician = quotation.technician;
  const reviews = quotation.technician_reviews || [];
  return card(
    h(
      "div",
      { class: "flex flex-wrap items-start justify-between gap-3" },
      h(
        "div",
        {},
        h("p", { class: "font-semibold text-slate-800" }, technician.full_name),
        h(
          "div",
          { class: "mt-1 flex flex-wrap items-center gap-3" },
          h("span", { class: "inline-flex items-center gap-2" }, stars(technician.rating_avg, { showValue: true }), h("span", { class: "text-xs text-slate-500" }, `${technician.rating_count} reseñas`)),
          verifiedBadge(technician.is_verified),
          technician.district_name ? h("span", { class: "inline-flex items-center gap-1 text-xs text-slate-500" }, icon("map-pin", { size: 12 }), technician.district_name) : null,
        ),
        h("p", { class: "mt-1 text-xs text-slate-500" }, `${formatDate(quotation.created_at)} · ${quotation.estimated_days} día(s)`),
      ),
      h("div", { class: "flex items-center gap-2" }, h("span", { class: "text-lg font-bold text-emerald-700" }, formatMoney(quotation.price)), badge(quotation.status)),
    ),
    h("p", { class: "mt-3 text-sm text-slate-600" }, quotation.preliminary_diagnosis),
    (quotation.items || []).length
      ? h(
          "ul",
          { class: "mt-3 space-y-1 text-sm text-slate-600" },
          quotation.items.map((item) =>
            h(
              "li",
              { class: "flex justify-between" },
              h("span", {}, `${item.description} x${item.quantity}`),
              h("span", {}, formatMoney(item.total)),
            ),
          ),
        )
      : null,
    reviews.length
      ? h(
          "details",
          { class: "mt-3 rounded-lg bg-slate-50 p-3 text-sm" },
          h("summary", { class: "cursor-pointer font-medium text-slate-700" }, `Reseñas recientes (${reviews.length})`),
          h(
            "div",
            { class: "mt-2 space-y-2" },
            reviews.map((review) =>
              h(
                "div",
                { class: "rounded-lg bg-white p-2.5" },
                h(
                  "div",
                  { class: "flex items-center justify-between gap-2" },
                  h("span", { class: "text-xs font-semibold text-slate-700" }, review.customer_name),
                  stars(review.rating, { size: 12 }),
                ),
                review.comment ? h("p", { class: "mt-1 text-xs text-slate-600" }, review.comment) : null,
                h("p", { class: "mt-0.5 text-[11px] text-slate-500" }, formatDate(review.created_at)),
              ),
            ),
          ),
        )
      : h("p", { class: "mt-2 text-xs text-slate-500" }, "Este técnico aún no tiene reseñas."),
    canAccept
      ? h(
          "div",
          { class: "mt-4" },
          button("Aceptar cotización", {
            variant: "success",
            iconName: "check",
            onClick: (event) =>
              withBusy(event.currentTarget, async () => {
                if (!window.confirm("Al aceptar se creará la orden y se rechazarán las demás cotizaciones. ¿Continuar?")) return;
                try {
                  const order = await api.post(endpoints.quotations.accept(quotation.id), {});
                  navigate(routes.orderDetail(order.id));
                } catch (error) {
                  window.alert(error.message || "No se pudo aceptar la cotización");
                }
              }),
          }),
        )
      : null,
  );
}

export function quoteFormCard(requestId) {
  const form = h(
    "form",
    { class: "space-y-3" },
    h("div", { "data-error": "true" }),
    field("Precio (S/)", input({ name: "price", type: "number", min: 0.01, step: "0.01", required: true })),
    field("Diagnóstico preliminar", textarea({ name: "preliminary_diagnosis", required: true, rows: 3 })),
    field("Tiempo estimado (días)", input({ name: "estimated_days", type: "number", min: 1, value: 1 })),
    button("Enviar cotización", { type: "submit", class: "w-full", iconName: "send" }),
  );
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const errorBox = form.querySelector("[data-error]");
    const submit = form.querySelector("button[type=submit]");
    errorBox.replaceChildren();
    submit.disabled = true;
    const data = Object.fromEntries(new FormData(form).entries());
    try {
      await api.post(endpoints.quotations.create, {
        request_id: requestId,
        price: data.price,
        preliminary_diagnosis: data.preliminary_diagnosis,
        estimated_days: Number(data.estimated_days),
      });
      navigate(routes.requestDetail(requestId));
    } catch (error) {
      errorBox.replaceChildren(alert(error.message || "No se pudo enviar la cotización"));
      submit.disabled = false;
    }
  });
  return card(h("h3", { class: "mb-3 text-lg font-semibold text-slate-900" }, "Enviar cotización"), form);
}
