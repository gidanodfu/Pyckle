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

import { api } from "../../api/client.js";
import { endpoints } from "../../api/endpoints.js";
import { h } from "../../components/dom.js";
import { locationFields } from "../../components/geo.js";
import { Container } from "../../components/layout/index.js";
import {
  alert,
  button,
  card,
  field,
  input,
  pageHeader,
  select,
  textarea,
} from "../../components/ui/index.js";
import { routes } from "../../lib/paths.js";
import { navigate } from "../../lib/navigation.js";
import { MAX_IMAGE_MB, MAX_IMAGES, validateImageSize } from "../../lib/uploads.js";
import { store } from "../../state/store.js";

const MODALITIES = [
  { value: "home", label: "A domicilio" },
  { value: "workshop", label: "En taller" },
];

export async function RequestCreate() {
  const specialties = await api.get(endpoints.specialties.list);
  const profile = store.get().me?.customer_profile;
  const location = locationFields({
    value: {
      department_id: profile?.department_id,
      province_id: profile?.province_id,
      district_id: profile?.district_id,
    },
    required: true,
    hint: "Selecciona dónde se realizará el servicio.",
  });

  const addressInput = input({
    name: "address",
    value: profile?.address || "",
    placeholder: "Av. Ejemplo 123",
  });
  const addressField = field(
    "Dirección del servicio",
    addressInput,
    "Privada: el técnico la verá recién cuando aceptes su cotización.",
  );

  const modalitySelect = select("modality", MODALITIES);
  function syncAddress() {
    const isHome = modalitySelect.value === "home";
    addressField.classList.toggle("hidden", !isHome);
    addressInput.required = isHome;
  }
  modalitySelect.addEventListener("change", syncAddress);
  syncAddress();

  const imagesInput = input({
    name: "images",
    type: "file",
    accept: "image/png,image/jpeg,image/webp",
    multiple: true,
  });
  const imagesFeedback = h("p", { class: "hidden text-xs font-medium text-red-600" });
  // Feedback inmediato: los archivos que exceden el límite no entran al flujo
  // de subida ni se envían al almacenamiento.
  imagesInput.addEventListener("change", () => {
    const invalid = [...imagesInput.files].map(validateImageSize).filter(Boolean);
    if (invalid.length) {
      imagesFeedback.textContent = `${invalid.join(" ")} No se subirán esos archivos.`;
      imagesFeedback.classList.remove("hidden");
    } else {
      imagesFeedback.textContent = "";
      imagesFeedback.classList.add("hidden");
    }
  });

  const submitButton = button("Publicar solicitud", {
    type: "submit",
    class: "w-full sm:w-auto",
    iconName: "send",
    disabled: true,
  });
  const form = h(
    "form",
    { class: "space-y-4" },
    h("div", { "data-error": "true" }),
    field("Título", input({ name: "title", required: true, placeholder: "Ej: Laptop no enciende" })),
    field(
      "Especialidad",
      select("specialty_id", [
        { value: "", label: "Selecciona una especialidad" },
        ...specialties.map((item) => ({ value: item.id, label: item.name })),
      ]),
    ),
    field("Descripción", textarea({ name: "description", required: true, placeholder: "Describe el problema con el mayor detalle posible." })),
    h(
      "div",
      { class: "grid gap-4 sm:grid-cols-2" },
      field("Modalidad", modalitySelect),
      field("Presupuesto mínimo (S/)", input({ name: "budget_min", type: "number", min: 0, step: "0.01" })),
      field("Presupuesto máximo (S/)", input({ name: "budget_max", type: "number", min: 0, step: "0.01" })),
    ),
    h("p", { class: "text-sm font-semibold text-slate-700" }, "Ubicación"),
    location.node,
    addressField,
    field(
      "Imágenes (opcional)",
      h("div", { class: "space-y-1" }, imagesInput, imagesFeedback),
      `Hasta ${MAX_IMAGES} imágenes de ${MAX_IMAGE_MB} MB cada una.`,
    ),
    submitButton,
  );
  location.ready.finally(() => {
    submitButton.disabled = false;
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const errorBox = form.querySelector("[data-error]");
    const submit = form.querySelector("button[type=submit]");
    errorBox.replaceChildren();
    submit.disabled = true;
    const data = new FormData(form);
    try {
      if (!location.isValid()) throw new Error("Selecciona departamento, provincia y distrito.");
      if (data.get("modality") === "home" && !String(data.get("address") || "").trim()) {
        throw new Error("Las solicitudes a domicilio requieren una dirección.");
      }
      const payload = {
        title: data.get("title"),
        description: data.get("description"),
        specialty_id: data.get("specialty_id") || null,
        modality: data.get("modality"),
        address: data.get("address") || null,
        ...location.getValue(),
      };
      if (data.get("budget_min")) payload.budget_min = data.get("budget_min");
      if (data.get("budget_max")) payload.budget_max = data.get("budget_max");

      const request = await api.post(endpoints.requests.create, payload);
      const rejected = [];
      for (const file of imagesInput.files) {
        // Segunda comprobación antes de subir: un archivo inválido no inicia
        // la subida al almacenamiento.
        const sizeError = validateImageSize(file);
        if (sizeError) {
          rejected.push(sizeError);
          continue;
        }
        try {
          await api.upload(endpoints.requests.images(request.id), file);
        } catch (error) {
          errorBox.replaceChildren(alert(`Solicitud creada, pero una imagen falló: ${error.message}`, "warning"));
        }
      }
      if (rejected.length) {
        errorBox.replaceChildren(alert(`Solicitud creada. ${rejected.join(" ")}`, "warning"));
      }
      navigate(routes.requestDetail(request.id));
    } catch (error) {
      errorBox.replaceChildren(alert(error.message || "No se pudo crear la solicitud"));
      submit.disabled = false;
    }
  });

  return Container(
    h(
      "div",
      { class: "mx-auto max-w-3xl" },
      pageHeader("Nueva solicitud", "Describe el problema para recibir cotizaciones de técnicos."),
      h("div", { class: "mt-6" }, card(form)),
    ),
  );
}
