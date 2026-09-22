import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import { goto, jsonResponse, setupDom, waitFor } from "./dom_env.mjs";

const window = setupDom();

const calls = [];

const customerUser = {
  user: {
    id: "u-cust",
    email: "cliente@test.dev",
    full_name: "Cliente Demo",
    phone: "+51999111333",
    is_active: true,
    is_verified: true,
    created_at: "2026-01-01T00:00:00Z",
    roles: [{ id: "r1", name: "customer" }],
  },
  customer_profile: { district_id: "x1", district_name: "JLO", province_name: "Chiclayo" },
  technician_id: null,
  permissions: [],
};

const order = {
  id: "o2",
  request_id: "req2",
  quotation_id: "q2",
  status: "waiting_customer",
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
    id: "q2",
    request_id: "req2",
    price: "180.00",
    preliminary_diagnosis: "Diagnóstico preliminar.",
    estimated_days: 2,
    status: "accepted",
    items: [],
    technician_reviews: [],
    created_at: "2026-01-01T00:00:00Z",
  },
  request: {
    id: "req2",
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
  technician_notes: "nota-interna-secreta",
  not_repairable_reason: null,
  events: [],
  price_changes: [
    {
      id: "pc1",
      previous_price: "180.00",
      new_price: "240.00",
      reason: "Se encontró daño adicional.",
      status: "pending",
      decided_note: null,
      decided_at: null,
      created_at: "2026-01-03T00:00:00Z",
    },
  ],
  cost_items: [],
  report: {
    id: "rep1",
    version: 1,
    content_type: "application/pdf",
    size_bytes: 1000,
    generated_at: "2026-01-04T00:00:00Z",
    download_url: "/api/v1/orders/o2/report",
  },
  report_versions: 1,
  has_pending_price_change: true,
  has_review: false,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
};

let currentOrder = order;

globalThis.fetch = async (url, options = {}) => {
  const target = String(url).replace("http://localhost", "");
  const method = (options.method || "GET").toUpperCase();
  calls.push({ target, method, body: options.body ? JSON.parse(options.body) : null });

  if (target.startsWith("/api/v1/auth/me")) return jsonResponse(customerUser);
  if (target.startsWith("/api/v1/ws/ticket")) return jsonResponse({ ticket: "t", expires_in: 60 });
  if (target.includes("/orders?limit=5")) return jsonResponse({ items: [], total: 0, limit: 5, offset: 0 });
  if (target.includes("/orders/o2")) return jsonResponse(currentOrder);
  if (target.startsWith("/api/v1/conversations")) return jsonResponse([]);
  if (target.startsWith("/api/v1/notifications?limit=20")) return jsonResponse([]);
  if (target.startsWith("/api/v1/repair-requests?limit=5")) {
    return jsonResponse({ items: [], total: 0, limit: 5, offset: 0 });
  }
  return jsonResponse({});
};

window.localStorage.setItem("pyckle_access_token", "test-token");

const assetsDir = fileURLToPath(new URL("../dist/assets/", import.meta.url));
const asset = readdirSync(assetsDir).find((name) => name.endsWith(".js"));
await import(pathToFileURL(path.join(assetsDir, asset)).href);

test("cliente: aprueba cambio de precio y accede al informe", async () => {
  goto(window, "/orders/o2");
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes("Aceptar nuevo costo"),
  );

  const text = window.document.querySelector("#view").textContent;
  assert.match(text, /Nuevo costo propuesto/);
  assert.match(text, /Descargar informe/);
  assert.doesNotMatch(text, /nota-interna-secreta/);
  // El cliente no ve acciones de gestión técnica.
  assert.doesNotMatch(text, /Actualizar proceso/);

  const approve = [...window.document.querySelectorAll("button")].find(
    (button) => button.textContent === "Aceptar nuevo costo",
  );
  approve.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  await waitFor(() =>
    calls.some(
      (call) =>
        call.method === "POST" && call.target.endsWith("/orders/o2/price-changes/pc1/approve"),
    ),
  );
});

test("cliente con reseña: muestra la confirmación y no el formulario", async () => {
  currentOrder = {
    ...order,
    status: "completed",
    result: "repaired",
    completed_at: "2026-01-05T00:00:00Z",
    has_review: true,
    has_pending_price_change: false,
    price_changes: [],
  };
  goto(window, "/orders/o2");
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes("Gracias por calificar"),
  );
  const text = window.document.querySelector("#view").textContent;
  assert.match(text, /Gracias por calificar este servicio\./);
  assert.doesNotMatch(text, /Califica el servicio/);
  currentOrder = order;
});

test("cliente sin reseña: muestra el formulario y no la confirmación", async () => {
  currentOrder = {
    ...order,
    status: "completed",
    result: "repaired",
    completed_at: "2026-01-05T00:00:00Z",
    has_review: false,
    has_pending_price_change: false,
    price_changes: [],
  };
  goto(window, "/orders/o2");
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes("Califica el servicio"),
  );
  const text = window.document.querySelector("#view").textContent;
  assert.match(text, /Califica el servicio/);
  assert.doesNotMatch(text, /Gracias por calificar este servicio\./);
  currentOrder = order;
});
