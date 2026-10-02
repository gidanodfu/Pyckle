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

import { h } from "../dom.js";
import { icon } from "../icons.js";
import { createPopover } from "../popover.js";
import { withBusy } from "../ui/index.js";
import { routes } from "../../lib/paths.js";
import { navigate } from "../../lib/navigation.js";
import { auth } from "../../services/auth.js";

function menuLink(label, path, iconName) {
  return h(
    "button",
    {
      class:
        "flex min-h-11 w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm text-foreground-secondary hover:bg-surface-hover hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background",
      onClick: () => navigate(path),
    },
    icon(iconName, { size: 16 }),
    label,
  );
}

export function userMenu(me) {
  const roles = me.user.roles.map((role) => role.name);
  const panel = h(
    "div",
    {
      "data-user-menu": "true",
      class:
        "absolute right-0 mt-2 hidden w-52 rounded-lg border border-border bg-surface-elevated p-1.5 shadow-floating",
    },
    roles.includes("customer") ? menuLink("Mi perfil", routes.profileCustomer, "user") : null,
    roles.includes("technician")
      ? menuLink("Perfil profesional", routes.profileTechnician, "wrench")
      : null,
    h("div", { class: "my-1 border-t border-border-subtle" }),
    h(
      "button",
      {
        class:
          "flex min-h-11 w-full items-center gap-2 rounded-md px-3 py-2 text-left text-sm text-danger hover:bg-danger-tint focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background",
        onClick: (event) =>
          withBusy(event.currentTarget, async () => {
            await auth.logout();
            navigate(routes.home);
          }),
      },
      icon("log-out", { size: 16 }),
      `Cerrar sesión (${me.user.full_name.split(" ")[0]})`,
    ),
  );
  const trigger = h(
    "button",
    {
      class:
        "inline-flex min-h-11 items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium text-foreground-secondary hover:bg-surface-hover hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background",
      "aria-label": "Menú de usuario",
    },
    icon("user", { size: 17 }),
    icon("chevron-down", { size: 14 }),
  );
  const wrapper = h("div", { class: "relative" }, trigger, panel);
  createPopover({ trigger, panel, wrapper });
  return wrapper;
}
