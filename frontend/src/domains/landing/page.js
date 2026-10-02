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
import { sectionShell } from "../../components/layout/index.js";
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

function sectionHeading(title, description) {
  return h(
    "div",
    { class: "text-center" },
    h("h2", { class: "text-2xl font-bold tracking-tight text-foreground md:text-3xl" }, title),
    description
      ? h(
          "p",
          { class: "mx-auto mt-2 max-w-2xl text-sm text-foreground-secondary md:text-base" },
          description,
        )
      : null,
  );
}

function stepCard([title, text, iconName], index) {
  return card(
    h(
      "span",
      { class: "flex h-11 w-11 items-center justify-center rounded-md bg-primary-tint text-primary" },
      icon(iconName, { size: 20 }),
    ),
    h("h3", { class: "mt-3 text-base font-semibold text-foreground" }, `${index + 1}. ${title}`),
    h("p", { class: "mt-2 text-sm leading-relaxed text-foreground-secondary" }, text),
  );
}

function specialtyCard(specialty) {
  const iconName = SPECIALTY_ICONS[specialty.slug] || DEFAULT_SPECIALTY_ICON;
  return card(
    h(
      "div",
      { class: "flex flex-col items-center gap-2 text-center" },
      h("span", { class: "text-primary", "aria-hidden": "true" }, icon(iconName, { size: 22 })),
      h("span", { class: "text-sm font-medium leading-snug text-foreground-secondary" }, specialty.name),
    ),
  );
}

export async function Landing() {
  let specialties = [];
  try {
    specialties = await api.get(endpoints.specialties.list, { auth: false });
  } catch {
    specialties = [];
  }

  const hero = sectionShell(
    {},
    h(
      "div",
      { class: "grid gap-8 md:grid-cols-2 md:items-center" },
      h(
        "div",
        { class: "space-y-5" },
        h(
          "span",
          {
            class:
              "inline-flex rounded-full border border-border bg-primary-tint px-3 py-1 text-xs font-semibold uppercase tracking-wide text-primary",
          },
          "Marketplace de reparación",
        ),
        h(
          "h1",
          { class: "text-3xl font-extrabold leading-tight text-foreground md:text-4xl" },
          "Tu equipo falla.",
          h("br"),
          "Encuentra quién lo repare.",
        ),
        h(
          "p",
          { class: "max-w-lg text-base text-foreground-secondary md:text-lg" },
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
        { class: "grid gap-4" },
        card(
          h("p", { class: "text-3xl font-bold tabular-nums text-foreground" }, String(specialties.length)),
          h("p", { class: "text-sm text-muted" }, "Especialidades disponibles"),
        ),
        card(
          h("p", { class: "text-sm font-semibold text-foreground" }, "Todo queda registrado"),
          h(
            "p",
            { class: "mt-1 text-sm text-foreground-secondary" },
            "Desde la solicitud hasta la entrega, consulta el estado y los cambios de tu reparación.",
          ),
        ),
      ),
    ),
  );

  const steps = sectionShell(
    {},
    sectionHeading("¿Cómo funciona?"),
    h(
      "div",
      { class: "mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3" },
      STEPS.map(stepCard),
    ),
  );

  const specialtiesSection = sectionShell(
    {},
    sectionHeading(
      "Especialidades disponibles",
      "Selecciona el tipo de equipo y encuentra técnicos que trabajan con él.",
    ),
    h(
      "div",
      { class: "mt-5 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4" },
      specialties.map(specialtyCard),
    ),
  );

  const cta = sectionShell(
    {},
    h(
      "div",
      { class: "mx-auto max-w-2xl py-2 text-center" },
      h("h2", { class: "text-2xl font-bold tracking-tight text-foreground md:text-3xl" }, "¿Reparas dispositivos?"),
      h(
        "p",
        { class: "mx-auto mt-2 max-w-2xl text-sm text-foreground-secondary md:text-base" },
        "Crea tu perfil, indica qué equipos reparas y cómo atiendes, y recibe solicitudes que coincidan con tus especialidades.",
      ),
      h(
        "div",
        { class: "mt-5 flex justify-center" },
        button("Quiero ser técnico", { iconName: "wrench", onClick: () => navigate(routes.registerTechnician) }),
      ),
    ),
  );

  return h("div", { class: "flex flex-col gap-4 py-6" }, hero, steps, specialtiesSection, cta);
}
