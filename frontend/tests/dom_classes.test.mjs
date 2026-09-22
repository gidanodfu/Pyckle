import assert from "node:assert/strict";
import test from "node:test";

import { setupDom } from "./dom_env.mjs";

setupDom();

const { toggleClasses } = await import("../src/components/dom.js");

const MULTI = "border-blue-500 bg-blue-50 ring-1 ring-blue-500";
const TOKENS = MULTI.split(" ");

test("toggleClasses aplica cada clase como token independiente (sin DOMException)", () => {
  const calls = [];
  const fake = { classList: { toggle: (token, force) => calls.push([token, force]) } };

  toggleClasses(fake, MULTI, true);

  assert.deepEqual(
    calls.map(([token]) => token),
    TOKENS,
  );
  assert.ok(calls.every(([, force]) => force === true));
  assert.ok(calls.every(([token]) => !/\s/.test(token)));
});

test("toggleClasses acepta arrays y aplica/elimina las clases reales", () => {
  const node = document.createElement("div");

  toggleClasses(node, TOKENS, true);
  for (const token of TOKENS) assert.ok(node.classList.contains(token), token);

  toggleClasses(node, TOKENS, false);
  for (const token of TOKENS) assert.ok(!node.classList.contains(token), token);
});

test("toggleClasses ignora espacios y elementos vacíos", () => {
  const calls = [];
  const fake = { classList: { toggle: (token, force) => calls.push([token, force]) } };

  toggleClasses(fake, ["  foo ", ["bar", ""], null], true);

  assert.deepEqual(
    calls.map(([token]) => token),
    ["foo", "bar"],
  );
});
