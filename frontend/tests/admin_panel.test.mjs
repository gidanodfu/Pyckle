import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import { goto, jsonResponse, page, setupDom, waitFor } from "./dom_env.mjs";

const window = setupDom();

const adminUser = {
  user: {
    id: "a1",
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
  permissions: ["admin:users"],
};

let orders = [];

const orderItem = {
  id: "b1e91166-0486-4b41-9bb3-115bb26cc7cf",
  request_id: "req1",
  quotation_id: "q1",
  status: "diagnosis",
  result: null,
  final_price: "180.00",
  customer: { id: "u1", full_name: "Cliente Demo" },
  technician: {
    id: "t1",
    full_name: "Técnico Demo",
    rating_avg: "4.5",
    rating_count: 2,
    is_verified: true,
    district_name: "José Leonardo Ortiz",
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
  has_report: false,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
  completed_at: null,
};

globalThis.fetch = async (url) => {
  const target = String(url).replace("http://localhost", "");
  if (target.startsWith("/api/v1/auth/me")) return jsonResponse(adminUser);
  if (target.startsWith("/api/v1/ws/ticket")) return jsonResponse({ ticket: "t", expires_in: 60 });
  if (target.startsWith("/api/v1/admin/stats")) {
    return jsonResponse({
      total_users: 1,
      total_customers: 1,
      total_technicians: 1,
      total_requests: 1,
      open_requests: 0,
      total_orders: orders.length,
      completed_orders: 0,
      total_revenue: "0.00",
      requests_by_status: {},
    });
  }
  if (target.startsWith("/api/v1/admin/specialties")) {
    return jsonResponse([{ id: "s1", name: "Laptops", description: "Laptops", is_active: true }]);
  }
  if (target.startsWith("/api/v1/admin/technicians")) return jsonResponse(page([]));
  if (target.startsWith("/api/v1/admin/requests")) return jsonResponse(page([]));
  if (target.startsWith("/api/v1/admin/orders")) return jsonResponse(page(orders));
  if (target.startsWith("/api/v1/notifications?limit=20")) return jsonResponse([]);
  return jsonResponse({});
};

window.localStorage.setItem("pyckle_access_token", "test-token");

const assetsDir = fileURLToPath(new URL("../dist/assets/", import.meta.url));
const asset = readdirSync(assetsDir).find((name) => name.endsWith(".js"));
await import(pathToFileURL(path.join(assetsDir, asset)).href);

test("panel admin renderiza órdenes recientes", async () => {
  orders = [orderItem];
  goto(window, "/admin");
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes("Órdenes recientes"),
  );
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes("Técnico Demo"),
  );
  const text = window.document.querySelector("#view").textContent;
  assert.match(text, /b1e91166/);
  assert.match(text, /180\.00/);
});

test("panel admin muestra estado vacío de órdenes", async () => {
  orders = [];
  goto(window, "/admin");
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes("Sin órdenes"),
  );
  assert.match(window.document.querySelector("#view").textContent, /Sin órdenes/);
});
