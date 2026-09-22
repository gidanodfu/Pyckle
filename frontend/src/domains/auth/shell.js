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

import { Logo } from "../../components/brand.js";
import { h } from "../../components/dom.js";
import { Container } from "../../components/layout/index.js";
import { alert, card } from "../../components/ui/index.js";

export function authShell(title, subtitle, form) {
  return Container(
    h(
      "div",
      { class: "mx-auto mt-6 w-full max-w-md" },
      h("div", { class: "mb-6 flex justify-center" }, Logo({ size: 44 })),
      h("h1", { class: "text-center text-2xl font-bold text-slate-900" }, title),
      h("p", { class: "mt-1 text-center text-sm text-slate-500" }, subtitle),
      h("div", { class: "mt-6" }, card(form)),
    ),
  );
}

export function submitHandler(form, onError) {
  return async (event) => {
    event.preventDefault();
    const errorBox = form.querySelector("[data-error]");
    const submit = form.querySelector("button[type=submit]");
    // Guarda explícita contra doble submit (además del botón deshabilitado).
    if (submit.disabled) return;
    errorBox.replaceChildren();
    submit.disabled = true;
    try {
      await onError(form);
    } catch (error) {
      errorBox.replaceChildren(alert(error.message || "No se pudo completar la operación"));
    } finally {
      submit.disabled = false;
    }
  };
}
