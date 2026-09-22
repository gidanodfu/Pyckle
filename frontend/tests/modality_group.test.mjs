import assert from "node:assert/strict";
import test from "node:test";

import { setupDom } from "./dom_env.mjs";

setupDom();

const { serviceModalityFields } = await import(
  "../src/domains/technicians/components/service-modality.js"
);

test("modalidad: opciones verticales, mismo grupo, exclusivas y valores intactos", () => {
  const modality = serviceModalityFields({ value: "home" });
  const node = modality.node;

  assert.equal(node.tagName, "FIELDSET");
  assert.equal(node.querySelector("legend").textContent, "Modalidad de atención");

  const radios = [...node.querySelectorAll('input[name="service_modality"]')];
  assert.equal(radios.length, 3);
  assert.deepEqual(
    radios.map((radio) => radio.value).sort(),
    ["both", "home", "workshop"],
  );
  assert.equal(radios.filter((radio) => radio.checked).length, 1);
  assert.equal(modality.getValue(), "home");

  const SELECTED = ["border-blue-500", "bg-blue-50", "ring-1", "ring-blue-500"];
  const labelFor = (value) => radios.find((radio) => radio.value === value).closest("label");
  const hasSelected = (label) => SELECTED.every((token) => label.classList.contains(token));

  // El estado inicial aplica las clases de selección como tokens.
  assert.ok(hasSelected(labelFor("home")));
  assert.ok(!hasSelected(labelFor("workshop")));
  assert.ok(labelFor("workshop").classList.contains("border-slate-200"));

  const workshop = radios.find((radio) => radio.value === "workshop");
  workshop.checked = true;
  workshop.dispatchEvent(new window.Event("change", { bubbles: true }));

  assert.equal(radios.filter((radio) => radio.checked).length, 1);
  assert.equal(modality.getValue(), "workshop");

  // Al cambiar de opción no quedan clases residuales en la anterior.
  assert.ok(hasSelected(labelFor("workshop")));
  assert.ok(!hasSelected(labelFor("home")));
  assert.ok(labelFor("home").classList.contains("border-slate-200"));

  const payload = modality.getPayload();
  assert.equal(payload.offers_home_service, false);
  assert.equal(payload.offers_workshop_service, true);
});
