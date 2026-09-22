import assert from "node:assert/strict";
import test from "node:test";

import { click, setupDom } from "./dom_env.mjs";

setupDom();
const { createPopover, closeAllPopovers } = await import("../src/components/popover.js");

function buildPopover(label) {
  const { document } = globalThis;
  const trigger = document.createElement("button");
  trigger.textContent = label;
  const panel = document.createElement("div");
  panel.textContent = `panel ${label}`;
  const wrapper = document.createElement("div");
  wrapper.append(trigger, panel);
  document.body.append(wrapper);
  const controller = createPopover({ trigger, panel, wrapper });
  return { trigger, panel, wrapper, controller };
}

test.afterEach(() => closeAllPopovers());

test("abre y cierra con el trigger", () => {
  const { trigger, panel, controller } = buildPopover("uno");
  assert.equal(controller.isOpen(), false);
  assert.equal(trigger.getAttribute("aria-expanded"), "false");

  click(trigger);
  assert.equal(controller.isOpen(), true);
  assert.equal(trigger.getAttribute("aria-expanded"), "true");
  assert.equal(panel.classList.contains("hidden"), false);

  click(trigger);
  assert.equal(controller.isOpen(), false);
  assert.equal(panel.classList.contains("hidden"), true);
});

test("abrir un popover cierra el anterior", () => {
  const first = buildPopover("uno");
  const second = buildPopover("dos");

  click(first.trigger);
  click(second.trigger);

  assert.equal(first.controller.isOpen(), false);
  assert.equal(second.controller.isOpen(), true);
  assert.equal(first.panel.classList.contains("hidden"), true);
});

test("un clic dentro del panel no lo cierra", () => {
  const { trigger, panel, controller } = buildPopover("uno");
  click(trigger);

  const inside = document.createElement("button");
  panel.append(inside);
  click(inside);

  assert.equal(controller.isOpen(), true);
  assert.equal(panel.classList.contains("hidden"), false);
});

test("un clic fuera cierra el popover", () => {
  const { trigger, controller } = buildPopover("uno");
  const outside = document.createElement("button");
  document.body.append(outside);

  click(trigger);
  click(outside);

  assert.equal(controller.isOpen(), false);
});

test("Escape cierra el popover abierto", () => {
  const { trigger, controller } = buildPopover("uno");
  click(trigger);
  assert.equal(controller.isOpen(), true);

  document.dispatchEvent(new globalThis.KeyboardEvent("keydown", { key: "Escape" }));
  assert.equal(controller.isOpen(), false);
});
