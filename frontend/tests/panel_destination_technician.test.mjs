import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import { goto, jsonResponse, page, setupDom, waitFor } from "./dom_env.mjs";

const window = setupDom();

const me = {
  user: {
    id: "u-tech",
    email: "tecnico@test.dev",
    full_name: "Técnico Demo",
    is_active: true,
    created_at: "2026-01-01T00:00:00Z",
    roles: [{ id: "r2", name: "technician" }],
  },
  customer_profile: null,
  technician_id: "t1",
  permissions: [],
};

globalThis.fetch = async (url) => {
  const target = String(url).replace("http://localhost", "");
  if (target.startsWith("/api/v1/auth/me")) return jsonResponse(me);
  if (target.startsWith("/api/v1/ws/ticket")) return jsonResponse({ ticket: "t", expires_in: 60 });
  if (target.startsWith("/api/v1/notifications?limit=20")) return jsonResponse([]);
  if (target.startsWith("/api/v1/specialties")) return jsonResponse([]);
  if (target.startsWith("/api/v1/technicians/me/summary")) {
    return jsonResponse({ total: 0, by_status: {}, by_result: {}, by_specialty: [], pending_price_changes: 0 });
  }
  if (target.startsWith("/api/v1/technicians/me/stats")) {
    return jsonResponse({ active_orders: 0, completed_orders: 0, total_earnings: "0", pending_quotations: 0 });
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
  if (target.startsWith("/api/v1/repair-requests/available")) return jsonResponse(page([]));
  return jsonResponse({});
};

window.localStorage.setItem("pyckle_access_token", "test-token");

const assetsDir = fileURLToPath(new URL("../dist/assets/", import.meta.url));
const asset = readdirSync(assetsDir).find((name) => name.endsWith(".js"));
await import(pathToFileURL(path.join(assetsDir, asset)).href);

test("TECHNICIAN: 'Ir a mi panel' navega al panel técnico", async () => {
  goto(window, "/");
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes("Ir a mi panel"),
  );
  const button = [...window.document.querySelectorAll("button")].find((node) =>
    node.textContent.includes("Ir a mi panel"),
  );
  assert.ok(button);
  button.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));

  await waitFor(() => window.location.pathname === "/technician");
  assert.equal(window.location.pathname, "/technician");
});
