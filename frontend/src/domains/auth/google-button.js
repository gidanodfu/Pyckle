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
import { googleIcon } from "../../components/google-icon.js";
import { button } from "../../components/ui/index.js";
import { auth } from "../../services/auth.js";

/**
 * Botón que inicia OAuth con Google navegando al endpoint backend.
 * Solo se muestra si el backend confirma que el proveedor está habilitado.
 * `divider` permite colocarlo arriba del formulario ("after") o debajo
 * ("before", por defecto) sin duplicar el botón ni el divisor.
 */
export function googleAuthButton(
  intent = "login",
  label = "Continuar con Google",
  { divider = "before", class: extra = "mt-4" } = {},
) {
  const container = h("div", { class: extra });
  auth.googleProviders().then((providers) => {
    if (!providers.google) return;
    const dividerNode = h(
      "div",
      { class: "my-4 flex items-center gap-3" },
      h("span", { class: "h-px flex-1 bg-slate-200" }),
      h("span", { class: "text-xs uppercase tracking-wide text-slate-500" }, "o"),
      h("span", { class: "h-px flex-1 bg-slate-200" }),
    );
    const googleButton = button(label, {
      variant: "neutral",
      iconNode: googleIcon({ size: 18 }),
      class: "w-full",
      onClick: () => auth.startGoogle(intent),
    });
    container.append(...(divider === "after" ? [googleButton, dividerNode] : [dividerNode, googleButton]));
  });
  return container;
}
