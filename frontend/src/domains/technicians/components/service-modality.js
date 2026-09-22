/*
 * Copyright (C) 2026 Josue David (gidanodfu)
 * https://github.com/gidanodfu
 *
 * This file is part of Pyckle.
 *
 * Pyckle is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as
 * published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 *
 * Pyckle is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with Pyckle. If not, see <https://www.gnu.org/licenses/>.
 */

import { h, toggleClasses } from "../../../components/dom.js";
import { field, input } from "../../../components/ui/index.js";

export const SERVICE_MODALITIES = [
  { value: "home", label: "A domicilio", hint: "Voy al lugar del cliente." },
  { value: "workshop", label: "En local o taller", hint: "El cliente lleva el dispositivo a mi local." },
  { value: "both", label: "Ambas", hint: "Atiendo a domicilio y en taller." },
];

const OPTION_BASE = "flex cursor-pointer items-start gap-3 rounded-lg border px-3 py-3 transition";
const OPTION_SELECTED = ["border-blue-500", "bg-blue-50", "ring-1", "ring-blue-500"];
const OPTION_IDLE = "border-slate-200";

/**
 * Radios exclusivos local / domicilio / ambas con dirección condicional.
 * Opciones apiladas verticalmente a ancho completo. Nunca envía una dirección
 * de taller si no se atiende en taller.
 */
export function serviceModalityFields({ value = "home", address = "" } = {}) {
  const addressInput = input({ name: "workshop_address", value: address, placeholder: "Av. Taller 456" });
  const addressBlock = field(
    "Dirección del local o taller",
    addressInput,
    "Obligatoria si atiendes en local.",
  );

  const options = SERVICE_MODALITIES.map((modality) => {
    const radio = h("input", {
      type: "radio",
      name: "service_modality",
      value: modality.value,
      checked: modality.value === value,
      class: "mt-0.5",
    });
    const label = h(
      "label",
      { class: `${OPTION_BASE} ${OPTION_IDLE}` },
      radio,
      h(
        "span",
        {},
        h("span", { class: "block text-sm font-medium text-slate-800" }, modality.label),
        h("span", { class: "block text-xs text-slate-500" }, modality.hint),
      ),
    );
    return { label };
  });

  const fieldset = h(
    "fieldset",
    { class: "space-y-2 rounded-lg border border-slate-200 bg-slate-50 p-4" },
    h("legend", { class: "px-1 text-sm font-semibold text-slate-700" }, "Modalidad de atención"),
    ...options.map((option) => option.label),
    addressBlock,
  );

  function getValue() {
    const checked = fieldset.querySelector('input[name="service_modality"]:checked');
    return checked ? checked.value : "home";
  }

  function syncSelected() {
    for (const option of options) {
      const radio = option.label.querySelector('input[name="service_modality"]');
      toggleClasses(option.label, OPTION_SELECTED, radio.checked);
      toggleClasses(option.label, OPTION_IDLE, !radio.checked);
    }
  }

  function syncAddress() {
    const atWorkshop = getValue() !== "home";
    addressBlock.classList.toggle("hidden", !atWorkshop);
    addressInput.required = atWorkshop;
  }

  function getPayload() {
    const modality = getValue();
    return {
      offers_home_service: modality !== "workshop",
      offers_workshop_service: modality !== "home",
      workshop_address: modality === "home" ? null : addressInput.value.trim() || null,
    };
  }

  function validate() {
    const payload = getPayload();
    if (payload.offers_workshop_service && !payload.workshop_address) {
      return "Si atiendes en taller, indica la dirección del local.";
    }
    return null;
  }

  fieldset.addEventListener("change", () => {
    syncSelected();
    syncAddress();
  });
  syncSelected();
  syncAddress();
  return { node: fieldset, getValue, getPayload, validate };
}
