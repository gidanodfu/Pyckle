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

import { h } from "../dom.js";
import { icon } from "../icons.js";
import { card } from "./primitives.js";

/**
 * Badge de verificación. Solo se renderiza cuando el backend confirma
 * `verified === true`; el icono es decorativo y la etiqueta accesible comunica
 * el estado sin depender del color.
 */
export function verifiedBadge(verified, { label = "Técnico verificado", size = 16 } = {}) {
  if (verified !== true) return null;
  return h(
    "span",
    {
      class: "inline-flex items-center text-primary",
      role: "img",
      "aria-label": label,
      title: label,
    },
    icon("badge-check", { size }),
  );
}

export function stars(rating, { size = 14, showValue = false } = {}) {
  const value = Number(rating || 0);
  const filled = Math.round(value);
  const wrapper = h("span", {
    class: "inline-flex items-center gap-1",
    role: "img",
    "aria-label": `${value} de 5`,
  });
  const row = h("span", { class: "inline-flex items-center" });
  for (let index = 1; index <= 5; index += 1) {
    row.append(
      icon("star", {
        size,
        class: index <= filled ? "fill-warning text-warning" : "text-surface-strong",
      }),
    );
  }
  wrapper.append(row);
  if (showValue) {
    wrapper.append(h("span", { class: "text-sm font-semibold text-warning" }, value.toFixed(1)));
  }
  return wrapper;
}

const ALIGN_CLASS = { left: "text-left", center: "text-center", right: "text-right" };

function cellClass(align) {
  return `px-4 py-3 text-sm text-foreground-secondary ${ALIGN_CLASS[align] || "text-left"}`;
}

export function table(columns, rows) {
  const normalized = columns.map((column) =>
    typeof column === "string" ? { label: column, align: "left" } : column,
  );
  const head = h(
    "thead",
    { class: "bg-surface-hover text-xs font-semibold uppercase tracking-wide text-muted" },
    h(
      "tr",
      {},
      normalized.map((column) =>
        h(
          "th",
          { scope: "col", class: `px-4 py-3 ${ALIGN_CLASS[column.align] || "text-left"}` },
          column.label,
        ),
      ),
    ),
  );
  const body = h(
    "tbody",
    { class: "divide-y divide-border-subtle" },
    rows.map((row) =>
      h(
        "tr",
        { class: "hover:bg-surface-hover" },
        row.map((cell, index) =>
          h(
            "td",
            {
              class: cellClass(normalized[index]?.align),
              "data-label": normalized[index]?.label || "",
            },
            cell,
          ),
        ),
      ),
    ),
  );
  // En móvil la tabla se reflowa a fichas usando `data-label` (sin scroll
  // horizontal). El contenedor es una región enfocable por teclado.
  return h(
    "div",
    {
      class: "responsive-table overflow-x-auto rounded-lg border border-border bg-surface",
      tabindex: "0",
      role: "region",
      "aria-label": "Tabla de datos",
    },
    h("table", { class: "min-w-full divide-y divide-border" }, head, body),
  );
}

export function statCard(label, value, { accent = "text-foreground", iconName } = {}) {
  return card(
    h(
      "div",
      { class: "flex items-start justify-between gap-3" },
      h(
        "div",
        {},
        h("p", { class: "text-sm text-muted" }, label),
        h("p", { class: `mt-1 text-2xl font-bold tabular-nums ${accent}` }, value),
      ),
      iconName
        ? h(
            "span",
            { class: "flex h-9 w-9 items-center justify-center rounded-md bg-surface-hover text-muted" },
            icon(iconName, { size: 18 }),
          )
        : null,
    ),
  );
}
