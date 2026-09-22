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

export function modal(title, content, onClose) {
  const overlay = h("div", {
    class: "fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4",
    role: "dialog",
    "aria-modal": "true",
    "data-modal": "true",
  });
  const box = h(
    "div",
    { class: "max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white p-6 shadow-xl" },
    h(
      "div",
      { class: "mb-4 flex items-center justify-between gap-3" },
      h("h2", { class: "text-lg font-semibold text-slate-900" }, title),
      button("", { variant: "ghost", class: "!px-2 !py-1 min-w-11", iconName: "x", onClick: () => close(), ariaLabel: "Cerrar" }),
    ),
    content,
  );
  function close() {
    if (!openModals.has(close)) return;
    openModals.delete(close);
    overlay.remove();
    document.removeEventListener("keydown", onKeydown);
    if (onClose) onClose();
  }
  function onKeydown(event) {
    if (event.key === "Escape") close();
  }
  overlay.addEventListener("click", (event) => {
    if (event.target === overlay) close();
  });
  document.addEventListener("keydown", onKeydown);
  overlay.append(box);
  overlay.close = close;
  openModals.add(close);
  return overlay;
}
