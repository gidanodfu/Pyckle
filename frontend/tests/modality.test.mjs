import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import { goto, jsonResponse, setupDom, sleep, waitFor } from "./dom_env.mjs";

const window = setupDom();

const counts = { register: 0, patches: [] };
let registerBody = null;

const me = {
  user: {
    id: "u1",
    email: "tecnico@pyckle.dev",
    full_name: "Técnico Prueba",
    phone: "+51999123456",
    is_active: true,
    is_verified: true,
    created_at: "2026-01-01T00:00:00Z",
    roles: [{ id: "r2", name: "technician" }],
  },
  customer_profile: null,
  technician_id: "t1",
  permissions: [],
};

const technicianProfile = {
  id: "t1",
  user: { id: "u1", full_name: "Técnico Prueba", email: "tecnico@pyckle.dev" },
  bio: "Reparaciones",
  experience_years: 5,
  is_verified: true,
  offers_home_service: true,
  offers_workshop_service: false,
  workshop_address: null,
  department_id: "d1",
  province_id: "p1",
  district_id: "x1",
  department_name: "Lambayeque",
  province_name: "Chiclayo",
  district_name: "José Leonardo Ortiz",
  rating_avg: "4.5",
  rating_count: 3,
  specialties: [],
  created_at: "2026-01-01T00:00:00Z",
};

globalThis.fetch = async (url, options = {}) => {
  const target = String(url).replace("http://localhost", "");
  const method = (options.method || "GET").toUpperCase();

  if (target.startsWith("/api/v1/auth/me")) return jsonResponse(me);
  if (target.startsWith("/api/v1/ws/ticket")) return jsonResponse({ ticket: "test-ticket", expires_in: 60 });
  if (target.startsWith("/api/v1/technicians/me/stats")) {
    return jsonResponse({ active_orders: 0, completed_orders: 0, total_earnings: "0", pending_quotations: 0 });
  }
  if (target.startsWith("/api/v1/technicians/me") && method === "PATCH") {
    const body = JSON.parse(options.body);
    counts.patches.push(body);
    return jsonResponse({ ...technicianProfile, ...body });
  }
  if (target.startsWith("/api/v1/technicians/me")) return jsonResponse(technicianProfile);
  if (target.startsWith("/api/v1/auth/register") && method === "POST") {
    counts.register += 1;
    registerBody = JSON.parse(options.body);
    return jsonResponse({ id: "u2", email: registerBody.email, roles: [{ id: "r2", name: "technician" }] }, 201);
  }
  if (target.startsWith("/api/v1/auth/login") && method === "POST") {
    return jsonResponse({ access_token: "a", refresh_token: "r", token_type: "bearer", expires_in: 900 });
  }
  if (target.startsWith("/api/v1/geo/departments/d1/provinces")) {
    return jsonResponse([{ id: "p1", code: "1401", name: "Chiclayo", department_id: "d1" }]);
  }
  if (target.startsWith("/api/v1/geo/provinces/p1/districts")) {
    return jsonResponse([{ id: "x1", code: "140105", name: "José Leonardo Ortiz", province_id: "p1", department_id: "d1" }]);
  }
  if (target.startsWith("/api/v1/geo/departments")) {
    return jsonResponse([{ id: "d1", code: "14", name: "Lambayeque" }]);
  }
  if (target.startsWith("/api/v1/specialties")) return jsonResponse([]);
  if (target.startsWith("/api/v1/notifications?limit=20")) return jsonResponse([]);
  if (target.includes("/repair-requests?limit=5")) return jsonResponse({ items: [], total: 0, limit: 20, offset: 0 });
  if (target.includes("/orders?limit=5")) return jsonResponse({ items: [], total: 0, limit: 20, offset: 0 });
  return jsonResponse({});
};

const assetsDir = fileURLToPath(new URL("../dist/assets/", import.meta.url));
const asset = readdirSync(assetsDir).find((name) => name.endsWith(".js"));
await import(pathToFileURL(path.join(assetsDir, asset)).href);
await waitFor(() => (window.document.querySelector("#view")?.textContent || "").includes("Repara"));

