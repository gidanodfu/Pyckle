import assert from "node:assert/strict";
import test from "node:test";

import { setupDom } from "./dom_env.mjs";

const window = setupDom();
window.localStorage.setItem("pyckle_access_token", "test-token");

const { api, setTokens } = await import("../src/api/client.js");

const REQUIRED_METHODS = ["get", "post", "put", "patch", "del", "delete", "download", "upload"];

test("el cliente HTTP expone todos los métodos del contrato", () => {
  for (const method of REQUIRED_METHODS) {
    assert.equal(typeof api[method], "function", `api.${method} debe ser una función`);
  }
});

test("api.put envía el verbo PUT con autorización y body JSON", async () => {
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options });
    return new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  };

  const result = await api.put("/orders/o1/repair-details", { diagnosis: "x" });

  assert.deepEqual(result, { ok: true });
  assert.equal(calls.length, 1);
  assert.equal(calls[0].url, "/api/v1/orders/o1/repair-details");
  assert.equal(calls[0].options.method, "PUT");
  assert.equal(calls[0].options.headers.Authorization, "Bearer test-token");
  assert.equal(calls[0].options.body, JSON.stringify({ diagnosis: "x" }));
});

test("api.download reintenta tras refrescar el token", async () => {
  setTokens({ access_token: "old", refresh_token: "refresh-1" });
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options });
    if (url.endsWith("/auth/refresh")) {
      return new Response(
        JSON.stringify({ access_token: "new", refresh_token: "refresh-2" }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    }
    const reportCalls = calls.filter((call) => call.url.endsWith("/orders/o1/report"));
    if (reportCalls.length === 1) return new Response(null, { status: 401 });
    return new Response(new Blob([new Uint8Array([37, 80, 68, 70])]), { status: 200 });
  };

  const blob = await api.download("/orders/o1/report");
  assert.ok(blob.size > 0);
  assert.ok(calls.some((call) => call.url.endsWith("/auth/refresh")));
  const lastReport = calls.filter((call) => call.url.endsWith("/orders/o1/report")).pop();
  assert.equal(lastReport.options.headers.Authorization, "Bearer new");
});

test("api.delete usa el verbo DELETE sin body", async () => {
  const calls = [];
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options });
    return new Response(null, { status: 204 });
  };

  await api.delete("/admin/users/u1");

  assert.equal(calls[0].options.method, "DELETE");
  assert.equal(calls[0].options.body, undefined);
});
