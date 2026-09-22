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
  completed: "bg-emerald-600",
  cancelled: "bg-red-500",
  not_repairable: "bg-red-500",
  received: "bg-blue-700",
  report_generated: "bg-indigo-600",
};

/**
 * Timeline alimentado por los eventos reales de la reparación.
 * El backend ya filtró los eventos no visibles al cliente.
 */
export function orderTimeline(events, { emptyLabel = "Sin eventos todavía." } = {}) {
  if (!events || !events.length) {
    return h("p", { class: "text-sm text-slate-500" }, emptyLabel);
  }
  return h(
    "ol",
    { class: "relative space-y-4 border-l border-slate-200 pl-6" },
    events.map((event) =>
      h(
        "li",
        { class: "relative" },
        h(
          "span",
          {
            class: `absolute -left-[31px] top-1 flex h-3 w-3 items-center justify-center rounded-full ${
              DOT[event.new_status] || DOT[event.event_type] || "bg-slate-400"
            }`,
          },
        ),
        h(
          "p",
          { class: "text-sm font-semibold text-slate-800" },
          statusLabel(event.new_status || event.event_type),
        ),
        event.description
          ? h("p", { class: "text-sm text-slate-600" }, event.description)
          : null,
        h(
          "p",
          { class: "mt-0.5 inline-flex items-center gap-1 text-xs text-slate-500" },
          icon("clock", { size: 12 }),
          formatDateTime(event.created_at),
          event.actor ? ` · ${event.actor.full_name}` : "",
        ),
      ),
    ),
  );
}
