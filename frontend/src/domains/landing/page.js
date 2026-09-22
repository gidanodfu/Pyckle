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

import { api } from "../../api/client.js";
import { endpoints } from "../../api/endpoints.js";
import { h } from "../../components/dom.js";
import { icon } from "../../components/icons.js";
import { button, card } from "../../components/ui/index.js";
import { navigate } from "../../lib/navigation.js";
import { isAuthenticated, store } from "../../state/store.js";
import { panelPath } from "../../lib/panel.js";
import { routes } from "../../lib/paths.js";

const STEPS = [
  ["Cuéntanos qué necesita tu equipo", "Describe la falla, agrega fotos y dinos si prefieres atención a domicilio o en taller.", "clipboard-list"],
  ["Compara las cotizaciones", "Técnicos que trabajan con esa especialidad pueden enviarte diagnóstico inicial, precio estimado y tiempo de reparación.", "file-text"],
  ["Elige y sigue la reparación", "Acepta una cotización, conversa con el técnico y consulta el avance de tu orden hasta la entrega.", "hammer"],
];

const SECTION_PAD = "py-10 md:py-12";

const SPECIALTY_ICONS = {
  celulares: "smartphone",
  "computadoras-de-escritorio": "monitor",
  consolas: "gamepad-2",
  impresoras: "printer",
  laptops: "laptop",
  tablets: "tablet",
  televisores: "tv",
};

// Fallback para especialidades nuevas que aún no tengan icono asignado.
const DEFAULT_SPECIALTY_ICON = "wrench";

function specialtyTile(specialty) {
  const iconName = SPECIALTY_ICONS[specialty.slug] || DEFAULT_SPECIALTY_ICON;
  return h(
    "div",
    {
      class: "flex w-[calc(50%-0.375rem)] shrink-0 flex-col items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-5 text-center shadow-sm sm:w-[calc(33.333%-0.5rem)] lg:w-[calc(25%-0.75rem)]",
    },
    h("span", { class: "text-blue-800", "aria-hidden": "true" }, icon(iconName, { size: 22 })),
    h("span", { class: "text-sm font-medium leading-snug text-slate-700" }, specialty.name),
  );
}

/** Contenedor de sección alineado al mismo eje del Hero (max-w-6xl + px-4). */
function Section({ class: extra = "", pad = SECTION_PAD } = {}, ...children) {
  return h(
    "section",
    { class: extra },
    h("div", { class: `mx-auto w-full max-w-6xl px-4 ${pad}`.trim() }, ...children),
  );
}

export async function Landing() {
  let specialties = [];
  try {
    specialties = await api.get(endpoints.specialties.list, { auth: false });
  } catch {
    specialties = [];
  }

  const hero = h(
    "section",
    { class: "border-b border-slate-200 bg-gradient-to-br from-blue-900 via-blue-800 to-emerald-700 text-white" },
    h(
      "div",
      { class: "mx-auto grid max-w-6xl gap-10 px-4 py-16 md:grid-cols-2 md:py-24" },
      h(
        "div",
        { class: "space-y-6" },
        h("span", { class: "inline-flex rounded-full bg-white/15 px-3 py-1 text-xs font-semibold uppercase tracking-wide" }, "Marketplace de reparación"),
        h(
          "h1",
          { class: "text-4xl font-extrabold leading-tight md:text-5xl" },
          "Tu equipo falla.",
          h("br"),
          "Encuentra quién lo repare.",
        ),
        h(
          "p",
          { class: "max-w-lg text-lg text-blue-50" },
          "Publica la falla de tu dispositivo, recibe cotizaciones de técnicos verificados y elige cómo y dónde repararlo.",
        ),
        h(
          "div",
          { class: "flex flex-wrap gap-3" },
          button(isAuthenticated() ? "Ir a mi panel" : "Publicar solicitud", {
            iconName: isAuthenticated() ? "layout-dashboard" : "plus",
            onClick: () =>
              navigate(isAuthenticated() ? panelPath(store.get().me) : routes.register),
          }),
          button("Ver técnicos", { variant: "outline", iconName: "wrench", onClick: () => navigate(routes.technicians) }),
        ),
      ),
      h(
        "div",
        { class: "grid gap-4 self-center" },
        h(
          "div",
          { class: "rounded-2xl bg-white/10 p-5 backdrop-blur" },
          h("p", { class: "text-3xl font-bold" }, String(specialties.length)),
          h("p", { class: "text-sm text-blue-50" }, "Especialidades disponibles"),
        ),
        h(
          "div",
          { class: "rounded-2xl bg-white/10 p-5 backdrop-blur" },
          h("p", { class: "text-sm font-semibold text-white" }, "Todo queda registrado"),
          h(
            "p",
            { class: "mt-1 text-sm text-blue-50" },
            "Desde la solicitud hasta la entrega, consulta el estado y los cambios de tu reparación.",
          ),
        ),
      ),
    ),
  );

  const steps = Section(
    {},
    h("h2", { class: "text-center text-3xl font-bold tracking-tight text-slate-900" }, "¿Cómo funciona?"),
    h(
      "div",
      { class: "mt-8 grid gap-5 sm:grid-cols-2 md:gap-6 lg:grid-cols-3" },
      STEPS.map(([title, text, iconName], index) =>
        card(
          h(
            "span",
            { class: "flex h-11 w-11 items-center justify-center rounded-lg bg-blue-50 text-blue-800" },
            icon(iconName, { size: 20 }),
          ),
          h("h3", { class: "mt-3 text-lg font-semibold text-blue-900" }, `${index + 1}. ${title}`),
          h("p", { class: "mt-2 text-sm leading-relaxed text-slate-600 md:text-base" }, text),
        ),
      ),
    ),
  );

  const specialtiesSection = Section(
    { class: "bg-white" },
    h("h2", { class: "text-center text-3xl font-bold tracking-tight text-slate-900" }, "Especialidades disponibles"),
    h(
      "p",
      { class: "mx-auto mt-3 max-w-2xl text-center text-sm text-slate-600 md:text-base" },
      "Selecciona el tipo de equipo y encuentra técnicos que trabajan con él.",
    ),
    h(
      "div",
      { class: "mt-6 flex flex-wrap justify-center gap-3 md:mt-8 lg:gap-4" },
      specialties.map((specialty) => specialtyTile(specialty)),
    ),
  );

  // CTA final: sin padding inferior extra porque el footer ya aporta su margen.
  const cta = Section(
    { pad: "pt-10 md:pt-12 pb-2 md:pb-4" },
    h(
      "div",
      { class: "mx-auto max-w-2xl text-center" },
      h("h2", { class: "text-3xl font-bold tracking-tight text-slate-900" }, "¿Reparas dispositivos?"),
      h(
        "p",
        { class: "mt-3 text-base text-slate-600 md:text-lg" },
        "Crea tu perfil, indica qué equipos reparas y cómo atiendes, y recibe solicitudes que coincidan con tus especialidades.",
      ),
      h(
        "div",
        { class: "mt-6 flex justify-center" },
        button("Quiero ser técnico", { variant: "success", iconName: "wrench", onClick: () => navigate(routes.registerTechnician) }),
      ),
    ),
  );

  return h("div", {}, hero, steps, specialtiesSection, cta);
}
