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

import { getTokens } from "../api/client.js";
import { createFooter } from "../components/footer.js";
import { h } from "../components/dom.js";
import { createNavbarController } from "../components/layout/index.js";
import { spinner } from "../components/ui/index.js";
import { routes } from "../lib/paths.js";
import { navigate } from "../lib/navigation.js";
import { initTheme } from "../lib/theme.js";
import { auth } from "../services/auth.js";
import { isAuthenticated, store } from "../state/store.js";
import { closeRealtime, onAuthenticated } from "./session.js";
import { render, setShell } from "./router.js";

function mountShell() {
  const root = document.getElementById("app");
  const navbar = createNavbarController();
  const outlet = h("main", { id: "view" });
  const footer = createFooter();
  root.replaceChildren(navbar.node, outlet, footer);
  setShell({ navbar, outlet });
  return { navbar, outlet };
}

function registerGlobalListeners() {
  document.addEventListener("click", (event) => {
    const anchor = event.target.closest("a[data-link]");
    if (!anchor) return;
    event.preventDefault();
    navigate(anchor.getAttribute("href"));
  });
  window.addEventListener("popstate", () => render());
  window.addEventListener("auth:expired", () => {
    closeRealtime();
    store.reset();
    navigate(routes.login);
  });
  window.addEventListener("auth:logout", () => closeRealtime());
}

export async function boot() {
  initTheme();
  const { outlet } = mountShell();
  outlet.replaceChildren(spinner());
  registerGlobalListeners();
  const { access } = getTokens();
  if (access) await auth.loadMe();
  if (isAuthenticated()) onAuthenticated();
  await render();
}
