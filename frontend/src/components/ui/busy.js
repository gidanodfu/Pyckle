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
 * Ejecuta una acción asíncrona bloqueando el botón mientras está en curso.
 * Evita que un doble clic dispare la misma operación dos veces.
 */
export async function withBusy(buttonNode, action) {
  if (!buttonNode) return action();
  if (buttonNode.dataset.busy === "1") return undefined;
  buttonNode.dataset.busy = "1";
  buttonNode.setAttribute("aria-busy", "true");
  const wasDisabled = buttonNode.disabled;
  buttonNode.disabled = true;
  try {
    return await action();
  } finally {
    // Restaurar siempre: el botón puede ejecutarse antes de estar conectado
    // al DOM (cargas iniciales). Restaurar un nodo desconectado es inofensivo.
    buttonNode.dataset.busy = "0";
    buttonNode.removeAttribute("aria-busy");
    buttonNode.disabled = wasDisabled;
  }
}
