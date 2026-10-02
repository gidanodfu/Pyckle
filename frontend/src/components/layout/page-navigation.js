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

/**
 * PageNavigation: navegación de subsecciones (tabs) reutilizable por todos los
 * paneles. El estado activo se comunica con borde inferior + color + icono +
 * `aria-current`, nunca solo con color. Navega por el router SPA (`data-link`).
 *
 * @param {{key:string,label:string,path:string,iconName?:string}[]} items
 * @param {string} activeKey
 */
export function pageNavigation(items, activeKey, { label = "Secciones" } = {}) {
  return h(
    "nav",
    { class: "flex flex-wrap gap-1 border-b border-border", "aria-label": label },
    items.map((item) => {
      const active = item.key === activeKey;
      return h(
        "a",
        {
          href: item.path,
          "data-link": "true",
          "aria-current": active ? "page" : null,
          class: `-mb-px inline-flex min-h-11 items-center gap-2 border-b-2 px-3 py-2 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background ${
            active
              ? "border-primary text-primary"
              : "border-transparent text-foreground-secondary hover:border-border hover:text-foreground"
          }`,
        },
        item.iconName ? icon(item.iconName, { size: 16 }) : null,
        item.label,
      );
    }),
  );
}
