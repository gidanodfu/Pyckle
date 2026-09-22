import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import { goto, jsonResponse, setupDom, waitFor } from "./dom_env.mjs";

const window = setupDom();

const me = {
  user: {
    id: "u-admin",
    email: "admin@test.dev",
    full_name: "Admin Demo",
    is_active: true,
    created_at: "2026-01-01T00:00:00Z",
    roles: [{ id: "r3", name: "admin" }],
  },
  customer_profile: null,
  technician_id: null,
  permissions: ["admin:users", "admin:orders"],
};

globalThis.fetch = async (url) => {
  const target = String(url).replace("http://localhost", "");
  if (target.startsWith("/api/v1/auth/me")) return jsonResponse(me);
  if (target.startsWith("/api/v1/ws/ticket")) return jsonResponse({ ticket: "t", expires_in: 60 });
  if (target.startsWith("/api/v1/notifications?limit=20")) return jsonResponse([]);
  if (target.startsWith("/api/v1/specialties")) return jsonResponse([]);
  return jsonResponse({});
};

window.localStorage.setItem("pyckle_access_token", "test-token");

const assetsDir = fileURLToPath(new URL("../dist/assets/", import.meta.url));
const asset = readdirSync(assetsDir).find((name) => name.endsWith(".js"));
await import(pathToFileURL(path.join(assetsDir, asset)).href);

test("ADMIN: 'Ir a mi panel' navega al panel administrativo", async () => {
  goto(window, "/");
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes("Ir a mi panel"),
  );
  const button = [...window.document.querySelectorAll("button")].find((node) =>
    node.textContent.includes("Ir a mi panel"),
  );
  assert.ok(button, "debe existir el botón 'Ir a mi panel'");
  button.dispatchEvent(new window.MouseEvent("click", { bubbles: true }));

  await waitFor(() => window.location.pathname === "/admin");
  assert.equal(window.location.pathname, "/admin");
  assert.notEqual(window.location.pathname, "/requests/new");
});
