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

import { Logo } from "../brand.js";
import { h } from "../dom.js";
import { icon } from "../icons.js";
import { button } from "../ui/index.js";
import { routes } from "../../lib/paths.js";
import { navigate } from "../../lib/navigation.js";
import { store } from "../../state/store.js";
import { notificationBell } from "./notification-bell.js";
import { themeToggle } from "./theme-toggle.js";
import { userMenu } from "./user-menu.js";

const FOCUS_RING =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2";

function navLink(label, path, current, iconName) {
  const active = current === path || (path !== "/" && current.startsWith(path));
  return h(
    "a",
    {
      href: path,
      "data-link": "true",
      class: `inline-flex min-h-11 items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium transition ${FOCUS_RING} ${
        active ? "bg-blue-50 text-blue-800" : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
      }`,
    },
    iconName ? icon(iconName, { size: 16 }) : null,
    label,
  );
}

function navLinksFor(me, current) {
  if (!me) {
    return [
      navLink("Inicio", routes.home, current, "home"),
      navLink("Técnicos", routes.technicians, current, "wrench"),
    ];
  }
  const roles = me.user.roles.map((role) => role.name);
  const isAdmin = roles.includes("admin");
  const links = [];
  if (roles.includes("customer")) {
    links.push(
      navLink("Mi panel", routes.dashboard, current, "layout-dashboard"),
      navLink("Mis solicitudes", routes.requests, current, "clipboard-list"),
    );
  }
  if (roles.includes("technician")) {
    links.push(
      navLink("Panel técnico", routes.technicianDashboard, current, "wrench"),
      navLink("Solicitudes", routes.requests, current, "clipboard-list"),
    );
  }
  if (isAdmin) {
    // El administrador supervisa órdenes en solo lectura y no usa el chat.
    links.push(navLink("Administración", routes.admin, current, "settings"));
    if (me.permissions.includes("admin:orders")) {
      links.push(navLink("Órdenes", routes.adminOrders, current, "receipt-text"));
    }
  } else {
    links.push(
      navLink("Chat", routes.chat, current, "message-square"),
      navLink("Órdenes", routes.orders, current, "receipt-text"),
    );
  }
  return links;
}

/**
 * Navbar persistente. Se monta una sola vez y se actualiza en su lugar:
 * - `setActive(path)`: recalcula el estado activo de los enlaces.
 * - `update()`: sincroniza usuario (login/logout) y campana de notificaciones.
 * No vuelve a registrar listeners ni suscripciones en cada navegación.
 *
 * En móvil los enlaces se pliegan tras un botón de menú; en escritorio se
 * mantiene la fila horizontal actual.
 */
export function createNavbarController() {
  const linksBox = h("nav", {
    class:
      "hidden w-full flex-col gap-1 md:flex md:w-auto md:min-w-0 md:flex-1 md:flex-row md:flex-wrap md:items-center",
    id: "main-nav",
  });
  const rightBox = h("div", { class: "ml-auto flex shrink-0 items-center gap-1" });
  const menuButton = button("", {
    variant: "ghost",
    class: `!px-2 !py-2 min-h-11 min-w-11 md:hidden`,
    iconName: "menu",
    ariaLabel: "Abrir menú",
  });
  menuButton.setAttribute("aria-expanded", "false");
  menuButton.setAttribute("aria-controls", "main-nav");
  const node = h(
    "header",
    { class: "sticky top-0 z-40 border-b border-slate-200 bg-white/95 backdrop-blur" },
    h(
      "div",
      { class: "mx-auto flex max-w-6xl flex-wrap items-center gap-2 px-4 py-3" },
      h("span", { class: "mr-2 shrink-0" }, Logo({ size: 34 })),
      menuButton,
      linksBox,
      rightBox,
    ),
  );

  let userSignature;
  let currentPath = window.location.pathname;
  let bell = null;

  function closeMenu() {
    linksBox.classList.add("hidden");
    menuButton.setAttribute("aria-expanded", "false");
  }

  menuButton.addEventListener("click", () => {
    const open = linksBox.classList.toggle("hidden") === false;
    menuButton.setAttribute("aria-expanded", open ? "true" : "false");
  });

  function renderRight(me) {
    rightBox.replaceChildren();
    bell = null;
    const theme = themeToggle();
    if (!me) {
      rightBox.append(
        theme,
        button("Iniciar sesión", { variant: "ghost", onClick: () => navigate(routes.login) }),
        button("Crear cuenta", { iconName: "user", onClick: () => navigate(routes.register) }),
      );
      return;
    }
    bell = notificationBell();
    rightBox.append(theme, bell.node, userMenu(me));
  }

  function syncUser(me) {
    const signature = me
      ? `${me.user.id}:${me.user.roles.map((role) => role.name).sort().join(",")}`
      : null;
    if (signature === userSignature) return;
    userSignature = signature;
    linksBox.replaceChildren(...navLinksFor(me, currentPath));
    renderRight(me);
  }

  function setActive(path) {
    currentPath = path;
    closeMenu();
    linksBox.replaceChildren(...navLinksFor(store.get().me, path));
  }

  function update() {
    syncUser(store.get().me);
    if (bell) bell.update();
  }

  const unsubscribe = store.subscribe(update);
  update();

  return { node, setActive, update, destroy: unsubscribe };
}
