import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import { goto, jsonResponse, page, setupDom, waitFor } from "./dom_env.mjs";

const window = setupDom();

const calls = [];

const technicianUser = {
  user: {
    id: "u-tech",
    email: "tech@test.dev",
    full_name: "Técnico Demo",
    phone: "+51999111222",
    is_active: true,
    is_verified: true,
    created_at: "2026-01-01T00:00:00Z",
    roles: [{ id: "r2", name: "technician" }],
  },
  customer_profile: null,
  technician_id: "t1",
  permissions: [],
};

const order = {
  id: "o1",
  request_id: "req1",
  quotation_id: "q1",
  status: "diagnosis",
  result: null,
  final_price: "180.00",
  received_at: "2026-01-02T00:00:00Z",
  completed_at: null,
  customer: { id: "u-cust", full_name: "Cliente Demo" },
  technician: {
    id: "t1",
    full_name: "Técnico Demo",
    rating_avg: "4.5",
    rating_count: 2,
    is_verified: true,
    district_name: "JLO",
  },
  quotation: {
    id: "q1",
    request_id: "req1",
    price: "180.00",
    preliminary_diagnosis: "Diagnóstico preliminar.",
    estimated_days: 2,
    status: "accepted",
    items: [],
    technician_reviews: [],
    created_at: "2026-01-01T00:00:00Z",
  },
  request: {
    id: "req1",
    title: "Laptop no enciende",
    status: "accepted",
    modality: "home",
    specialty_name: "Laptops",
    district_name: "JLO",
    province_name: "Chiclayo",
    department_name: "Lambayeque",
  },
  service_address: "Av. Prueba 123",
  diagnosis: null,
  work_performed: null,
  tests_performed: null,
  technician_notes: null,
  not_repairable_reason: null,
  events: [
    {
      id: "e1",
      event_type: "received",
      old_status: "awaiting_receipt",
      new_status: "received",
      description: "Equipo recibido",
      visible_to_customer: true,
      actor: { id: "u-tech", full_name: "Técnico Demo" },
      created_at: "2026-01-02T00:00:00Z",
    },
  ],
  price_changes: [],
  cost_items: [
    {
      id: "c1",
      kind: "part",
      description: "Repuesto",
      amount: "60.00",
      visible_to_customer: true,
      created_at: "2026-01-02T00:00:00Z",
    },
  ],
  report: null,
  report_versions: 0,
  has_pending_price_change: false,
  has_review: false,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
};

let currentOrder = order;

globalThis.fetch = async (url, options = {}) => {
  const target = String(url).replace("http://localhost", "");
  const method = (options.method || "GET").toUpperCase();
  calls.push({ target, method, body: options.body ? JSON.parse(options.body) : null });

  if (target.startsWith("/api/v1/auth/me")) return jsonResponse(technicianUser);
  if (target.startsWith("/api/v1/ws/ticket")) return jsonResponse({ ticket: "t", expires_in: 60 });
  if (target.startsWith("/api/v1/technicians/me/summary")) {
    return jsonResponse({
      total: 3,
      by_status: { diagnosis: 1, in_repair: 1, completed: 1 },
      by_result: { repaired: 1 },
      by_specialty: [{ specialty_id: "s1", name: "Laptops", count: 2 }],
      pending_price_changes: 0,
    });
  }
  if (target.startsWith("/api/v1/technicians/me/stats")) {
    return jsonResponse({
      active_orders: 1,
      completed_orders: 1,
      total_earnings: "180.00",
      pending_quotations: 1,
    });
  }
  if (target.startsWith("/api/v1/technicians/me")) {
    return jsonResponse({
      id: "t1",
      user: { id: "u-tech", full_name: "Técnico Demo" },
      bio: null,
      experience_years: 3,
      is_verified: true,
      offers_home_service: true,
      offers_workshop_service: false,
      workshop_address: null,
      department_id: "d1",
      province_id: "p1",
      district_id: "x1",
      department_name: "Lambayeque",
      province_name: "Chiclayo",
      district_name: "JLO",
      rating_avg: "4.5",
      rating_count: 2,
      specialties: [],
      created_at: "2026-01-01T00:00:00Z",
    });
  }
  if (target.startsWith("/api/v1/specialties")) {
    return jsonResponse([{ id: "s1", name: "Laptops", slug: "laptops", is_active: true }]);
  }
  if (target.startsWith("/api/v1/repair-requests/available?limit=5")) {
    return jsonResponse(page([]));
  }
  if (target.includes("/orders?limit=5")) return jsonResponse(page([]));
  if (target.includes("/orders?limit=50")) return jsonResponse(page([]));
  if (target.includes("/orders/o1")) return jsonResponse(currentOrder);
  if (target.startsWith("/api/v1/conversations")) return jsonResponse([]);
  if (target.startsWith("/api/v1/quotations/mine")) return jsonResponse([]);
  if (target.startsWith("/api/v1/notifications?limit=20")) return jsonResponse([]);
  return jsonResponse({});
};

