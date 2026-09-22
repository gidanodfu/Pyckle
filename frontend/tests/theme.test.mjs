import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import { goto, jsonResponse, setupDom, waitFor } from "./dom_env.mjs";

const window = setupDom();
window.localStorage.clear();

globalThis.fetch = async (url) => {
  const target = String(url).replace("http://localhost", "");
  if (target.startsWith("/api/v1/auth/me")) return jsonResponse({ detail: "no auth" }, 401);
  if (target.startsWith("/api/v1/specialties")) return jsonResponse([]);
  return jsonResponse({});
};

const assetsDir = fileURLToPath(new URL("../dist/assets/", import.meta.url));
const asset = readdirSync(assetsDir).find((name) => name.endsWith(".js"));
await import(pathToFileURL(path.join(assetsDir, asset)).href);

function click(node) {
  node.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
}

test("el tema alterna entre claro y oscuro y se persiste", async () => {
  goto(window, "/");
  await waitFor(() => window.document.querySelector("header"));
  const toggle = [...window.document.querySelectorAll("header button")].find((node) =>
    (node.getAttribute("aria-label") || "").includes("tema"),
  );
  assert.ok(toggle, "debe existir el botón de tema");

  const before = window.document.documentElement.classList.contains("dark");
  click(toggle);
  const after = window.document.documentElement.classList.contains("dark");
  assert.equal(after, !before, "el tema debe alternar");
  assert.equal(window.localStorage.getItem("pyckle_theme"), after ? "dark" : "light");

  click(toggle);
  assert.equal(window.document.documentElement.classList.contains("dark"), before);
});

test("el menú móvil despliega y pliega la navegación", async () => {
  goto(window, "/");
  await waitFor(() => window.document.querySelector("header"));
  const menu = [...window.document.querySelectorAll("header button")].find(
    (node) => node.getAttribute("aria-label") === "Abrir menú",
  );
  assert.ok(menu, "debe existir el botón de menú");
  const nav = window.document.querySelector("header #main-nav");
  assert.ok(nav, "debe existir el contenedor de navegación");
  assert.ok(nav.classList.contains("hidden"), "en móvil inicia plegado");

  click(menu);
  assert.equal(nav.classList.contains("hidden"), false);
  assert.equal(menu.getAttribute("aria-expanded"), "true");

  click(menu);
  assert.equal(nav.classList.contains("hidden"), true);
  assert.equal(menu.getAttribute("aria-expanded"), "false");
});
