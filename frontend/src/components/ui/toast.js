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

/**
 * Toasts de feedback para acciones asíncronas (guardados, errores de red).
 *
 * Reglas:
 * - Un único contenedor `aria-live="polite"` montado bajo demanda; los errores
 *   usan `role="alert"` para anunciarse de inmediato.
 * - El color nunca es el único indicador: icono + texto en cada variante.
 * - Se pausa el autodescarte al pasar el ratón o al enfocar, y se puede cerrar
 *   a mano. Los errores de validación de formularios siguen mostrándose junto
 *   al campo; el toast es complementario, no sustituto.
 */

const TYPES = {
  success: { cls: "border-border bg-success-tint text-success", iconName: "check-circle-2", role: "status" },
  error: { cls: "border-border bg-danger-tint text-danger", iconName: "alert-circle", role: "alert" },
  info: { cls: "border-border bg-primary-tint text-primary", iconName: "info", role: "status" },
  warning: { cls: "border-border bg-warning-tint text-warning", iconName: "alert-triangle", role: "status" },
};

let container = null;

function getContainer() {
  if (container && document.body.contains(container)) return container;
  container = h("div", {
    class: "pointer-events-none fixed inset-x-0 bottom-0 z-[60] flex flex-col items-end gap-2 p-4",
    "aria-live": "polite",
    "data-toast-region": "true",
  });
  document.body.append(container);
  return container;
}

export function toast(message, { type = "info", duration = 4000 } = {}) {
  const config = TYPES[type] || TYPES.info;
  let timer = null;

  const close = () => {
    if (timer) window.clearTimeout(timer);
    node.remove();
  };

  const node = h(
    "div",
    {
      class: `pointer-events-auto flex w-[min(22rem,calc(100vw-2rem))] items-start gap-3 rounded-lg border px-4 py-3 text-sm shadow-floating ${config.cls}`,
      role: config.role,
    },
    icon(config.iconName, { size: 18, class: "mt-0.5" }),
    h("span", { class: "flex-1" }, message),
    h(
      "button",
      {
        type: "button",
        class:
          "-mr-1 -mt-1 inline-flex min-h-8 min-w-8 items-center justify-center rounded-md hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-current",
        "aria-label": "Cerrar aviso",
        onClick: close,
      },
      icon("x", { size: 16 }),
    ),
  );

  const schedule = () => {
    if (duration > 0) timer = window.setTimeout(close, duration);
  };
  const pause = () => {
    if (timer) window.clearTimeout(timer);
  };
  node.addEventListener("mouseenter", pause);
  node.addEventListener("focusin", pause);
  node.addEventListener("mouseleave", schedule);

  getContainer().append(node);
  schedule();
  return { close };
}
