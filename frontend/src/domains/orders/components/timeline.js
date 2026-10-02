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

import { formatDateTime, h, statusLabel } from "../../../components/dom.js";
import { icon } from "../../../components/icons.js";

const DOT = {
  completed: "bg-success",
  cancelled: "bg-danger",
  not_repairable: "bg-danger",
  received: "bg-primary",
  report_generated: "bg-primary",
};

/**
 * Timeline alimentado por los eventos reales de la reparación.
 * El backend ya filtró los eventos no visibles al cliente.
 */
export function orderTimeline(events, { emptyLabel = "Sin eventos todavía." } = {}) {
  if (!events || !events.length) {
    return h("p", { class: "text-sm text-muted" }, emptyLabel);
  }
  return h(
    "ol",
    { class: "relative space-y-4 border-l border-border pl-6" },
    events.map((event) =>
      h(
        "li",
        { class: "relative" },
        h(
          "span",
          {
            class: `absolute -left-[31px] top-1 flex h-3 w-3 items-center justify-center rounded-full ${
              DOT[event.new_status] || DOT[event.event_type] || "bg-surface-strong"
            }`,
          },
        ),
        h(
          "p",
          { class: "text-sm font-semibold text-foreground" },
          statusLabel(event.new_status || event.event_type),
        ),
        event.description
          ? h("p", { class: "text-sm text-foreground-secondary" }, event.description)
          : null,
        h(
          "p",
          { class: "mt-0.5 inline-flex items-center gap-1 text-xs text-muted" },
          icon("clock", { size: 12 }),
          formatDateTime(event.created_at),
          event.actor ? ` · ${event.actor.full_name}` : "",
        ),
      ),
    ),
  );
}
