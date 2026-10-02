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

const FOCUS =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background";

const VARIANTS = {
  primary: "bg-primary text-primary-foreground hover:bg-primary-hover",
  success: "bg-success text-success-foreground hover:opacity-90",
  danger: "bg-danger text-danger-foreground hover:opacity-90",
  ghost: "border border-border text-foreground-secondary hover:bg-surface-hover",
  outline: "border border-border bg-surface text-foreground hover:bg-surface-hover",
  neutral: "border border-border bg-surface text-foreground hover:bg-surface-hover",
  "danger-ghost": "border border-border text-danger hover:bg-danger-tint",
};

const SIZES = {
  sm: "min-h-9 px-3 py-1.5 text-sm",
  md: "min-h-11 px-4 py-2 text-sm",
};

export function button(
  label,
  {
    variant = "primary",
    size = "md",
    onClick,
    disabled = false,
    loading = false,
    type = "button",
    class: extra = "",
    iconName,
    iconSize = 16,
    iconNode,
    ariaLabel,
  } = {},
) {
  const leading = loading
    ? icon("loader-2", { size: iconSize, class: "animate-spin" })
    : iconNode || (iconName ? icon(iconName, { size: iconSize }) : null);
  const node = h(
    "button",
    {
      type,
      class: `inline-flex items-center justify-center gap-2 rounded-md font-semibold transition focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50 ${FOCUS} ${SIZES[size] || SIZES.md} ${VARIANTS[variant] || VARIANTS.primary} ${extra}`,
      "aria-label": ariaLabel,
      "aria-busy": loading ? "true" : null,
    },
    leading,
    label,
  );
  if (disabled || loading) node.disabled = true;
  if (onClick) node.addEventListener("click", onClick);
  return node;
}

/**
 * Botón de solo icono. Exige `label` (texto accesible) y usa `title` para el
 * tooltip nativo; el área táctil es de 44px.
 */
export function iconButton(
  iconName,
  { label, onClick, variant = "ghost", size = "md", class: extra = "" } = {},
) {
  if (!label) throw new Error("iconButton requiere un label accesible");
  return button("", {
    variant,
    size,
    iconName,
    iconSize: 18,
    ariaLabel: label,
    class: `!px-0 ${size === "sm" ? "min-w-9" : "min-w-11"} ${extra}`,
    onClick,
  });
}

export function link(label, href, { class: extra = "" } = {}) {
  return h(
    "a",
    {
      href,
      class: `inline-flex min-h-11 items-center font-medium text-primary hover:text-primary-hover hover:underline ${FOCUS} ${extra}`,
      "data-link": "true",
    },
    label,
  );
}

/**
 * Campo etiquetado. El tercer argumento acepta un string (ayuda) o un objeto
 * `{ hint, error }`; el error se anuncia con `role="alert"` y no depende solo
 * del color.
 */
export function field(label, control, options) {
  const hint = typeof options === "string" ? options : options?.hint;
  const error = typeof options === "object" && options ? options.error : null;
  return h(
    "label",
    { class: "block min-w-0 space-y-1" },
    h("span", { class: "block text-sm font-medium text-foreground-secondary" }, label),
    control,
    error
      ? h("span", { class: "block text-xs font-medium text-danger", role: "alert" }, error)
      : hint
        ? h("span", { class: "block text-xs text-muted" }, hint)
        : null,
  );
}

export function input({
  type = "text",
  name,
  value = "",
  placeholder = "",
  required = false,
  min,
  max,
  step,
  pattern,
  minlength,
  maxlength,
  autocomplete,
  accept,
  multiple,
} = {}) {
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
 * Campo de contraseña con botón para mostrarla u ocultarla. Reutiliza `input()`
 * y expone un botón accesible (`aria-label` y `aria-pressed` sincronizados).
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
      class: `absolute inset-y-0 right-0 flex min-w-11 items-center justify-center rounded-r-md text-muted hover:text-foreground ${FOCUS}`,
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

export function textarea({
  name,
  value = "",
  placeholder = "",
  rows = 4,
  required = false,
  minlength,
} = {}) {
  return h(
    "textarea",
    { name, rows, placeholder, required, minlength, class: "field-input" },
    value,
  );
}

export function select(name, options, { value = "", required = false } = {}) {
  const node = h("select", { name, required, class: "field-input" });
  for (const option of options) {
    node.append(
      h(
        "option",
        { value: option.value, selected: String(option.value) === String(value) },
        option.label,
      ),
    );
  }
  return node;
}

export function card(...children) {
  return h("div", { class: "min-w-0 rounded-lg border border-border bg-surface p-4" }, ...children);
}

export function sectionTitle(title, actions) {
  return h(
    "div",
    { class: "flex flex-wrap items-center justify-between gap-2" },
    h("h2", { class: "text-lg font-semibold text-foreground" }, title),
    actions || null,
  );
}

const BADGE = {
  open: "bg-primary-tint text-primary",
  quoted: "bg-warning-tint text-warning",
  accepted: "bg-primary-tint text-primary",
  in_progress: "bg-info-tint text-info",
  completed: "bg-success-tint text-success",
  cancelled: "bg-danger-tint text-danger",
  pending: "bg-surface-hover text-foreground-secondary",
  rejected: "bg-danger-tint text-danger",
  withdrawn: "bg-surface-hover text-muted",
  archived: "bg-surface-strong text-foreground-secondary",
  closed: "bg-surface-strong text-foreground-secondary",
  awaiting_receipt: "bg-surface-hover text-foreground-secondary",
  received: "bg-primary-tint text-primary",
  diagnosis: "bg-primary-tint text-primary",
  waiting_customer: "bg-warning-tint text-warning",
  waiting_part: "bg-warning-tint text-warning",
  in_repair: "bg-info-tint text-info",
  testing: "bg-primary-tint text-primary",
  ready: "bg-success-tint text-success",
  repaired: "bg-success-tint text-success",
  not_repairable: "bg-danger-tint text-danger",
  approved: "bg-success-tint text-success",
};

export function badge(value, label) {
  return h(
    "span",
    {
      class: `inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${BADGE[value] || "bg-surface-hover text-foreground-secondary"}`,
    },
    label || statusLabel(value),
  );
}

export function pageHeader(title, subtitle, actions) {
  return h(
    "div",
    {
      class:
        "flex flex-col gap-3 border-b border-border pb-5 sm:flex-row sm:items-center sm:justify-between",
    },
    h(
      "div",
      {},
      h("h1", { class: "text-2xl font-bold text-foreground" }, title),
      subtitle ? h("p", { class: "mt-1 text-sm text-muted" }, subtitle) : null,
    ),
    actions ? h("div", { class: "flex flex-wrap gap-2" }, actions) : null,
  );
}

export function setContent(node, ...children) {
  node.replaceChildren(...children.flat());
  return node;
}
