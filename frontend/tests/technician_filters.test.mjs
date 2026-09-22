import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import { click, goto, jsonResponse, page, setupDom, sleep, waitFor } from "./dom_env.mjs";

const window = setupDom();

function technician(overrides) {
  return {
    id: "t1",
    full_name: "Base",
    bio: null,
    experience_years: 5,
    is_verified: false,
    offers_home_service: true,
    offers_workshop_service: false,
    workshop_address: null,
    department_name: "Lambayeque",
    province_name: "Chiclayo",
    district_name: "José Leonardo Ortiz",
    rating_avg: "0.00",
    rating_count: 0,
    specialties: [],
    ...overrides,
  };
}

const SPECIALTY = { id: "s1", name: "Laptops", slug: "laptops", is_active: true };
const ADA = technician({ id: "t-ada", full_name: "Ada Verificada", is_verified: true, specialties: [SPECIALTY] });
const BRUNO = technician({ id: "t-bruno", full_name: "Bruno No Verificado", is_verified: false, specialties: [SPECIALTY] });
const CARLA = technician({
  id: "t-carla",
  full_name: "Carla Otra Zona",
  is_verified: false,
  district_name: "Chiclayo",
  specialties: [SPECIALTY],
});

const listRequests = [];

globalThis.fetch = async (url) => {
  const target = String(url).replace("http://localhost", "");
  const parsed = new URL(target, "http://localhost");
  if (target.startsWith("/api/v1/auth/me")) return jsonResponse({ detail: "no auth" }, 401);
  if (target.startsWith("/api/v1/geo/departments/d1/provinces")) {
    return jsonResponse([{ id: "p1", code: "1401", name: "Chiclayo", department_id: "d1" }]);
  }
  if (target.startsWith("/api/v1/geo/provinces/p1/districts")) {
    return jsonResponse([
      { id: "x1", code: "140105", name: "José Leonardo Ortiz", province_id: "p1", department_id: "d1" },
    ]);
  }
  if (target.startsWith("/api/v1/geo/departments")) {
    return jsonResponse([{ id: "d1", code: "14", name: "Lambayeque" }]);
  }
  if (target.startsWith("/api/v1/specialties")) return jsonResponse([SPECIALTY]);
  if (target.startsWith("/api/v1/notifications")) return jsonResponse([]);
  if (/^\/api\/v1\/technicians\/[^?/]+$/.test(parsed.pathname)) {
    const id = parsed.pathname.split("/").pop();
    return jsonResponse([ADA, BRUNO, CARLA].find((item) => item.id === id) || {});
  }
  if (target.startsWith("/api/v1/technicians")) {
    listRequests.push(parsed.searchParams);
    let items = [ADA, BRUNO, CARLA];
    if (parsed.searchParams.get("verified_only") === "true") {
      items = items.filter((item) => item.is_verified);
    }
    if (parsed.searchParams.get("district_id")) {
      items = items.filter((item) => item.district_name === "José Leonardo Ortiz");
    }
    if (parsed.searchParams.get("specialty_id")) {
      items = items.filter((item) =>
        item.specialties.some((specialty) => specialty.id === parsed.searchParams.get("specialty_id")),
      );
    }
    return jsonResponse(page(items));
  }
  return jsonResponse({});
};

const assetsDir = fileURLToPath(new URL("../dist/assets/", import.meta.url));
const asset = readdirSync(assetsDir).find((name) => name.endsWith(".js"));
await import(pathToFileURL(path.join(assetsDir, asset)).href);
await waitFor(() => (window.document.querySelector("#view")?.textContent || "").includes("Repara"));

function viewText() {
  return window.document.querySelector("#view")?.textContent || "";
}

function selectFilter(name) {
  return window.document.querySelector(`#view select[name="${name}"]`);
}

function filterButton(label) {
  return [...window.document.querySelectorAll("#view button")].find((node) =>
    node.textContent.includes(label),
  );
}

test("sin filtros muestra todos los técnicos", async () => {
  goto(window, "/technicians");
  await waitFor(() => viewText().includes("Ada Verificada"));
  assert.ok(viewText().includes("Bruno No Verificado"));
  assert.ok(viewText().includes("Carla Otra Zona"));
  assert.equal(listRequests.at(-1).get("department_id"), null);
});

test("la cascada geográfica y los filtros combinados consultan al backend", async () => {
  await waitFor(() => (selectFilter("department_id")?.options.length || 0) > 1);

  const department = selectFilter("department_id");
  department.value = "d1";
  department.dispatchEvent(new window.Event("change"));
  await waitFor(() => (selectFilter("province_id")?.options.length || 0) > 1);
  assert.equal(selectFilter("district_id").disabled, true, "el distrito depende de la provincia");

  const province = selectFilter("province_id");
  province.value = "p1";
  province.dispatchEvent(new window.Event("change"));
  await waitFor(() => (selectFilter("district_id")?.options.length || 0) > 1);
  selectFilter("district_id").value = "x1";

  selectFilter("specialty_id").value = "s1";
  const verified = window.document.querySelector('#view input[name="verified_only"]');
  verified.checked = true;

  const before = listRequests.length;
  click(filterButton("Filtrar"));
  await waitFor(() => listRequests.length > before, { timeout: 2000 });
  await sleep(40);

  const applied = listRequests.at(-1);
  assert.equal(applied.get("department_id"), "d1");
  assert.equal(applied.get("province_id"), "p1");
  assert.equal(applied.get("district_id"), "x1");
  assert.equal(applied.get("specialty_id"), "s1");
  assert.equal(applied.get("verified_only"), "true");

  assert.ok(viewText().includes("Ada Verificada"));
  assert.ok(!viewText().includes("Bruno No Verificado"));
  assert.ok(!viewText().includes("Carla Otra Zona"));

  const search = window.location.search;
  for (const param of ["department_id=d1", "province_id=p1", "district_id=x1", "specialty_id=s1", "verified_only=true"]) {
    assert.ok(search.includes(param), `URL sin ${param}`);
  }
});

test("limpiar filtros reinicia el estado y la URL", async () => {
  const before = listRequests.length;
  click(filterButton("Limpiar filtros"));
  await waitFor(() => listRequests.length > before, { timeout: 2000 });
  await sleep(40);

  const cleared = listRequests.at(-1);
  assert.equal(cleared.get("department_id"), null);
  assert.equal(cleared.get("verified_only"), null);
  assert.equal(window.location.pathname, "/technicians");
  assert.equal(window.location.search, "");
  assert.equal(selectFilter("department_id").value, "");
  assert.equal(window.document.querySelector('#view input[name="verified_only"]').checked, false);

  await waitFor(() => viewText().includes("Ada Verificada"));
  assert.ok(viewText().includes("Bruno No Verificado"));
  assert.ok(viewText().includes("Carla Otra Zona"));
});
