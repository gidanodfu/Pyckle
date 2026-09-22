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
import { alert, button, card, field, input, textarea } from "../../../components/ui/index.js";

/** Acciones de cierre: completar, declarar no reparable o cancelar. */
export function closeActionsCard(order, reload) {
  const completeForm = h(
    "form",
    { class: "space-y-3" },
    h("div", { "data-error": "true" }),
    field(
      "Precio final (S/)",
      input({
        name: "final_price",
        type: "number",
        min: 0,
        step: "0.01",
        value: order.final_price,
      }),
    ),
    button("Completar reparación", {
      type: "submit",
      variant: "success",
      iconName: "circle-check",
    }),
  );
  completeForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const errorBox = completeForm.querySelector("[data-error]");
    const submit = completeForm.querySelector("button[type=submit]");
    submit.disabled = true;
    try {
      await api.post(endpoints.orders.complete(order.id), {
        final_price: Number(new FormData(completeForm).get("final_price")),
      });
      reload();
    } catch (error) {
      errorBox.replaceChildren(alert(error.message || "No se pudo completar"));
      submit.disabled = false;
    }
  });

  const reasonInput = textarea({ name: "reason", rows: 2, placeholder: "Motivo / diagnóstico" });
  const diagnosisInput = textarea({
    name: "diagnosis",
    rows: 2,
    placeholder: "Diagnóstico técnico",
  });
  const notRepairableForm = h(
    "form",
    { class: "space-y-3" },
    h("div", { "data-error": "true" }),
    field("Motivo", reasonInput),
    field("Diagnóstico", diagnosisInput),
    button("Declarar no reparable", {
      type: "submit",
      variant: "danger",
      iconName: "circle-x",
    }),
  );
  notRepairableForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const errorBox = notRepairableForm.querySelector("[data-error]");
    const submit = notRepairableForm.querySelector("button[type=submit]");
    submit.disabled = true;
    try {
      await api.post(endpoints.orders.notRepairable(order.id), {
        reason: reasonInput.value.trim(),
        diagnosis: diagnosisInput.value.trim(),
      });
      reload();
    } catch (error) {
      errorBox.replaceChildren(alert(error.message || "No se pudo declarar no reparable"));
      submit.disabled = false;
    }
  });

  const cancelInput = input({ name: "reason", placeholder: "Motivo de cancelación" });
  const cancelForm = h(
    "form",
    { class: "space-y-3" },
    h("div", { "data-error": "true" }),
    field("Cancelar reparación", cancelInput),
    button("Cancelar", { type: "submit", variant: "ghost", iconName: "ban" }),
  );
  cancelForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const errorBox = cancelForm.querySelector("[data-error]");
    if (!cancelInput.value.trim()) return;
    const submit = cancelForm.querySelector("button[type=submit]");
    submit.disabled = true;
    try {
      await api.post(endpoints.orders.cancel(order.id), {
        reason: cancelInput.value.trim(),
      });
      reload();
    } catch (error) {
      errorBox.replaceChildren(alert(error.message || "No se pudo cancelar"));
      submit.disabled = false;
    }
  });

  return card(
    h("h3", { class: "mb-3 text-lg font-semibold text-slate-900" }, "Cierre"),
    completeForm,
    h("hr", { class: "my-4 border-slate-200" }),
    notRepairableForm,
    h("hr", { class: "my-4 border-slate-200" }),
    cancelForm,
  );
}
