import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import { goto, jsonResponse, page, setupDom, waitFor } from "./dom_env.mjs";

const window = setupDom();

function technician(overrides) {
  return {
    id: "t-verified",
    full_name: "Técnico Verificado",
    bio: "Especialista en laptops.",
    experience_years: 8,
    is_verified: true,
    offers_home_service: true,
    offers_workshop_service: false,
    workshop_address: null,
    department_name: "Lambayeque",
    province_name: "Chiclayo",
    district_name: "José Leonardo Ortiz",
    rating_avg: "4.8",
    rating_count: 12,
    specialties: [],
    ...overrides,
  };
}

const VERIFIED = technician({ id: "t-verified", full_name: "Técnico Verificado", is_verified: true });
const UNVERIFIED = technician({ id: "t-unverified", full_name: "Técnico No Verificado", is_verified: false });

globalThis.fetch = async (url) => {
  const target = String(url).replace("http://localhost", "");
  if (target.startsWith("/api/v1/auth/me")) {
    return jsonResponse({ detail: "no auth" }, 401);
  }
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
  if (target.startsWith("/api/v1/specialties")) return jsonResponse([]);
  if (target.startsWith("/api/v1/technicians/") && target.includes("/reviews")) return jsonResponse([]);
  if (target.startsWith("/api/v1/technicians/")) {
    const id = target.split("/")[4];
    return jsonResponse(id === "t-verified" ? VERIFIED : UNVERIFIED);
  }
  if (target.startsWith("/api/v1/technicians")) return jsonResponse(page([VERIFIED, UNVERIFIED]));
  if (target.startsWith("/api/v1/notifications")) return jsonResponse([]);
  return jsonResponse({});
};

const assetsDir = fileURLToPath(new URL("../dist/assets/", import.meta.url));
const asset = readdirSync(assetsDir).find((name) => name.endsWith(".js"));
await import(pathToFileURL(path.join(assetsDir, asset)).href);
await waitFor(() => (window.document.querySelector("#view")?.textContent || "").includes("Repara"));

test("el listado muestra el badge solo en técnicos verificados", async () => {
  goto(window, "/technicians");
  await waitFor(() => (window.document.querySelector("#view")?.textContent || "").includes("Técnico Verificado"));
  const view = window.document.querySelector("#view");
  const badges = view.querySelectorAll('[aria-label="Técnico verificado"]');
  assert.equal(badges.length, 1, "debe haber exactamente un badge de verificación");
  assert.equal(badges[0].querySelectorAll("svg.lucide-badge-check").length, 1);
  assert.equal(badges[0].getAttribute("title"), "Técnico verificado");

  const unverifiedName = [...view.querySelectorAll("p")].find((node) =>
    node.textContent.includes("Técnico No Verificado"),
  );
  assert.ok(unverifiedName);
  assert.equal(unverifiedName.querySelector('[aria-label="Técnico verificado"]'), null);
});

test("el perfil público respeta el estado de verificación de la API", async () => {
  goto(window, "/technicians/t-verified");
  await waitFor(
    () =>
      (window.document.querySelector("#view")?.textContent || "").includes("Técnico Verificado") &&
      (window.document.querySelector("#view")?.textContent || "").includes("Calificación"),
  );
  assert.equal(
    window.document.querySelectorAll('#view [aria-label="Técnico verificado"]').length,
    1,
  );

  goto(window, "/technicians/t-unverified");
  await waitFor(
    () =>
      (window.document.querySelector("#view")?.textContent || "").includes("Técnico No Verificado") &&
      (window.document.querySelector("#view")?.textContent || "").includes("Calificación"),
  );
  assert.equal(
    window.document.querySelectorAll('#view [aria-label="Técnico verificado"]').length,
    0,
    "un perfil no verificado no debe mostrar el badge",
  );
});
