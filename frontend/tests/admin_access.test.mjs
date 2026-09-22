import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import { goto, jsonResponse, page, setupDom, waitFor } from "./dom_env.mjs";

const window = setupDom();

const calls = [];

const adminUser = {
  user: {
    id: "u-admin",
    email: "admin@test.dev",
    full_name: "Admin Demo",
    phone: "+51900000000",
    is_active: true,
    is_verified: true,
    created_at: "2026-01-01T00:00:00Z",
    roles: [{ id: "r3", name: "admin" }],
  },
  customer_profile: null,
  technician_id: null,
  permissions: ["admin:users", "admin:orders", "admin:reports", "order:read_all"],
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
  diagnosis: "Placa con sulfatación leve.",
  work_performed: "Limpieza y resoldado.",
  tests_performed: "Encendido estable 2h.",
  technician_notes: "INTERNAL: no informar al cliente",
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
  price_changes: [
    {
      id: "pc1",
      previous_price: "180.00",
      new_price: "200.00",
      reason: "Repuesto adicional",
      status: "pending",
      decided_note: null,
      decided_at: null,
      created_at: "2026-01-03T00:00:00Z",
    },
  ],
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
  report: {
    id: "r1",
    version: 1,
    content_type: "application/pdf",
    size_bytes: 100,
    generated_at: "2026-01-04T00:00:00Z",
    download_url: "/api/v1/orders/o1/report",
  },
  report_versions: 1,
  has_pending_price_change: true,
  has_review: false,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
};

let currentOrder = order;

