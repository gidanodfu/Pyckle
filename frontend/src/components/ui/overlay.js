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
import { button } from "./primitives.js";

const openModals = new Set();

export function closeAllModals() {
  for (const close of [...openModals]) close();
}

const FOCUSABLE =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function modal(title, content, onClose) {
  const previouslyFocused = document.activeElement;
  const overlay = h("div", {
    class: "fixed inset-0 z-50 flex items-center justify-center bg-overlay p-4",
    role: "dialog",
    "aria-modal": "true",
    "data-modal": "true",
  });
  const box = h(
    "div",
    {
      class:
        "max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl border border-border bg-surface-elevated p-6 shadow-floating",
      tabindex: "-1",
    },
    h(
      "div",
      { class: "mb-4 flex items-center justify-between gap-3" },
      h("h2", { class: "text-lg font-semibold text-foreground" }, title),
      button("", {
        variant: "ghost",
        class: "!px-2 !py-1 min-w-11",
        iconName: "x",
        onClick: () => close(),
        ariaLabel: "Cerrar",
      }),
    ),
    content,
  );
  function close() {
    if (!openModals.has(close)) return;
    openModals.delete(close);
    overlay.remove();
    document.removeEventListener("keydown", onKeydown);
    if (previouslyFocused && previouslyFocused.focus) previouslyFocused.focus();
    if (onClose) onClose();
  }
  function onKeydown(event) {
    if (event.key === "Escape") {
      close();
      return;
    }
    if (event.key !== "Tab") return;
    // Focus trap: mantiene el foco dentro del diálogo.
    const items = [...box.querySelectorAll(FOCUSABLE)].filter((el) => el.offsetParent !== null);
    if (!items.length) {
      event.preventDefault();
      box.focus();
      return;
    }
    const first = items[0];
    const last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }
  overlay.addEventListener("click", (event) => {
    if (event.target === overlay) close();
  });
  document.addEventListener("keydown", onKeydown);
  overlay.append(box);
  overlay.close = close;
  openModals.add(close);
  // Mueve el foco al diálogo para lectores de pantalla y teclado.
  queueMicrotask(() => box.focus());
  return overlay;
}
