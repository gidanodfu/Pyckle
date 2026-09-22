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

import { api } from "../api/client.js";
import { endpoints } from "../api/endpoints.js";
import { createLatestGuard } from "../lib/latest.js";
import { h } from "./dom.js";
import { field } from "./ui/index.js";

const resultCache = {
  departments: null,
  provinces: new Map(),
  districts: new Map(),
};
const inflight = new Map();

/** Cachea el resultado y también la petición en vuelo (evita duplicados). */
function fetchOnce(key, loader) {
  if (!inflight.has(key)) {
    inflight.set(
      key,
      loader().finally(() => inflight.delete(key)),
    );
  }
  return inflight.get(key);
}

async function loadDepartments() {
  if (!resultCache.departments) {
    resultCache.departments = await fetchOnce("departments", () =>
      api.get(endpoints.geo.departments, { auth: false }),
    );
  }
  return resultCache.departments;
}

async function loadProvinces(departmentId) {
  if (!departmentId) return [];
  const key = `provinces:${departmentId}`;
  if (!resultCache.provinces.has(key)) {
    resultCache.provinces.set(
      key,
      await fetchOnce(key, () => api.get(endpoints.geo.provinces(departmentId), { auth: false })),
    );
  }
  return resultCache.provinces.get(key);
}

async function loadDistricts(provinceId) {
  if (!provinceId) return [];
  const key = `districts:${provinceId}`;
  if (!resultCache.districts.has(key)) {
    resultCache.districts.set(
      key,
      await fetchOnce(key, () => api.get(endpoints.geo.districts(provinceId), { auth: false })),
    );
  }
  return resultCache.districts.get(key);
}

function fill(node, options, selected = "") {
  node.replaceChildren(
    ...options.map((option) =>
      h(
        "option",
        { value: option.value, selected: String(option.value) === String(selected || "") },
        option.label,
      ),
    ),
  );
}

function makeSelect(name, required, disabled = false) {
  return h("select", { name, required, disabled, class: "field-input disabled:bg-slate-100" });
}

const PLACEHOLDER = {
  province: { value: "", label: "Selecciona" },
  district: { value: "", label: "Selecciona" },
};

/**
 * Selectores departamento -> provincia -> distrito.
 *
 * No bloquea el render: devuelve el nodo de inmediato con los selects
 * deshabilitados y expone `ready` para habilitar el submit cuando la carga
 * inicial termina. Las guardias de secuencia garantizan que una respuesta
 * antigua no repoble un select después de un cambio más reciente.
 */
export function locationFields({ value = {}, required = true, hint } = {}) {
  const departmentSelect = makeSelect("department_id", required, true);
  const provinceSelect = makeSelect("province_id", required, true);
  const districtSelect = makeSelect("district_id", required, true);
  const guard = createLatestGuard();

  function resetDistricts() {
    fill(districtSelect, [PLACEHOLDER.district]);
    districtSelect.disabled = true;
  }

  async function setDistricts(provinceId, selected = "") {
    const isCurrent = guard.next();
    fill(districtSelect, [PLACEHOLDER.district]);
    districtSelect.disabled = true;
    if (!provinceId) return;
    const districts = await loadDistricts(provinceId);
    if (!isCurrent()) return;
    fill(
      districtSelect,
      [PLACEHOLDER.district, ...districts.map((item) => ({ value: item.id, label: item.name }))],
      selected,
    );
    districtSelect.disabled = false;
  }

  async function setProvinces(departmentId, selectedProvince = "", selectedDistrict = "") {
    const isCurrent = guard.next();
    fill(provinceSelect, [PLACEHOLDER.province]);
    provinceSelect.disabled = true;
    resetDistricts();
    if (!departmentId) return;
    const provinces = await loadProvinces(departmentId);
    if (!isCurrent()) return;
    fill(
      provinceSelect,
      [PLACEHOLDER.province, ...provinces.map((item) => ({ value: item.id, label: item.name }))],
      selectedProvince,
    );
    provinceSelect.disabled = false;
    if (selectedProvince) await setDistricts(selectedProvince, selectedDistrict);
  }

  departmentSelect.addEventListener("change", () => setProvinces(departmentSelect.value));
  provinceSelect.addEventListener("change", () => setDistricts(provinceSelect.value));

  async function hydrate() {
    const isCurrent = guard.next();
    const departments = await loadDepartments();
    if (!isCurrent()) return;
    fill(
      departmentSelect,
      [
        { value: "", label: "Selecciona" },
        ...departments.map((item) => ({ value: item.id, label: item.name })),
      ],
      value.department_id,
    );
    departmentSelect.disabled = false;
    if (value.department_id) {
      await setProvinces(value.department_id, value.province_id, value.district_id);
    }
  }

  const node = h(
    "div",
    { class: "grid gap-3 sm:grid-cols-3" },
    field("Departamento", departmentSelect),
    field("Provincia", provinceSelect),
    field("Distrito", districtSelect),
    hint ? h("p", { class: "text-xs text-slate-600 sm:col-span-3" }, hint) : null,
  );

  return {
    node,
    ready: hydrate().catch(() => {}),
    getValue: () => ({
      department_id: departmentSelect.value || null,
      province_id: provinceSelect.value || null,
      district_id: districtSelect.value || null,
    }),
    isValid: () => Boolean(departmentSelect.value && provinceSelect.value && districtSelect.value),
    reset: () => {
      guard.invalidate();
      departmentSelect.value = "";
      fill(provinceSelect, [PLACEHOLDER.province]);
      resetDistricts();
      provinceSelect.disabled = true;
    },
  };
}
