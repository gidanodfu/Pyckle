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

import { onAuthenticated } from "../../app/session.js";
import { Container } from "../../components/layout/index.js";
import { alert, spinner } from "../../components/ui/index.js";
import { navigate } from "../../lib/navigation.js";
import { panelPath } from "../../lib/panel.js";
import { routes } from "../../lib/paths.js";
import { auth } from "../../services/auth.js";

/**
 * Página a la que el backend redirige tras el callback OAuth con un código de
 * intercambio de un solo uso. El frontend lo canjea por la sesión normal.
 */
export async function OAuthCallback() {
  const container = Container(spinner("Completando inicio de sesión..."));
  const code = new URLSearchParams(window.location.search).get("code");
  if (!code) {
    container.replaceChildren(
      alert("No se pudo completar el inicio de sesión con Google."),
    );
    window.setTimeout(() => navigate(routes.login), 1500);
    return container;
  }
  try {
    const me = await auth.exchangeOAuth(code);
    if (!me || !me.user) throw new Error("No se pudo cargar tu perfil.");
    onAuthenticated();
    navigate(panelPath(me));
  } catch (error) {
    container.replaceChildren(
      alert(error.message || "No se pudo completar el inicio de sesión con Google."),
    );
    window.setTimeout(() => navigate(routes.login), 2000);
  }
  return container;
}
