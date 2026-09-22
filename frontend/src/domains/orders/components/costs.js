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
import { formatMoney, h, statusLabel } from "../../../components/dom.js";
import { icon } from "../../../components/icons.js";
import {
  alert,
  button,
  card,
  field,
  input,
  select,
  withBusy,
} from "../../../components/ui/index.js";

const KIND_OPTIONS = [
  { value: "part", label: "Repuesto" },
  { value: "labor", label: "Servicio técnico" },
  { value: "other", label: "Otro" },
];

/** Desglose de costos. El backend solo entrega al cliente las líneas visibles. */
export function costsCard(order, { canManage, onChanged }) {
  const items = order.cost_items || [];
  const terminal = ["completed", "cancelled"].includes(order.status);

  const children = [
    h(
      "h3",
      { class: "mb-3 flex items-center gap-2 text-lg font-semibold text-slate-900" },
      icon("receipt", { size: 18 }),
      "Costos",
    ),
  ];

  children.push(
    items.length
      ? h(
          "dl",
          { class: "space-y-1 text-sm" },
          items.map((item) =>
            h(
              "div",
              { class: "flex items-center justify-between" },
              h(
                "dt",
                { class: "text-slate-600" },
                `${statusLabel(item.kind)}${item.description ? `: ${item.description}` : ""}`,
              ),
              h("dd", { class: "font-medium text-slate-800" }, formatMoney(item.amount)),
            ),
          ),
          h(
            "div",
            {
              class: "mt-2 flex items-center justify-between border-t border-slate-200 pt-2 font-semibold text-slate-900",
            },
            h("dt", {}, "Precio final"),
            h("dd", {}, formatMoney(order.final_price)),
          ),
        )
      : h("p", { class: "text-sm text-slate-500" }, "Sin costos registrados."),
  );

  if (canManage && !terminal) {
    const kindSelect = select("kind", KIND_OPTIONS, { value: "part" });
    const descriptionInput = input({ name: "description", required: true, placeholder: "Detalle" });
    const amountInput = input({ name: "amount", type: "number", min: 0, step: "0.01", required: true });
    const visibleCheckbox = h("input", { type: "checkbox", name: "visible", checked: true });
    const form = h(
      "form",
      { class: "mt-4 space-y-3" },
      h("div", { "data-error": "true" }),
      h(
        "div",
        { class: "grid gap-3 sm:grid-cols-2" },
        field("Tipo", kindSelect),
        field("Monto (S/)", amountInput),
      ),
      field("Descripción", descriptionInput),
      h(
        "label",
        { class: "flex items-center gap-2 text-sm text-slate-700" },
        visibleCheckbox,
        "Mostrar este costo al cliente",
      ),
      button("Agregar costo", { type: "submit", variant: "outline", iconName: "plus" }),
    );
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const errorBox = form.querySelector("[data-error]");
      const submit = form.querySelector("button[type=submit]");
      errorBox.replaceChildren();
      submit.disabled = true;
      try {
        await api.post(endpoints.orders.costs(order.id), {
          kind: kindSelect.value,
          description: descriptionInput.value.trim(),
          amount: Number(amountInput.value),
          visible_to_customer: visibleCheckbox.checked,
        });
        onChanged();
      } catch (error) {
        errorBox.replaceChildren(alert(error.message || "No se pudo agregar el costo"));
        submit.disabled = false;
      }
    });
    children.push(form);
  }

  return card(...children);
}