const listItem = {
  id: "o1",
  request_id: "req1",
  quotation_id: "q1",
  status: "diagnosis",
  result: null,
  final_price: "180.00",
  customer: { id: "u-cust", full_name: "Cliente Demo" },
  technician: {
    id: "t1",
    full_name: "Técnico Demo",
    rating_avg: "4.5",
    rating_count: 2,
    is_verified: true,
    district_name: "JLO",
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
  has_pending_price_change: false,
  has_report: true,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
  completed_at: null,
};

const request = {
  id: "req1",
  title: "Laptop no enciende",
  description: "La laptop no enciende desde ayer.",
  status: "accepted",
  modality: "home",
  address: "Av. Prueba 123",
  district_name: "JLO",
  province_name: "Chiclayo",
  department_name: "Lambayeque",
  specialty: { id: "s1", name: "Laptops", slug: "laptops", is_active: true },
  customer: { id: "u-cust", full_name: "Cliente Demo" },
  assigned_technician: { id: "t1", full_name: "Técnico Demo", is_verified: true },
  images: [],
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

globalThis.fetch = async (url, options = {}) => {
  const target = String(url).replace("http://localhost", "");
  const method = (options.method || "GET").toUpperCase();
  calls.push({ target, method });

  if (target.startsWith("/api/v1/auth/me")) return jsonResponse(adminUser);
  if (target.startsWith("/api/v1/ws/ticket")) return jsonResponse({ ticket: "t", expires_in: 60 });
  if (target.startsWith("/api/v1/notifications?limit=20")) return jsonResponse([]);
  if (target.startsWith("/api/v1/specialties")) {
    return jsonResponse([{ id: "s1", name: "Laptops", slug: "laptops", is_active: true }]);
  }
  if (target.startsWith("/api/v1/admin/stats")) {
    return jsonResponse({
      total_users: 1,
      total_customers: 1,
      total_technicians: 0,
      total_requests: 0,
      open_requests: 0,
      total_orders: 1,
      completed_orders: 0,
      total_revenue: "0.00",
      requests_by_status: {},
    });
  }
  if (target.startsWith("/api/v1/admin/technicians")) return jsonResponse(page([]));
  if (target.startsWith("/api/v1/admin/requests")) return jsonResponse(page([]));
  if (target.startsWith("/api/v1/orders/o1/customer-profile")) {
    return jsonResponse({
      id: "u-cust",
      full_name: "Cliente Demo",
      member_since: "2026-01-01T00:00:00Z",
      completed_repairs: 1,
      department_name: "Lambayeque",
      province_name: "Chiclayo",
      district_name: "JLO",
    });
  }
  if (target.startsWith("/api/v1/orders/o1")) return jsonResponse(currentOrder);
  if (target.startsWith("/api/v1/repair-requests/req1")) return jsonResponse(request);
  if (target.startsWith("/api/v1/quotations/request/req1")) return jsonResponse([]);
  if (target.startsWith("/api/v1/orders?request_id=req1")) return jsonResponse(page([]));
  if (target.startsWith("/api/v1/admin/orders")) {
    const parsed = new URL(target, "http://localhost");
    const offset = Number(parsed.searchParams.get("offset") || 0);
    return jsonResponse({ ...page([listItem]), total: 30, limit: 20, offset });
  }
  return jsonResponse({});
};

window.localStorage.setItem("pyckle_access_token", "test-token");

const assetsDir = fileURLToPath(new URL("../dist/assets/", import.meta.url));
const asset = readdirSync(assetsDir).find((name) => name.endsWith(".js"));
await import(pathToFileURL(path.join(assetsDir, asset)).href);

test("navbar admin: Administración y Órdenes, sin Chat", async () => {
  goto(window, "/admin");
  await waitFor(() => window.document.querySelector("header"));
  const header = window.document.querySelector("header").textContent;
  assert.match(header, /Administración/);
  assert.match(header, /Órdenes/);
  assert.doesNotMatch(header, /Chat/);
});

test("admin no puede entrar a /chat manualmente", async () => {
  goto(window, "/chat");
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes("No tienes acceso"),
  );
  assert.doesNotMatch(window.document.querySelector("#view").textContent, /Escribe un mensaje/);
});

test("detalle de orden admin es solo lectura", async () => {
  calls.length = 0;
  goto(window, "/orders/o1");
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes("Detalles técnicos"),
  );
  const text = window.document.querySelector("#view").textContent;

  assert.match(text, /Ver solicitud/);
  assert.match(text, /Perfil del cliente/);
  assert.match(text, /Descargar informe/);
  assert.match(text, /Seguimiento/);
  assert.match(text, /Cotización y cambios de precio/);
  assert.match(text, /Costos/);
  assert.match(text, /Placa con sulfatación leve/);

  assert.doesNotMatch(text, /Abrir chat/);
  assert.doesNotMatch(text, /Actualizar proceso/);
  assert.doesNotMatch(text, /Guardar detalles/);
  assert.doesNotMatch(text, /Proponer nuevo costo/);
  assert.doesNotMatch(text, /Agregar costo/);
  assert.doesNotMatch(text, /Completar reparación/);
  assert.doesNotMatch(text, /Declarar no reparable/);
  assert.doesNotMatch(text, /Cancelar reparación/);

  // No debe consultar conversaciones para el administrador.
  assert.equal(
    calls.some((call) => call.target.includes("/conversations")),
    false,
  );
});

test("detalle admin: no muestra la confirmación de reseña del cliente", async () => {
  currentOrder = {
    ...order,
    status: "completed",
    result: "repaired",
    has_review: true,
    has_pending_price_change: false,
    price_changes: [],
  };
  goto(window, "/orders/o1");
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes("Detalles técnicos"),
  );
  const text = window.document.querySelector("#view").textContent;
  assert.doesNotMatch(text, /Gracias por calificar este servicio\./);
  currentOrder = order;
});

test("detalle de solicitud admin: sin chat", async () => {
  calls.length = 0;
  goto(window, "/requests/req1");
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes("Detalle de solicitud"),
  );
  const text = window.document.querySelector("#view").textContent;
  assert.doesNotMatch(text, /Abrir chat/);
  assert.doesNotMatch(text, /Moderación de administrador/);
  assert.equal(
    calls.some((call) => call.target.includes("/conversations")),
    false,
  );
});

test("listado admin de órdenes pagina y filtra", async () => {
  calls.length = 0;
  goto(window, "/admin/orders");
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes("Mostrando 1-1 de 30"),
  );

  const next = [...window.document.querySelectorAll("button")].find(
    (node) => node.textContent.includes("Siguiente"),
  );
  assert.ok(next, "debe existir paginación");
  next.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));
  await waitFor(() =>
    calls.some((call) => call.target.includes("/admin/orders") && call.target.includes("offset=20")),
  );
});
