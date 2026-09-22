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
import { alert, button, card, field, textarea } from "../../../components/ui/index.js";

const DETAIL_ROWS = [
  ["Diagnóstico técnico", "diagnosis"],
  ["Trabajo realizado", "work_performed"],
  ["Pruebas realizadas", "tests_performed"],
  ["Notas internas (no visibles al cliente)", "technician_notes"],
];

/**
 * Detalles técnicos de la reparación: formulario para el técnico asignado y
 * vista de solo lectura (p. ej. administrador) cuando ``canManage`` es falso.
 */
export function detailsCard(order, { canManage, onChanged } = {}) {
  if (!canManage) {
    return card(
      h("h3", { class: "mb-3 text-lg font-semibold text-slate-900" }, "Detalles técnicos"),
      h(
        "dl",
        { class: "space-y-3 text-sm" },
        DETAIL_ROWS.map(([label, field]) =>
          h(
            "div",
            {},
            h("dt", { class: "text-xs uppercase tracking-wide text-slate-500" }, label),
            h(
              "dd",
              { class: "mt-0.5 whitespace-pre-line text-slate-700" },
              order[field] || "-",
            ),
          ),
        ),
      ),
    );
  }

  const form = h(
    "form",
    { class: "space-y-3" },
    h("div", { "data-error": "true" }),
    field(
      "Diagnóstico técnico",
      textarea({ name: "diagnosis", rows: 3, value: order.diagnosis || "" }),
    ),
    field(
      "Trabajo realizado",
      textarea({ name: "work_performed", rows: 3, value: order.work_performed || "" }),
    ),
    field(
      "Pruebas realizadas",
      textarea({ name: "tests_performed", rows: 2, value: order.tests_performed || "" }),
    ),
    field(
      "Notas internas (no visibles al cliente)",
      textarea({ name: "technician_notes", rows: 2, value: order.technician_notes || "" }),
    ),
    button("Guardar detalles", { type: "submit", variant: "outline", iconName: "save" }),
  );
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const errorBox = form.querySelector("[data-error]");
    const submit = form.querySelector("button[type=submit]");
    errorBox.replaceChildren();
    submit.disabled = true;
    try {
      await api.put(
        endpoints.orders.repairDetails(order.id),
        Object.fromEntries(new FormData(form)),
      );
      onChanged();
    } catch (error) {
      errorBox.replaceChildren(alert(error.message || "No se pudieron guardar los detalles"));
      submit.disabled = false;
    }
  });
  return card(
    h("h3", { class: "mb-3 text-lg font-semibold text-slate-900" }, "Detalles técnicos"),
    form,
  );
}
