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
  "inline-flex min-h-11 items-center gap-1.5 rounded text-sm text-foreground-secondary transition-colors hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background";

function legalLink({ label, path, iconName }) {
  return h(
    "a",
    { href: path, "data-link": "true", class: LINK_CLASS },
    h("span", { class: "text-muted", "aria-hidden": "true" }, icon(iconName, { size: 14 })),
    label,
  );
}

/**
 * Footer global único de Pyckle. Es el extremo inferior del App Shell: usa el
 * mismo contenedor (max-w-6xl + px-4), la misma familia de superficie, borde y
 * radio que la Navbar. Se monta una sola vez en `app/bootstrap.js` y se
 * comparte en todas las rutas (landing, cliente, técnico y admin).
 */
export function createFooter() {
  return h(
    "footer",
    { class: "shrink-0 pb-6" },
    h(
      "div",
      { class: "app-container" },
      h(
        "div",
        { class: "rounded-xl border border-border bg-surface px-5 py-5 sm:px-6" },
        h(
          "div",
          { class: "grid gap-5 sm:grid-cols-[minmax(240px,0.7fr)_minmax(0,1.8fr)] sm:items-start" },
          h(
            "div",
            { class: "flex items-start gap-3" },
            h("img", {
              src: assets.logo64,
              alt: "Pyckle",
              width: 24,
              height: 24,
              class: "mt-0.5 h-6 w-6 shrink-0 object-contain",
            }),
            h(
              "div",
              { class: "leading-tight" },
              h(
                "p",
                { class: "text-sm font-semibold text-foreground" },
                "Reparación de dispositivos en Perú",
              ),
              h(
                "p",
                { class: "mt-1 max-w-xs text-xs text-muted" },
                "Solicita, compara cotizaciones y sigue tu reparación de principio a fin.",
              ),
            ),
          ),
          h(
            "nav",
            {
              class: "flex flex-wrap gap-x-6 gap-y-2",
              "aria-label": "Enlaces legales",
            },
            LEGAL_LINKS.map((link) => legalLink(link)),
          ),
        ),
      ),
    ),
  );
}
