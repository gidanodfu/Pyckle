import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import { goto, jsonResponse, page, setupDom, waitFor } from "./dom_env.mjs";

const window = setupDom();

const me = {
  user: {
    id: "u-cust",
    email: "cliente@test.dev",
    full_name: "Cliente Demo",
    is_active: true,
    created_at: "2026-01-01T00:00:00Z",
    roles: [{ id: "r1", name: "customer" }],
  },
  customer_profile: {
    id: "cp1",
    address: "Av. Demo 1",
    district: "JLO",
    city: "Lambayeque",
    department_id: "d1",
    province_id: "p1",
    district_id: "x1",
    department_name: "Lambayeque",
    province_name: "Chiclayo",
    district_name: "JLO",
  },
  technician_id: null,
  permissions: [],
};

globalThis.fetch = async (url) => {
  const target = String(url).replace("http://localhost", "");
  if (target.startsWith("/api/v1/auth/me")) return jsonResponse(me);
  if (target.startsWith("/api/v1/ws/ticket")) return jsonResponse({ ticket: "t", expires_in: 60 });
  if (target.startsWith("/api/v1/notifications?limit=20")) return jsonResponse([]);
  if (target.startsWith("/api/v1/specialties")) return jsonResponse([]);
  if (target.includes("/repair-requests?limit=5")) return jsonResponse(page([]));
  if (target.includes("/orders?limit=5")) return jsonResponse(page([]));
  return jsonResponse({});
};

window.localStorage.setItem("pyckle_access_token", "test-token");

const assetsDir = fileURLToPath(new URL("../dist/assets/", import.meta.url));
const asset = readdirSync(assetsDir).find((name) => name.endsWith(".js"));
await import(pathToFileURL(path.join(assetsDir, asset)).href);

test("CUSTOMER: 'Ir a mi panel' navega al panel de cliente", async () => {
  goto(window, "/");
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes("Ir a mi panel"),
  );
  const button = [...window.document.querySelectorAll("button")].find((node) =>
    node.textContent.includes("Ir a mi panel"),
  );
  assert.ok(button);
  button.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));

  await waitFor(() => window.location.pathname === "/dashboard");
  assert.equal(window.location.pathname, "/dashboard");
});
