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
import { alert, button, field, input, passwordInput } from "../../components/ui/index.js";
import { routes } from "../../lib/paths.js";
import { onAuthenticated } from "../../app/session.js";
import { navigate } from "../../lib/navigation.js";
import { panelPath } from "../../lib/panel.js";
import { auth, oauthErrorMessage } from "../../services/auth.js";
import { googleAuthButton } from "./google-button.js";
import { authShell, submitHandler } from "./shell.js";

export function Login() {
  const form = h(
    "form",
    { class: "space-y-4", novalidate: "true" },
    h("div", { "data-error": "true" }),
    field(
      "Correo electrónico",
      input({ name: "email", type: "email", required: true, placeholder: "tu@correo.com", autocomplete: "email" }),
    ),
    field("Contraseña", passwordInput({ autocomplete: "current-password" })),
    button("Ingresar", { type: "submit", class: "w-full", iconName: "log-in" }),
    googleAuthButton("login", "Continuar con Google"),
    h(
      "p",
      { class: "text-center text-sm text-slate-500" },
      "¿No tienes cuenta? ",
      h("a", { href: routes.register, "data-link": "true", class: "font-medium text-blue-700 hover:underline" }, "Regístrate"),
    ),
  );
  // Error devuelto por el callback OAuth (solo un código no sensible).
  const oauthError = new URLSearchParams(window.location.search).get("oauth_error");
  if (oauthError) {
    form.querySelector("[data-error]").replaceChildren(alert(oauthErrorMessage(oauthError)));
    window.history.replaceState({}, "", routes.login);
  }
  form.addEventListener(
    "submit",
    submitHandler(form, async () => {
      const data = new FormData(form);
      const me = await auth.login(data.get("email"), data.get("password"));
      if (!me || !me.user) {
        throw new Error("No se pudo cargar tu perfil. Intenta iniciar sesión nuevamente.");
      }
      onAuthenticated();
      navigate(panelPath(me));
    }),
  );
  return authShell("Iniciar sesión", "Accede para gestionar tus solicitudes y órdenes.", form);
}
