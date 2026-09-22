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

import { h } from "../../components/dom.js";
import { locationFields } from "../../components/geo.js";
import { googleIcon } from "../../components/google-icon.js";
import { icon } from "../../components/icons.js";
import { alert, button, field, input, passwordInput, select } from "../../components/ui/index.js";
import { routes } from "../../lib/paths.js";
import { normalizePhone, PHONE_ERROR } from "../../lib/phone.js";
import { onAuthenticated } from "../../app/session.js";
import { navigate } from "../../lib/navigation.js";
import { auth } from "../../services/auth.js";
import { serviceModalityFields } from "../technicians/components/service-modality.js";
import { googleAuthButton } from "./google-button.js";
import { authShell, submitHandler } from "./shell.js";

function googleVerifiedCard(info) {
  return h(
    "div",
    { class: "space-y-1 rounded-lg border border-emerald-200 bg-emerald-50 p-4" },
    h(
      "p",
      { class: "flex items-center gap-2 text-sm font-semibold text-emerald-800" },
      googleIcon({ size: 18 }),
      "Cuenta de Google verificada",
    ),
    h("p", { class: "text-sm font-medium text-slate-800" }, info.email),
    h(
      "p",
      { class: "text-xs text-slate-600" },
      "Completa tus datos para crear tu cuenta en Pyckle.",
    ),
  );
}

