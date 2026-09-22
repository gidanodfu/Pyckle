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
import { icon } from "./icons.js";
import { assets, routes } from "../lib/paths.js";

const LEGAL_LINKS = [
  { label: "Información legal", path: routes.legal, iconName: "file-text" },
  { label: "Privacidad", path: routes.privacy, iconName: "shield-check" },
  { label: "Términos y Condiciones", path: routes.terms, iconName: "clipboard-check" },
  { label: "Tratamiento de Datos", path: routes.dataTreatment, iconName: "database" },
  { label: "Contacto", path: routes.contact, iconName: "mail" },
];

const LINK_CLASS =
  "inline-flex min-h-11 items-center gap-1.5 rounded text-sm text-slate-600 transition-colors hover:text-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2";

function legalLink({ label, path, iconName }) {
  return h(
    "a",
    { href: path, "data-link": "true", class: LINK_CLASS },
    h("span", { class: "text-slate-500", "aria-hidden": "true" }, icon(iconName, { size: 14 })),
    label,
  );
}

/**
 * Footer global único de Pyckle. Se monta una sola vez en el App Shell
 * (`app/bootstrap.js`) y se comparte en todas las rutas.
 */
export function createFooter() {
  return h(
    "footer",
    { class: "mt-10 shrink-0 border-t border-slate-200 bg-white" },
    h(
      "div",
      { class: "mx-auto max-w-6xl px-4 py-6" },
      h(
        "div",
        { class: "flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between" },
        h(
          "div",
          { class: "flex items-center gap-2.5" },
          h("img", {
            src: assets.logo64,
            alt: "Pyckle",
            width: 20,
            height: 20,
            class: "h-5 w-5 shrink-0 object-contain",
          }),
          h(
            "div",
            { class: "leading-tight" },
            h("p", { class: "text-xs text-slate-500" }, "Reparación de dispositivos en Perú"),
          ),
        ),
        h("span", { class: "text-xs text-slate-500" }, String(new Date().getFullYear())),
      ),
      h(
        "nav",
        {
          class:
            "mt-4 flex flex-wrap justify-center gap-x-6 gap-y-2 border-t border-slate-100 pt-4",
          "aria-label": "Enlaces legales",
        },
        LEGAL_LINKS.map((link) => legalLink(link)),
      ),
    ),
  );
}
