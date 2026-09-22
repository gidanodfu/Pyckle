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
import { formatDate, formatMoney, h, statusLabel } from "../../../components/dom.js";
import { icon } from "../../../components/icons.js";
import {
  alert,
  badge,
  button,
  card,
  field,
  input,
  textarea,
  withBusy,
} from "../../../components/ui/index.js";

/**
 * Propuestas de cambio de precio. El cliente aprueba/rechaza; el técnico propone.
 * El backend valida la autorización y bloquea el trabajo facturable sin aprobación.
 */
export function priceChangesCard(order, { isCustomer, canManage, onChanged }) {
  const changes = order.price_changes || [];
  const pending = changes.find((change) => change.status === "pending");
  const terminal = ["completed", "cancelled"].includes(order.status);

  const rows = changes.length
    ? h(
        "ul",
        { class: "space-y-2" },
        changes.map((change) =>
          h(
            "li",
            { class: "rounded-lg border border-slate-200 p-3 text-sm" },
            h(
              "div",
              { class: "flex flex-wrap items-center justify-between gap-2" },
              h(
                "span",
                { class: "font-medium text-slate-800" },
                `${formatMoney(change.previous_price)} -> ${formatMoney(change.new_price)}`,
              ),
              badge(change.status),
            ),
            h("p", { class: "mt-1 text-slate-600" }, change.reason),
            change.decided_note
              ? h("p", { class: "mt-1 text-xs text-slate-500" }, change.decided_note)
              : null,
            h("p", { class: "mt-1 text-xs text-slate-500" }, formatDate(change.created_at)),
          ),
        ),
      )
    : h("p", { class: "text-sm text-slate-500" }, "Sin cambios de precio registrados.");

  const children = [
    h(
      "h3",
      { class: "mb-3 flex items-center gap-2 text-lg font-semibold text-slate-900" },
      icon("receipt", { size: 18 }),
      "Cotización y cambios de precio",
    ),
    h(
      "p",
      { class: "mb-3 text-xs text-slate-500" },
      "La cotización inicial no garantiza el precio final. Todo cambio queda registrado.",
    ),
    rows,
  ];

  if (isCustomer && pending) {
    children.push(
      h(
        "div",
        { class: "mt-4 flex flex-wrap gap-2 rounded-lg bg-amber-50 p-3" },
        h(
          "p",
          { class: "w-full text-sm font-medium text-amber-800" },
          `Nuevo costo propuesto: ${formatMoney(pending.new_price)}`,
        ),
        button("Aceptar nuevo costo", {
          variant: "success",
          iconName: "check",
          onClick: (event) =>
            withBusy(event.currentTarget, async () => {
              try {
                await api.post(endpoints.orders.approvePriceChange(order.id, pending.id), {});
                onChanged();
              } catch (error) {
                window.alert(error.message || "No se pudo aprobar el cambio");
              }
            }),
        }),
        button("Rechazar", {
          variant: "ghost",
          iconName: "x",
          onClick: (event) =>
            withBusy(event.currentTarget, async () => {
              try {
                await api.post(endpoints.orders.rejectPriceChange(order.id, pending.id), {});
                onChanged();
              } catch (error) {
                window.alert(error.message || "No se pudo rechazar el cambio");
              }
            }),
        }),
      ),
    );
  }

  if (canManage && !terminal && !pending) {
    const priceInput = input({ name: "new_price", type: "number", min: 0, step: "0.01", required: true });
    const reasonInput = textarea({ name: "reason", rows: 2, required: true, placeholder: "Motivo del nuevo costo" });
    const form = h(
      "form",
      { class: "mt-4 space-y-3" },
      h("div", { "data-error": "true" }),
      field("Nuevo precio (S/)", priceInput),
      field("Motivo", reasonInput),
      button("Proponer nuevo costo", { type: "submit", iconName: "send" }),
    );
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const errorBox = form.querySelector("[data-error]");
      const submit = form.querySelector("button[type=submit]");
      errorBox.replaceChildren();
      submit.disabled = true;
      try {
        await api.post(endpoints.orders.priceChanges(order.id), {
          new_price: Number(priceInput.value),
          reason: reasonInput.value.trim(),
        });
        onChanged();
      } catch (error) {
        errorBox.replaceChildren(alert(error.message || "No se pudo proponer el cambio"));
        submit.disabled = false;
      }
    });
    children.push(h("p", { class: "mt-4 text-sm font-semibold text-slate-700" }, "Proponer cambio"), form);
  }

  return card(...children);
}
