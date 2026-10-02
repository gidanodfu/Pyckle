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
    { class: "flex items-center justify-center gap-3 py-12 text-muted" },
    icon("loader-2", { size: 20, class: "animate-spin text-primary" }),
    h("span", { class: "text-sm" }, label),
  );
}

export function emptyState(title, description, action, { iconName = "inbox" } = {}) {
  return h(
    "div",
    {
      class:
        "flex flex-col items-center gap-2 rounded-lg border border-dashed border-border bg-surface px-6 py-12 text-center",
    },
    h(
      "span",
      { class: "flex h-11 w-11 items-center justify-center rounded-full bg-surface-hover text-muted" },
      icon(iconName, { size: 22 }),
    ),
    h("p", { class: "text-base font-semibold text-foreground" }, title),
    description ? h("p", { class: "max-w-md text-sm text-muted" }, description) : null,
    action || null,
  );
}

const ALERTS = {
  error: "border-border bg-danger-tint text-danger",
  success: "border-border bg-success-tint text-success",
  info: "border-border bg-primary-tint text-primary",
  warning: "border-border bg-warning-tint text-warning",
};
const ALERT_ICONS = {
  error: "alert-circle",
  success: "check-circle-2",
  info: "info",
  warning: "alert-triangle",
};

export function alert(message, type = "error") {
  return h(
    "div",
    {
      class: `flex items-start gap-2 rounded-md border px-4 py-3 text-sm ${ALERTS[type] || ALERTS.error}`,
      role: "alert",
    },
    icon(ALERT_ICONS[type] || ALERT_ICONS.error, { size: 18, class: "mt-0.5" }),
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
