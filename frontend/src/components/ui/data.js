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
      class: "inline-flex items-center text-blue-700",
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
  const wrapper = h("span", { class: "inline-flex items-center gap-1", role: "img", "aria-label": `${value} de 5` });
  const row = h("span", { class: "inline-flex items-center" });
  for (let index = 1; index <= 5; index += 1) {
    row.append(
      icon("star", {
        size,
        class: index <= filled ? "fill-amber-400 text-amber-500" : "text-slate-300",
      }),
    );
  }
  wrapper.append(row);
  if (showValue) wrapper.append(h("span", { class: "text-sm font-semibold text-amber-700" }, value.toFixed(1)));
  return wrapper;
}

const ALIGN_CLASS = { left: "text-left", center: "text-center", right: "text-right" };

function cellClass(align) {
  return `px-4 py-3 text-sm text-slate-700 ${ALIGN_CLASS[align] || "text-left"}`;
}

export function table(columns, rows) {
  const normalized = columns.map((column) =>
    typeof column === "string" ? { label: column, align: "left" } : column,
  );
  const head = h(
    "thead",
    { class: "bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500" },
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
    { class: "divide-y divide-slate-100" },
    rows.map((row) =>
      h(
        "tr",
        { class: "hover:bg-slate-50" },
        row.map((cell, index) => h("td", { class: cellClass(normalized[index]?.align) }, cell)),
      ),
    ),
  );
  return h(
    "div",
    { class: "overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm" },
    h("table", { class: "min-w-full divide-y divide-slate-200" }, head, body),
  );
}

export function statCard(label, value, { accent = "text-blue-800", iconName } = {}) {
  return card(
    h(
      "div",
      { class: "flex items-start justify-between gap-3" },
      h(
        "div",
        {},
        h("p", { class: "text-sm text-slate-500" }, label),
        h("p", { class: `mt-1 text-2xl font-bold ${accent}` }, value),
      ),
      iconName
        ? h("span", { class: "flex h-9 w-9 items-center justify-center rounded-lg bg-slate-100 text-slate-500" }, icon(iconName, { size: 18 }))
        : null,
    ),
  );
}
