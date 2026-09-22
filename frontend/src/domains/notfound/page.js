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
import { icon } from "../../components/icons.js";
import { button } from "../../components/ui/index.js";
import { navigate } from "../../lib/navigation.js";
import { routes } from "../../lib/paths.js";

export function NotFound() {
  return h(
    "div",
    { class: "flex flex-col items-center justify-center gap-3 px-4 py-20 text-center" },
    h("span", { class: "flex h-14 w-14 items-center justify-center rounded-full bg-slate-100 text-slate-500" }, icon("search", { size: 26 })),
    h("h1", { class: "text-2xl font-bold text-slate-900" }, "Página no encontrada"),
    h("p", { class: "max-w-md text-sm text-slate-500" }, "La ruta que buscas no existe o fue movida."),
    button("Volver al inicio", { iconName: "home", onClick: () => navigate(routes.home) }),
  );
}
