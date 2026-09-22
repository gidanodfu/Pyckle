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
import { alert, button, card, field, input, pageHeader } from "../../components/ui/index.js";
import { normalizePhone, PHONE_ERROR } from "../../lib/phone.js";
import { store } from "../../state/store.js";

export function CustomerProfilePage() {
  const me = store.get().me;
  const profile = me?.customer_profile || {};
  const location = locationFields({
    value: {
      department_id: profile.department_id,
      province_id: profile.province_id,
      district_id: profile.district_id,
    },
    required: true,
  });

  const phoneInput = input({ name: "phone", type: "tel", value: me?.user?.phone || "" });
  const phoneError = h("span", { class: "block text-xs font-medium text-red-600 hidden" }, PHONE_ERROR);
  phoneInput.addEventListener("input", () => {
    try {
      normalizePhone(phoneInput.value);
      phoneError.classList.add("hidden");
    } catch {
      phoneError.classList.remove("hidden");
    }
  });

  const submitButton = button("Guardar cambios", { type: "submit", iconName: "save", disabled: true });
  const form = h(
    "form",
    { class: "space-y-4" },
    h("div", { "data-error": "true" }),
    h("div", { "data-success": "true" }),
    field("Nombre completo", input({ name: "full_name", required: true, value: me?.user?.full_name || "" })),
    h("div", { class: "space-y-1" }, field("Teléfono", phoneInput), phoneError),
    field(
      "Dirección",
      input({ name: "address", value: profile.address || "", placeholder: "Av. Ejemplo 123" }),
      "Privada. Solo se comparte con el técnico cuando aceptas su cotización.",
    ),
    h("p", { class: "text-sm font-semibold text-slate-700" }, "Ubicación"),
    location.node,
    submitButton,
  );
  location.ready.finally(() => {
    submitButton.disabled = false;
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const errorBox = form.querySelector("[data-error]");
    const successBox = form.querySelector("[data-success]");
    const submit = form.querySelector("button[type=submit]");
    errorBox.replaceChildren();
    successBox.replaceChildren();
    submit.disabled = true;
    try {
      const data = new FormData(form);
      let phone = null;
      try {
        phone = normalizePhone(data.get("phone"));
      } catch {
        throw new Error(PHONE_ERROR);
      }
      if (!location.isValid()) throw new Error("Selecciona departamento, provincia y distrito.");
      await api.patch(endpoints.users.updateMe, {
        full_name: data.get("full_name"),
        phone,
      });
      await api.patch(endpoints.users.customerProfile, {
        address: data.get("address") || null,
        ...location.getValue(),
      });
      try {
        store.setMe(await api.get(endpoints.auth.me));
      } catch {
        // El perfil se guardó; un fallo de recarga no debe cerrar la sesión.
      }
      successBox.replaceChildren(alert("Perfil actualizado correctamente.", "success"));
    } catch (error) {
      errorBox.replaceChildren(alert(error.message || "No se pudo actualizar el perfil"));
    } finally {
      submit.disabled = false;
    }
  });

  const currentLocation = [profile.district_name, profile.province_name, profile.department_name]
    .filter(Boolean)
    .join(", ");

  return Container(
    h(
      "div",
      { class: "mx-auto max-w-2xl" },
      pageHeader("Mi perfil", "Actualiza tus datos de contacto, dirección y ubicación."),
      h(
        "div",
        { class: "mt-6 grid gap-4 sm:grid-cols-2" },
        card(
          h("p", { class: "text-xs uppercase tracking-wide text-slate-500" }, "Ubicación actual"),
          h("p", { class: "mt-1 font-medium text-slate-800" }, currentLocation || "Sin registrar"),
        ),
        card(
          h("p", { class: "text-xs uppercase tracking-wide text-slate-500" }, "Miembro desde"),
          h("p", { class: "mt-1 font-medium text-slate-800" }, me?.user?.created_at ? new Date(me.user.created_at).toLocaleDateString("es-PE", { day: "2-digit", month: "long", year: "numeric" }) : "-"),
        ),
      ),
      h("div", { class: "mt-6" }, card(form)),
    ),
  );
}
