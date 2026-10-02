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

/**
 * Sección: bloque funcional de mayor nivel dentro de un PanelShell. Agrupa un
 * título con acciones y su contenido. No aporta superficie propia para no
 * anidar cards; la superficie la aporta el panel y las cards que contiene.
 *
 * @param {{title?:string, description?:string, actions?:Node, class?:string}} options
 * @param  {...Node} children
 */
export function section({ title, description, actions, class: extra = "" } = {}, ...children) {
  const head =
    title || description || actions
      ? h(
          "div",
          { class: "flex flex-wrap items-center justify-between gap-2" },
          h(
            "div",
            { class: "min-w-0" },
            title ? h("h2", { class: "text-lg font-semibold text-foreground" }, title) : null,
            description ? h("p", { class: "mt-0.5 text-sm text-muted" }, description) : null,
          ),
          actions || null,
        )
      : null;
  return h("section", { class: `space-y-3 ${extra}`.trim() }, head, ...children);
}
