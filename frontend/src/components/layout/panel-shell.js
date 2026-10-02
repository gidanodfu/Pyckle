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
import { Container } from "./container.js";

/**
 * PanelShell: contenedor principal de las páginas autenticadas. Aporta la
 * superficie contenida (borde + radio + fondo) que envuelve el PageHeader, la
 * navegación contextual y el contenido. Se usa igual para cliente, técnico y
 * admin: solo cambia el contenido, no la geometría.
 *
 * @param {{header?:Node, navigation?:Node, class?:string}} options
 * @param  {...Node} content
 */
export function PanelShell({ header, navigation, class: extra = "" } = {}, ...content) {
  return Container(
    h(
      "div",
      { class: `overflow-hidden rounded-xl border border-border bg-surface ${extra}`.trim() },
      header ? h("div", { class: "px-5 pt-5 sm:px-6" }, header) : null,
      navigation ? h("div", { class: "px-5 sm:px-6" }, navigation) : null,
      h("div", { class: "space-y-6 px-5 py-6 sm:px-6" }, ...content),
    ),
  );
}