async function fillLocation(form) {
  await waitFor(() => (form.querySelector('select[name="department_id"]')?.options.length || 0) > 1);
  const department = form.querySelector('select[name="department_id"]');
  department.value = "d1";
  department.dispatchEvent(new window.Event("change"));
  await waitFor(() => (form.querySelector('select[name="province_id"]')?.options.length || 0) > 1);
  const province = form.querySelector('select[name="province_id"]');
  province.value = "p1";
  province.dispatchEvent(new window.Event("change"));
  await waitFor(() => (form.querySelector('select[name="district_id"]')?.options.length || 0) > 1);
  form.querySelector('select[name="district_id"]').value = "x1";
}

function selectModality(scope, value) {
  const radio = scope.querySelector(`input[name="service_modality"][value="${value}"]`);
  radio.checked = true;
  radio.dispatchEvent(new window.Event("change", { bubbles: true }));
  return radio;
}

test("el registro técnico valida y envía la modalidad elegida", async () => {
  goto(window, "/register?role=technician");
  await waitFor(() => window.document.querySelector("#view form"));
  const form = window.document.querySelector("#view form");
  await fillLocation(form);

  form.querySelector('input[name="full_name"]').value = "Técnico Modalidad";
  form.querySelector('input[name="email"]').value = "modalidad@test.dev";
  form.querySelector('input[name="phone"]').value = "+51 999 111 222";
  form.querySelector('input[name="password"]').value = "password12345";
  const terms = form.querySelector('input[name="terms"]');
  terms.checked = true;
  terms.dispatchEvent(new window.Event("change"));

  assert.ok(form.querySelector('input[name="service_modality"][value="home"]').checked);
  assert.ok(form.querySelector("[name=workshop_address]").closest("label").classList.contains("hidden"));

  selectModality(form, "workshop");
  assert.ok(!form.querySelector("[name=workshop_address]").closest("label").classList.contains("hidden"));
  form.dispatchEvent(new window.Event("submit", { bubbles: true, cancelable: true }));
  await sleep(40);
  assert.equal(counts.register, 0, "taller exige dirección");

  form.querySelector('input[name="workshop_address"]').value = "Jr. Taller 456";
  form.dispatchEvent(new window.Event("submit", { bubbles: true, cancelable: true }));
  await waitFor(() => counts.register === 1);
  assert.equal(registerBody.offers_home_service, false);
  assert.equal(registerBody.offers_workshop_service, true);
  assert.equal(registerBody.workshop_address, "Jr. Taller 456");
  await waitFor(() => window.location.pathname === "/profile/technician");
});

test("el perfil propio edita la modalidad con radios y normaliza la dirección", async () => {
  counts.patches.length = 0;
  goto(window, "/profile/technician");
  await waitFor(() => window.document.querySelector("#view form"));
  const form = window.document.querySelector("#view form");
  await waitFor(() => form.querySelector('select[name="district_id"]')?.value === "x1");

  const addressBlock = () => form.querySelector("[name=workshop_address]").closest("label");
  assert.ok(form.querySelector('input[name="service_modality"][value="home"]').checked);
  assert.ok(addressBlock().classList.contains("hidden"));

  selectModality(form, "both");
  assert.ok(!addressBlock().classList.contains("hidden"));
  form.dispatchEvent(new window.Event("submit", { bubbles: true, cancelable: true }));
  await sleep(40);
  assert.equal(counts.patches.length, 0, "sin dirección no debe guardar ambas modalidades");

  form.querySelector('input[name="workshop_address"]').value = "Av. Taller 123";
  form.dispatchEvent(new window.Event("submit", { bubbles: true, cancelable: true }));
  await waitFor(() => counts.patches.length === 1);
  assert.equal(counts.patches[0].offers_home_service, true);
  assert.equal(counts.patches[0].offers_workshop_service, true);
  assert.equal(counts.patches[0].workshop_address, "Av. Taller 123");

  selectModality(form, "home");
  form.dispatchEvent(new window.Event("submit", { bubbles: true, cancelable: true }));
  await waitFor(() => counts.patches.length === 2);
  assert.equal(counts.patches[1].offers_home_service, true);
  assert.equal(counts.patches[1].offers_workshop_service, false);
  assert.equal(counts.patches[1].workshop_address, null, "una dirección vieja no debe viajar en modo domicilio");
});
