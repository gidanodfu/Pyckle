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
 * SectionShell: sección de página contenida como tarjeta. Alinea el contenido
 * al mismo contenedor global que la Navbar y el Footer (max-w-6xl + px-4) y
 * aporta la superficie (borde + radio + fondo). Su altura depende del contenido:
 * no fija min-height ni paddings verticales grandes.
 *
 * Se usa para las secciones de la landing; los paneles usan PanelShell.
 */
export function sectionShell({ class: extra = "" } = {}, ...children) {
  return h(
    "section",
    { class: extra },
    h(
      "div",
      { class: "app-container" },
      h("div", { class: "rounded-xl border border-border bg-surface p-5 sm:p-6" }, ...children),
    ),
  );
}
