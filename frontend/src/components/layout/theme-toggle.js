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
import { isDark, toggleTheme } from "../../lib/theme.js";

/** Alterna tema claro/oscuro. Conserva el sistema visual (botón icono). */
export function themeToggle() {
  const node = h("button", {
    type: "button",
    class:
      "inline-flex min-h-11 min-w-11 items-center justify-center rounded-lg p-2 text-slate-600 transition hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2",
  });

  function render() {
    const dark = isDark();
    node.replaceChildren(icon(dark ? "sun" : "moon", { size: 18 }));
    node.setAttribute("aria-pressed", dark ? "true" : "false");
    node.setAttribute("aria-label", dark ? "Activar tema claro" : "Activar tema oscuro");
    node.setAttribute("title", dark ? "Activar tema claro" : "Activar tema oscuro");
  }

  node.addEventListener("click", () => {
    toggleTheme();
    render();
  });
  render();
  return node;
}