export function Register() {
  const params = new URLSearchParams(window.location.search);
  const presetRole = params.get("role") === "technician" ? "technician" : "customer";
  // Onboarding de un usuario nuevo que llegó desde Google OAuth.
  const oauthToken = params.get("oauth_token");
  const location = locationFields({ required: true, hint: "La ubicación es obligatoria para conectar con técnicos de tu zona." });

  const phoneInput = input({ name: "phone", type: "tel", required: true, placeholder: "+51 999 123 456", autocomplete: "tel" });
  const phoneHint = h("span", { class: "block text-xs text-slate-500" }, "Celular peruano de 9 dígitos.");
  const phoneError = h("span", { class: "block text-xs font-medium text-red-600 hidden" }, PHONE_ERROR);
  phoneInput.addEventListener("input", () => {
    try {
      normalizePhone(phoneInput.value);
      phoneError.classList.add("hidden");
      phoneInput.classList.remove("border-red-400");
    } catch {
      phoneError.classList.remove("hidden");
      phoneInput.classList.add("border-red-400");
    }
  });

  const customerAddress = field(
    "Dirección",
    input({ name: "address", placeholder: "Av. Ejemplo 123, distrito" }),
    "Privada. Solo se mostrará al técnico cuando aceptes su cotización.",
  );
  const modality = serviceModalityFields();

  const roleSelect = select(
    "role",
    [
      { value: "customer", label: "Cliente - necesito reparar un dispositivo" },
      { value: "technician", label: "Técnico - ofrezco servicios de reparación" },
    ],
    { value: presetRole },
  );

  function syncRoleFields() {
    const isTechnician = roleSelect.value === "technician";
    customerAddress.classList.toggle("hidden", isTechnician);
    modality.node.classList.toggle("hidden", !isTechnician);
  }
  roleSelect.addEventListener("change", syncRoleFields);

  const termsCheckbox = h("input", {
    type: "checkbox",
    name: "terms",
    id: "register-terms",
    "aria-describedby": "register-terms-error",
  });
  const termsError = h(
    "p",
    { id: "register-terms-error", class: "hidden text-xs font-medium text-red-600" },
    "Debes aceptar los Términos y Condiciones para crear tu cuenta.",
  );
  const termsBlock = h(
    "div",
    { class: "space-y-1 rounded-lg border border-slate-200 bg-slate-50 p-4" },
    h(
      "label",
      { class: "flex items-start gap-2 text-sm text-slate-700" },
      termsCheckbox,
      h(
        "span",
        {},
        "Acepto los ",
        h(
          "a",
          {
            href: routes.terms,
            target: "_blank",
            rel: "noopener noreferrer",
            class: "font-medium text-blue-700 hover:underline",
          },
          "Términos y Condiciones",
        ),
      ),
    ),
    termsError,
  );
  termsCheckbox.addEventListener("change", () => {
    const accepted = termsCheckbox.checked;
    termsCheckbox.setAttribute("aria-invalid", accepted ? "false" : "true");
    termsError.classList.toggle("hidden", accepted);
  });

  const submitButton = button(oauthToken ? "Completar registro" : "Crear cuenta", {
    type: "submit",
    variant: "success",
    class: "w-full",
    iconName: "user",
    disabled: true,
  });
  // La identidad Google solo se considera válida tras confirmarla con el
  // backend (peek); nunca por el solo hecho de existir en la URL.
  let oauthTokenInvalid = false;
  const oauthNotice = oauthToken
    ? h(
        "div",
        { class: "rounded-lg border border-slate-200 bg-slate-50 p-4" },
        h("p", { class: "text-sm text-slate-600" }, "Verificando tu cuenta de Google..."),
      )
    : null;
  if (oauthToken) {
    auth
      .oauthOnboarding(oauthToken)
      .then((info) => {
        oauthNotice.replaceChildren(googleVerifiedCard(info));
      })
      .catch((error) => {
        oauthTokenInvalid = true;
        submitButton.disabled = true;
        oauthNotice.replaceChildren(
          alert(error.message || "No se pudo validar tu registro con Google."),
          googleAuthButton("register", "Reintentar con Google", { class: "mt-3" }),
        );
      });
  }
  // El correo es la identidad OAuth: no se muestra como campo editable.
  const emailField = oauthToken
    ? null
    : field(
        "Correo electrónico",
        input({ name: "email", type: "email", required: true, autocomplete: "email" }),
      );
  const passwordField = oauthToken
    ? null
    : field(
        "Contraseña",
        passwordInput({ required: true, minlength: 8, autocomplete: "new-password" }),
        "Mínimo 8 caracteres.",
      );
  const googleBlock = oauthToken
    ? null
    : googleAuthButton("register", "Crear cuenta con Google", {
        divider: "after",
        class: "mb-2",
      });
  const form = h(
    "form",
    { class: "space-y-4", novalidate: "true" },
    h("div", { "data-error": "true" }),
    oauthNotice,
    googleBlock,
    field("Nombre completo", input({ name: "full_name", required: true, autocomplete: "name" })),
    emailField,
    h("div", { class: "space-y-1" }, field("Teléfono", phoneInput, phoneHint), phoneError),
    field("Tipo de cuenta", roleSelect),
    h(
      "div",
      { class: "space-y-3" },
      h("p", { class: "flex items-center gap-2 text-sm font-semibold text-slate-700" }, icon("map-pin", { size: 16 }), "Ubicación"),
      location.node,
    ),
    customerAddress,
    modality.node,
    passwordField,
    termsBlock,
    submitButton,
    h(
      "p",
      { class: "text-center text-sm text-slate-500" },
      "¿Ya tienes cuenta? ",
      h("a", { href: routes.login, "data-link": "true", class: "font-medium text-blue-700 hover:underline" }, "Inicia sesión"),
    ),
  );
  syncRoleFields();
  location.ready.finally(() => {
    submitButton.disabled = oauthTokenInvalid;
  });

  form.addEventListener(
    "submit",
    submitHandler(form, async () => {
      if (!termsCheckbox.checked) {
        termsError.classList.remove("hidden");
        termsCheckbox.setAttribute("aria-invalid", "true");
        termsCheckbox.focus();
        throw new Error("Debes aceptar los Términos y Condiciones para crear tu cuenta.");
      }
      const data = Object.fromEntries(new FormData(form).entries());
      try {
        data.phone = normalizePhone(data.phone);
      } catch {
        throw new Error(PHONE_ERROR);
      }
      if (!location.isValid()) {
        throw new Error("Selecciona departamento, provincia y distrito.");
      }
      const payload = {
        full_name: data.full_name,
        phone: data.phone,
        role: data.role,
        accept_terms: true,
        ...location.getValue(),
      };
      if (data.role === "technician") {
        const modalityError = modality.validate();
        if (modalityError) throw new Error(modalityError);
        Object.assign(payload, modality.getPayload());
      } else {
        payload.address = data.address || null;
      }
      let me;
      if (oauthToken) {
        me = await auth.completeOAuth({ ...payload, oauth_token: oauthToken });
      } else {
        await auth.register({ ...payload, email: data.email, password: data.password });
        me = await auth.login(data.email, data.password);
      }
      if (!me || !me.user) {
        throw new Error("Tu cuenta fue creada. Inicia sesión para continuar.");
      }
      onAuthenticated();
      const roles = me.user.roles.map((role) => role.name);
      if (roles.includes("technician")) navigate(routes.profileTechnician);
      else navigate(routes.dashboard);
    }),
  );
  return authShell(
    oauthToken ? "Completa tu registro" : "Crear cuenta",
    oauthToken
      ? "Solo faltan tus datos para activar tu cuenta de Google."
      : "Únete a Pyckle en menos de un minuto.",
    form,
  );
}
