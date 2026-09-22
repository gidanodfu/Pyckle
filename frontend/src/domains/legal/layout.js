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

import { h } from "../../components/dom.js";
import { icon } from "../../components/icons.js";
import { Container } from "../../components/layout/index.js";
import { alert, card } from "../../components/ui/index.js";
import { routes } from "../../lib/paths.js";

export const PENDING_UPDATED = "[FECHA DE ÚLTIMA ACTUALIZACIÓN PENDIENTE]";
export const PENDING_RETENTION = "[PLAZO DE CONSERVACIÓN PENDIENTE DE DEFINICIÓN LEGAL]";
export const PENDING_RESPONSE = "[PLAZO DE RESPUESTA PENDIENTE DE DEFINICIÓN]";

export function pending(value) {
  return h(
    "span",
    {
      class: "inline-flex items-center gap-1 rounded bg-amber-100 px-1.5 py-0.5 text-xs font-semibold text-amber-800",
      title: "Dato pendiente de configuración",
    },
    icon("alert-triangle", { size: 12 }),
    value,
  );
}

export function internalLink(label, path) {
  return h(
    "a",
    { href: path, "data-link": "true", class: "font-medium text-blue-700 hover:underline" },
    label,
  );
}

export function paragraph(...content) {
  return h("p", { class: "text-sm leading-relaxed text-slate-600" }, ...content);
}

export function bullets(items) {
  return h(
    "ul",
    { class: "list-disc space-y-1 pl-5 text-sm leading-relaxed text-slate-600" },
    ...items.map((item) => h("li", {}, item)),
  );
}

export function legalSection(title, ...content) {
  return card(
    h("h2", { class: "text-lg font-semibold text-slate-900" }, title),
    h("div", { class: "mt-3 space-y-3" }, ...content),
  );
}

export function draftNotice() {
  return alert(
    "Borrador informativo. Este documento describe el funcionamiento real de Pyckle, pero no constituye asesoría legal y está pendiente de revisión por un profesional antes de considerarse definitivo.",
    "warning",
  );
}

export function LegalNav({ current } = {}) {
  const links = [
    ["Información legal", routes.legal],
    ["Política de Privacidad", routes.privacy],
    ["Términos y Condiciones", routes.terms],
    ["Tratamiento de Datos Personales", routes.dataTreatment],
    ["Contacto", routes.contact],
  ].filter(([, path]) => path !== current);
  return h(
    "nav",
    { class: "mt-8 rounded-xl border border-slate-200 bg-white p-4", "aria-label": "Documentos legales" },
    h("p", { class: "text-sm font-semibold text-slate-700" }, "Otros documentos"),
    h(
      "div",
      { class: "mt-2 flex flex-wrap gap-x-4 gap-y-1" },
      ...links.map(([label, path]) => internalLink(label, path)),
    ),
  );
}

export function LegalShell({ title, subtitle, current, children }) {
  return Container(
    h(
      "article",
      { class: "mx-auto max-w-3xl" },
      h("h1", { class: "text-2xl font-bold text-slate-900" }, title),
      h("p", { class: "mt-1 text-sm text-slate-500" }, subtitle),
      h("p", { class: "mt-2 text-xs text-slate-500" }, `Última actualización: ${PENDING_UPDATED}`),
      h("div", { class: "mt-5" }, draftNotice()),
      h("div", { class: "mt-6 space-y-4" }, ...children),
      h("div", { class: "mt-6" }, LegalNav({ current })),
    ),
  );
}
