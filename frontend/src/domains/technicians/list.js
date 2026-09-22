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
import { locationFields } from "../../components/geo.js";
import { icon } from "../../components/icons.js";
import { Container } from "../../components/layout/index.js";
import { alert, button, card, emptyState, field, input, pageHeader, select, withBusy } from "../../components/ui/index.js";
import { createLatestGuard } from "../../lib/latest.js";
import { routes } from "../../lib/paths.js";
import { store } from "../../state/store.js";
import { technicianCard } from "./components/technician-card.js";

const SCOPE_LABELS = {
  province: "la provincia",
  department: "el departamento",
  all: "todo el país",
};

function expansionNotice(scope, expanded) {
  if (!expanded || !SCOPE_LABELS[scope]) return null;
  return alert(
    `No encontramos técnicos en tu distrito; mostrando resultados de ${SCOPE_LABELS[scope]}.`,
    "info",
  );
}

const FILTER_PARAMS = ["search", "specialty_id", "verified_only", "department_id", "province_id", "district_id"];

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Ignora ids de URL que no sean UUID válidos (evita 422 por enlaces manuales). */
function validId(value) {
  return value && UUID_RE.test(value) ? value : "";
}

function readUrlFilters() {
  const params = new URLSearchParams(window.location.search);
  return {
    search: params.get("search") || "",
    specialty_id: validId(params.get("specialty_id") || ""),
    verified_only: params.get("verified_only") === "true",
    department_id: validId(params.get("department_id") || ""),
    province_id: validId(params.get("province_id") || ""),
    district_id: validId(params.get("district_id") || ""),
  };
}

function writeUrlFilters(filters) {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.specialty_id) params.set("specialty_id", filters.specialty_id);
  if (filters.verified_only) params.set("verified_only", "true");
  for (const key of ["department_id", "province_id", "district_id"]) {
    if (filters[key]) params.set(key, filters[key]);
  }
  const suffix = params.toString();
  window.history.pushState({}, "", `${routes.technicians}${suffix ? `?${suffix}` : ""}`);
}

export async function TechniciansList() {
  const profile = store.get().me?.customer_profile;
  const initial = readUrlFilters();
  // Refleja el filtro automático por zona del backend cuando no hay filtros explícitos.
  if (!initial.department_id && !initial.province_id && !initial.district_id && profile?.district_id) {
    initial.department_id = profile.department_id || "";
    initial.province_id = profile.province_id || "";
    initial.district_id = profile.district_id || "";
  }

  const specialties = await api.get(endpoints.specialties.list, { auth: false });
  const searchInput = input({ name: "search", value: initial.search, placeholder: "Buscar por nombre o descripción" });
  const specialtySelect = select(
    "specialty_id",
    [
      { value: "", label: "Todas las especialidades" },
      ...specialties.map((item) => ({ value: item.id, label: item.name })),
    ],
    { value: initial.specialty_id },
  );
  const verifiedCheckbox = h("input", { type: "checkbox", name: "verified_only", checked: initial.verified_only });
  const location = locationFields({
    value: {
      department_id: initial.department_id,
      province_id: initial.province_id,
      district_id: initial.district_id,
    },
    required: false,
  });

  const notice = h("div", { class: "mt-4" });
  const results = h("div", { class: "mt-6 grid gap-4 md:grid-cols-2" });
  const guard = createLatestGuard();
  const filterButton = button("Filtrar", { iconName: "filter", onClick: () => apply() });
  const clearButton = button("Limpiar filtros", { variant: "ghost", iconName: "x", onClick: () => clear() });

  function renderResults(data, filters) {
    const expansion = expansionNotice(data.scope, data.expanded);
    notice.replaceChildren(...[expansion].filter(Boolean));
    const hasFilters = FILTER_PARAMS.some((key) => filters[key]);
    results.replaceChildren(
      ...(data.items.length
        ? data.items.map((technician) => technicianCard(technician))
        : [
            emptyState(
              "Sin técnicos",
              hasFilters
                ? "No se encontraron técnicos con esos filtros."
                : "Aún no hay técnicos registrados.",
              null,
              { iconName: "search" },
            ),
          ]),
    );
  }

  function currentFilters() {
    const selected = location.getValue();
    return {
      search: searchInput.value.trim(),
      specialty_id: specialtySelect.value,
      verified_only: verifiedCheckbox.checked,
      department_id: selected.department_id || "",
      province_id: selected.province_id || "",
      district_id: selected.district_id || "",
    };
  }

  async function load(filters, { updateUrl = false } = {}) {
    const isCurrent = guard.next();
    if (updateUrl) writeUrlFilters(filters);
    await withBusy(filterButton, async () => {
      let data;
      try {
        data = await api.get(
          endpoints.technicians.list({
            limit: 50,
            search: filters.search,
            specialty_id: filters.specialty_id,
            verified_only: filters.verified_only ? "true" : undefined,
            department_id: filters.department_id,
            province_id: filters.province_id,
            district_id: filters.district_id,
          }),
        );
      } catch (error) {
        if (isCurrent()) {
          notice.replaceChildren(alert(error.message || "No se pudieron cargar los técnicos"));
        }
        return;
      }
      if (!isCurrent()) return;
      renderResults(data, filters);
    });
  }

  function apply() {
    load(currentFilters(), { updateUrl: true });
  }

  function clear() {
    searchInput.value = "";
    specialtySelect.value = "";
    verifiedCheckbox.checked = false;
    location.reset();
    load(
      {
        search: "",
        specialty_id: "",
        verified_only: false,
        department_id: "",
        province_id: "",
        district_id: "",
      },
      { updateUrl: true },
    );
  }

  const filters = card(
    h(
      "div",
      { class: "space-y-4" },
      h(
        "div",
        { class: "grid gap-4 sm:grid-cols-[1fr_240px_auto]" },
        field("Buscar", searchInput),
        field("Especialidad", specialtySelect),
        h("div", { class: "flex flex-wrap items-end gap-2" }, filterButton, clearButton),
      ),
      h(
        "div",
        { class: "grid gap-4 sm:grid-cols-[1fr_auto]" },
        h(
          "div",
          {},
          h(
            "p",
            { class: "mb-2 flex items-center gap-1.5 text-sm font-medium text-slate-700" },
            icon("map-pin", { size: 15 }),
            "Ubicación",
          ),
          location.node,
        ),
        h(
          "label",
          { class: "flex items-center gap-2 self-start text-sm text-slate-700 sm:pb-2 sm:self-end" },
          verifiedCheckbox,
          "Solo verificados",
        ),
      ),
    ),
  );

  await load(initial);

  return Container(
    pageHeader("Técnicos", "Técnicos listos para atender tu dispositivo en tu zona."),
    h("div", { class: "mt-6" }, filters),
    notice,
    results,
  );
}
