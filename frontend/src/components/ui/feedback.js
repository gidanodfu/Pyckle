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

export function spinner(label = "Cargando...") {
  return h(
    "div",
    { class: "flex items-center justify-center gap-3 py-12 text-slate-500" },
    icon("loader-2", { size: 20, class: "animate-spin text-blue-700" }),
    h("span", { class: "text-sm" }, label),
  );
}

export function emptyState(title, description, action, { iconName = "inbox" } = {}) {
  return h(
    "div",
    { class: "flex flex-col items-center gap-2 rounded-xl border border-dashed border-slate-300 bg-white px-6 py-12 text-center" },
    h("span", { class: "flex h-11 w-11 items-center justify-center rounded-full bg-slate-100 text-slate-500" }, icon(iconName, { size: 22 })),
    h("p", { class: "text-base font-semibold text-slate-700" }, title),
    description ? h("p", { class: "max-w-md text-sm text-slate-500" }, description) : null,
    action || null,
  );
}

export function alert(message, type = "error") {
  const palette = {
    error: "border-red-200 bg-red-50 text-red-800",
    success: "border-emerald-200 bg-emerald-50 text-emerald-800",
    info: "border-blue-200 bg-blue-50 text-blue-800",
    warning: "border-amber-200 bg-amber-50 text-amber-800",
  };
  const icons = { error: "alert-circle", success: "check-circle-2", info: "info", warning: "alert-triangle" };
  return h(
    "div",
    { class: `flex items-start gap-2 rounded-lg border px-4 py-3 text-sm ${palette[type]}`, role: "alert" },
    icon(icons[type], { size: 18, class: "mt-0.5" }),
    h("span", {}, message),
  );
}

export function loadingList(rows = 3) {
  const container = h("div", { class: "space-y-3" });
  for (let index = 0; index < rows; index += 1) {
    container.append(h("div", { class: "skeleton h-16 w-full" }));
  }
  return container;
}
