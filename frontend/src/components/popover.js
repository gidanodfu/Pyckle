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

/**
 * Gestor centralizado de popovers (notificaciones, menú de usuario).
 *
 * Reglas:
 * - Solo puede haber un popover abierto a la vez.
 * - Un único listener a nivel de documento cierra el popover abierto cuando el
 *   clic ocurre fuera de su wrapper. Los clics dentro del wrapper (trigger o
 *   panel) no lo cierran, por lo que no se necesita `stopPropagation`.
 * - Escape cierra cualquier popover abierto.
 */

const openPopovers = new Set();

function closeEntry(entry) {
  if (!openPopovers.has(entry)) return;
  openPopovers.delete(entry);
  entry.panel.classList.add("hidden");
  entry.trigger.setAttribute("aria-expanded", "false");
}

export function closeAllPopovers() {
  for (const entry of [...openPopovers]) closeEntry(entry);
}

export function createPopover({ trigger, panel, wrapper }) {
  const entry = { trigger, panel, wrapper };
  trigger.setAttribute("aria-haspopup", "true");
  trigger.setAttribute("aria-expanded", "false");
  panel.classList.add("hidden");

  trigger.addEventListener("click", (event) => {
    event.preventDefault();
    if (openPopovers.has(entry)) {
      closeEntry(entry);
      return;
    }
    closeAllPopovers();
    openPopovers.add(entry);
    panel.classList.remove("hidden");
    trigger.setAttribute("aria-expanded", "true");
  });

  return {
    close: () => closeEntry(entry),
    isOpen: () => openPopovers.has(entry),
  };
}

document.addEventListener(
  "click",
  (event) => {
    for (const entry of [...openPopovers]) {
      if (!entry.wrapper.contains(event.target)) closeEntry(entry);
    }
  },
  true,
);

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeAllPopovers();
});