window.localStorage.setItem("pyckle_access_token", "test-token");

const assetsDir = fileURLToPath(new URL("../dist/assets/", import.meta.url));
const asset = readdirSync(assetsDir).find((name) => name.endsWith(".js"));
await import(pathToFileURL(path.join(assetsDir, asset)).href);

test("panel técnico: resumen, categorías y navegación", async () => {
  goto(window, "/technician");
  await waitFor(() =>
    (window.document.body.textContent || "").includes("Reparaciones por estado"),
  );
  const text = window.document.body.textContent;
  assert.match(text, /Reparaciones por estado/);
  assert.match(text, /Reparaciones por categoría/);
  assert.match(text, /Laptops/);
  assert.match(text, /Cotizaciones/);
  assert.match(text, /Informes/);
});

test("detalle técnico: timeline y cambio de estado", async () => {
  calls.length = 0;
  goto(window, "/orders/o1");
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes("Seguimiento"),
  );

  const text = window.document.querySelector("#view").textContent;
  assert.match(text, /Equipo recibido/);
  assert.match(text, /Iniciar reparación/);

  const startButton = [...window.document.querySelectorAll("button")].find(
    (button) => button.textContent === "Iniciar reparación",
  );
  assert.ok(startButton, "debe existir la acción de iniciar reparación");
  startButton.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  await waitFor(() =>
    calls.some((call) => call.method === "PATCH" && call.target.endsWith("/orders/o1/status")),
  );
  const patch = calls.find(
    (call) => call.method === "PATCH" && call.target.endsWith("/orders/o1/status"),
  );
  assert.equal(patch.body.status, "in_repair");
});

test("detalle técnico: guarda detalles técnicos con PUT", async () => {
  calls.length = 0;
  goto(window, "/orders/o1");
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes("Detalles técnicos"),
  );

  const form = [...window.document.querySelectorAll("form")].find((node) =>
    node.textContent.includes("Guardar detalles"),
  );
  assert.ok(form, "debe existir el formulario de detalles técnicos");
  form.querySelector('textarea[name="diagnosis"]').value = "Diagnóstico de prueba";
  form.dispatchEvent(new window.Event("submit", { bubbles: true, cancelable: true }));

  await waitFor(() =>
    calls.some(
      (call) => call.method === "PUT" && call.target.endsWith("/orders/o1/repair-details"),
    ),
  );
  const put = calls.find(
    (call) => call.method === "PUT" && call.target.endsWith("/orders/o1/repair-details"),
  );
  assert.equal(put.body.diagnosis, "Diagnóstico de prueba");
});

test("detalle técnico: propone cambio de precio", async () => {
  calls.length = 0;
  goto(window, "/orders/o1");
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes("Proponer cambio"),
  );

  const form = [...window.document.querySelectorAll("form")].find((node) =>
    node.textContent.includes("Proponer nuevo costo"),
  );
  form.querySelector('input[name="new_price"]').value = "250";
  form.querySelector('textarea[name="reason"]').value = "Daño adicional encontrado";
  form.dispatchEvent(new window.Event("submit", { bubbles: true, cancelable: true }));

  await waitFor(() =>
    calls.some((call) => call.method === "POST" && call.target.endsWith("/orders/o1/price-changes")),
  );
  const post = calls.find(
    (call) => call.method === "POST" && call.target.endsWith("/orders/o1/price-changes"),
  );
  assert.equal(post.body.new_price, 250);
});

test("detalle terminal: oculta acciones de gestión", async () => {
  currentOrder = { ...order, status: "completed", result: "repaired" };
  goto(window, "/orders/o1");
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes("Seguimiento"),
  );
  const text = window.document.querySelector("#view").textContent;
  assert.doesNotMatch(text, /Actualizar proceso/);
  assert.doesNotMatch(text, /Detalles técnicos/);
  currentOrder = order;
});

test("detalle técnico: no muestra la confirmación de reseña del cliente", async () => {
  currentOrder = { ...order, status: "completed", result: "repaired", has_review: true };
  goto(window, "/orders/o1");
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes("Seguimiento"),
  );
  const text = window.document.querySelector("#view").textContent;
  assert.doesNotMatch(text, /Gracias por calificar este servicio\./);
  currentOrder = order;
});
