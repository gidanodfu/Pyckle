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

import { h, statusLabel } from "../dom.js";
import { icon } from "../icons.js";

const VARIANTS = {
  primary: "bg-blue-700 hover:bg-blue-800 text-white shadow-sm",
  success: "bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm",
  danger: "bg-red-600 hover:bg-red-700 text-white shadow-sm",
  ghost: "bg-transparent hover:bg-slate-100 text-slate-700 border border-slate-300",
  outline: "bg-white hover:bg-slate-50 text-blue-800 border border-blue-200",
  neutral: "bg-white hover:bg-slate-50 text-slate-700 border border-slate-300",
};

export function button(
  label,
  {
    variant = "primary",
    onClick,
    disabled = false,
    type = "button",
    class: extra = "",
    iconName,
    iconSize = 16,
    iconNode,
    ariaLabel,
  } = {},
) {
  const leading = iconNode || (iconName ? icon(iconName, { size: iconSize }) : null);
  const node = h(
    "button",
    {
      type,
      class: `inline-flex min-h-11 items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 ${VARIANTS[variant]} ${extra}`,
      "aria-label": ariaLabel,
    },
    leading,
    label,
  );
  if (disabled) node.disabled = true;
  if (onClick) node.addEventListener("click", onClick);
  return node;
}

export function link(label, href, { class: extra = "" } = {}) {
  return h(
    "a",
    { href, class: `inline-flex min-h-11 items-center font-medium text-blue-700 hover:text-blue-900 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 ${extra}`, "data-link": "true" },
    label,
  );
}

export function field(label, control, hint) {
  return h(
    "label",
    { class: "block space-y-1" },
    h("span", { class: "block text-sm font-medium text-slate-700" }, label),
    control,
    hint ? h("span", { class: "block text-xs text-slate-500" }, hint) : null,
  );
}

export function input({ type = "text", name, value = "", placeholder = "", required = false, min, max, step, pattern, minlength, maxlength, autocomplete, accept, multiple } = {}) {
  return h("input", {
    type,
    name,
    value,
    placeholder,
    required,
    min,
    max,
    step,
    pattern,
    minlength,
    maxlength,
    autocomplete,
    accept,
    multiple,
    class: "field-input",
  });
}

/**
 * Campo de contraseña con botón para mostrarla u ocultarla.
 *
 * Reutiliza `input()` y expone un botón accesible (foco por teclado, `aria-label`
 * y `aria-pressed` sincronizados). No interviene en el envío del formulario.
 */
export function passwordInput({
  name = "password",
  required = false,
  minlength,
  autocomplete = "current-password",
  placeholder = "",
} = {}) {
  const control = input({
    name,
    type: "password",
    required,
    minlength,
    autocomplete,
    placeholder,
  });
  control.classList.add("pr-11");
  const toggle = h(
    "button",
    {
      type: "button",
      class:
        "absolute inset-y-0 right-0 flex min-w-11 items-center justify-center rounded-r-lg text-slate-500 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500",
      "aria-label": "Mostrar contraseña",
      "aria-pressed": "false",
    },
    icon("eye", { size: 18 }),
  );
  toggle.addEventListener("click", (event) => {
    event.preventDefault();
    const show = control.type === "password";
    control.type = show ? "text" : "password";
    toggle.setAttribute("aria-pressed", show ? "true" : "false");
    toggle.setAttribute("aria-label", show ? "Ocultar contraseña" : "Mostrar contraseña");
    toggle.replaceChildren(icon(show ? "eye-off" : "eye", { size: 18 }));
  });
  return h("div", { class: "relative" }, control, toggle);
}

export function textarea({ name, value = "", placeholder = "", rows = 4, required = false, minlength } = {}) {
  return h("textarea", { name, rows, placeholder, required, minlength, class: "field-input" }, value);
}

export function select(name, options, { value = "", required = false } = {}) {
  const node = h("select", { name, required, class: "field-input" });
  for (const option of options) {
    node.append(
      h("option", { value: option.value, selected: String(option.value) === String(value) }, option.label),
    );
  }
  return node;
}

export function card(...children) {
  return h("div", { class: "rounded-xl border border-slate-200 bg-white p-5 shadow-sm" }, ...children);
}

export function sectionTitle(title, actions) {
  return h(
    "div",
    { class: "flex flex-wrap items-center justify-between gap-2" },
    h("h2", { class: "text-lg font-semibold text-slate-900" }, title),
    actions || null,
  );
}

export function badge(value, label) {
  const palette = {
    open: "bg-blue-100 text-blue-800",
    quoted: "bg-amber-100 text-amber-800",
    accepted: "bg-indigo-100 text-indigo-800",
    in_progress: "bg-cyan-100 text-cyan-800",
    completed: "bg-emerald-100 text-emerald-800",
    cancelled: "bg-red-100 text-red-800",
    pending: "bg-slate-100 text-slate-700",
    rejected: "bg-red-100 text-red-700",
    withdrawn: "bg-slate-100 text-slate-600",
    archived: "bg-slate-200 text-slate-700",
    closed: "bg-slate-200 text-slate-700",
    awaiting_receipt: "bg-slate-100 text-slate-700",
    received: "bg-blue-100 text-blue-800",
    diagnosis: "bg-indigo-100 text-indigo-800",
    waiting_customer: "bg-amber-100 text-amber-800",
    waiting_part: "bg-amber-100 text-amber-800",
    in_repair: "bg-cyan-100 text-cyan-800",
    testing: "bg-violet-100 text-violet-800",
    ready: "bg-emerald-100 text-emerald-800",
    repaired: "bg-emerald-100 text-emerald-800",
    not_repairable: "bg-red-100 text-red-700",
    approved: "bg-emerald-100 text-emerald-800",
  };
  return h(
    "span",
    { class: `inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${palette[value] || "bg-slate-100 text-slate-700"}` },
    label || statusLabel(value),
  );
}

export function pageHeader(title, subtitle, actions) {
  return h(
    "div",
    { class: "flex flex-col gap-3 border-b border-slate-200 pb-5 sm:flex-row sm:items-center sm:justify-between" },
    h(
      "div",
      {},
      h("h1", { class: "text-2xl font-bold text-slate-900" }, title),
      subtitle ? h("p", { class: "mt-1 text-sm text-slate-500" }, subtitle) : null,
    ),
    actions ? h("div", { class: "flex flex-wrap gap-2" }, actions) : null,
  );
}

export function setContent(node, ...children) {
  node.replaceChildren(...children.flat());
  return node;
}
