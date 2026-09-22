import assert from "node:assert/strict";
import test from "node:test";

import { closeAllModals, modal } from "../src/components/ui/index.js";
import { setupDom } from "./dom_env.mjs";

setupDom();

test("closeAllModals cierra todos los modales abiertos", () => {
  const first = modal("Primero", globalThis.document.createElement("p"));
  const second = modal("Segundo", globalThis.document.createElement("p"));
  globalThis.document.body.append(first, second);

  assert.equal(globalThis.document.querySelectorAll("[data-modal]").length, 2);

  closeAllModals();

  assert.equal(globalThis.document.querySelectorAll("[data-modal]").length, 0);
});

test("cerrar un modal no afecta a los demás", () => {
  const first = modal("Primero", globalThis.document.createElement("p"));
  const second = modal("Segundo", globalThis.document.createElement("p"));
  globalThis.document.body.append(first, second);

  first.close();

  assert.equal(first.isConnected, false);
  assert.equal(second.isConnected, true);
  closeAllModals();
});

test("Escape sin modales abiertos no falla", () => {
  closeAllModals();
  globalThis.document.dispatchEvent(new globalThis.KeyboardEvent("keydown", { key: "Escape" }));
  assert.equal(globalThis.document.querySelectorAll("[data-modal]").length, 0);
});
