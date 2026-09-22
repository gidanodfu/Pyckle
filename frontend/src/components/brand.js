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

import { h } from "./dom.js";
import { assets, routes } from "../lib/paths.js";

/**
 * Isotipo oficial de Pyckle. Fuente única del asset y de la ruta de inicio vía
 * `lib/paths.js` (nunca escribir la ruta del archivo en los componentes).
 * Se muestra solo el isotipo; el `alt` conserva el nombre accesible de la marca.
 */
export function Logo({ size = 36, href = routes.home } = {}) {
  return h(
    "a",
    { href, "data-link": "true", class: "flex items-center gap-2" },
    h("img", {
      src: assets.logo,
      alt: "Pyckle",
      width: size,
      height: size,
      class: "shrink-0 object-contain",
    }),
  );
}
