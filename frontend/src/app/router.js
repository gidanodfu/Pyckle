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

import { h } from "../components/dom.js";
import { closeAllPopovers } from "../components/popover.js";
import { alert, closeAllModals, spinner } from "../components/ui/index.js";
import { teardownChat } from "../domains/chat/page.js";
import { NotFound } from "../domains/notfound/page.js";
import { routes } from "../lib/paths.js";
import { setNavigator } from "../lib/navigation.js";
import { panelPath } from "../lib/panel.js";
import { hasPermission, hasRole, isAuthenticated, store } from "../state/store.js";
import { appRoutes } from "./routes.js";

const APP_NAME = "Pyckle";

let shell = null;
/**
 * Versión de navegación. Cada render captura la suya; solo el render vigente
 * puede escribir en el outlet, por lo que una respuesta async antigua nunca
 * sobrescribe una navegación posterior.
 */
let renderVersion = 0;

export function setShell(nextShell) {
  shell = nextShell;
}

function resolve(pathname) {
  for (const route of appRoutes) {
    const patternParts = route.path.split("/").filter(Boolean);
    const pathParts = pathname.split("/").filter(Boolean);
    if (patternParts.length !== pathParts.length) continue;
    const params = {};
    let matched = true;
    for (let index = 0; index < patternParts.length; index += 1) {
      const pattern = patternParts[index];
      if (pattern.startsWith(":")) {
        try {
          const value = decodeURIComponent(pathParts[index]);
          // Un id no puede contener separadores ni navegación relativa: evita
          // que un path crafted re-apunte endpoints (p. ej. ..%2Fadmin%2Fusers).
          if (value === "." || value === ".." || /[/\\]/.test(value)) return null;
          params[pattern.slice(1)] = value;
        } catch {
          // URL malformada (percent-encoding inválido): no bloquea el render.
          return null;
        }
      } else if (pattern !== pathParts[index]) {
        matched = false;
        break;
      }
    }
    if (matched) return { route, params };
  }
  return null;
}

function pageTitle(match) {
  if (!match) return `No encontrada | ${APP_NAME}`;
  return `${match.route.title || APP_NAME} | ${APP_NAME}`;
}

function centered(content) {
  return h("div", { class: "mx-auto max-w-3xl px-4 py-10" }, content);
}

export function navigate(path, { replace = false } = {}) {
  if (replace) window.history.replaceState({}, "", path);
  else window.history.pushState({}, "", path);
  render();
  window.scrollTo({ top: 0 });
}

export async function render() {
  const version = ++renderVersion;
  const { navbar, outlet } = shell;
  const match = resolve(window.location.pathname);
  document.title = pageTitle(match);
  navbar.setActive(window.location.pathname);
  closeAllPopovers();
  closeAllModals();
  if (window.location.pathname !== routes.chat) teardownChat();

  const commit = (content) => {
    if (version !== renderVersion) return false;
    outlet.replaceChildren(content);
    return true;
  };

  if (!match) {
    commit(NotFound());
    return;
  }

  const { route, params } = match;
  if (route.auth && !isAuthenticated()) {
    navigate(routes.login, { replace: true });
    return;
  }
  if (route.guest && isAuthenticated()) {
    navigate(panelPath(store.get().me), { replace: true });
    return;
  }
  if (route.permission && !hasPermission(route.permission)) {
    commit(centered(alert("No tienes permisos para ver esta sección.", "error")));
    return;
  }
  if (route.deniedRoles && route.deniedRoles.some((role) => hasRole(role))) {
    commit(centered(alert("No tienes acceso a esta sección.", "error")));
    return;
  }

  commit(spinner());
  let content;
  try {
    content = await route.page(params);
  } catch (error) {
    if (version === renderVersion) {
      outlet.replaceChildren(centered(alert(error.message || "Ocurrió un error")));
    }
    return;
  }
  if (version !== renderVersion) return;
  outlet.replaceChildren(content);
}

setNavigator(navigate);
