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
import { alert, button, card, field, input, pageHeader, textarea } from "../../components/ui/index.js";
import { routes } from "../../lib/paths.js";
import { serviceModalityFields } from "./components/service-modality.js";
import { navigate } from "../../lib/navigation.js";

export async function TechnicianOwnProfile() {
  const [profile, specialties] = await Promise.all([
    api.get(endpoints.technicians.me),
    api.get(endpoints.specialties.list),
  ]);
  const currentIds = new Set((profile.specialties || []).map((item) => item.id));
  const location = locationFields({
    value: {
      department_id: profile.department_id,
      province_id: profile.province_id,
      district_id: profile.district_id,
    },
    required: true,
  });

  const specialtyBoxes = h(
    "div",
    { class: "grid gap-2 sm:grid-cols-2" },
    specialties.map((specialty) =>
      h(
        "label",
        { class: "flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm" },
        h("input", { type: "checkbox", name: "specialty_ids", value: specialty.id, checked: currentIds.has(specialty.id) }),
        specialty.name,
      ),
    ),
  );

  const initialModality =
    profile.offers_home_service && profile.offers_workshop_service
      ? "both"
      : profile.offers_workshop_service
        ? "workshop"
        : "home";
  const modality = serviceModalityFields({
    value: initialModality,
    address: profile.workshop_address || "",
  });

  const submitButton = button("Guardar cambios", { type: "submit", iconName: "save", disabled: true });
  const form = h(
    "form",
    { class: "space-y-4" },
    h("div", { "data-error": "true" }),
    field("Descripción profesional", textarea({ name: "bio", rows: 4, value: profile.bio || "" })),
    field("Años de experiencia", input({ name: "experience_years", type: "number", min: 0, max: 80, value: profile.experience_years })),
    modality.node,
    h("p", { class: "text-sm font-semibold text-slate-700" }, "Ubicación de servicio"),
    location.node,
    field("Especialidades", specialtyBoxes),
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
      const modalityError = modality.validate();
      if (modalityError) throw new Error(modalityError);
      await api.patch(endpoints.technicians.updateMe, {
        bio: data.get("bio") || null,
        experience_years: Number(data.get("experience_years")),
        ...modality.getPayload(),
        specialty_ids: data.getAll("specialty_ids"),
        ...location.getValue(),
      });
      navigate(routes.technicianDashboard);
    } catch (error) {
      errorBox.replaceChildren(alert(error.message || "No se pudo actualizar el perfil"));
      submit.disabled = false;
    }
  });

  return Container(
    h(
      "div",
      { class: "mx-auto max-w-2xl" },
      pageHeader("Perfil profesional", "Completa tu información para recibir más solicitudes de tu zona."),
      h("div", { class: "mt-6" }, card(form)),
    ),
  );
}
