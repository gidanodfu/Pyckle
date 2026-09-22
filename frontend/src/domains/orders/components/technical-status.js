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

import { h, statusLabel } from "../../../components/dom.js";
import { icon } from "../../../components/icons.js";

/** Secuencia principal del proceso técnico. */
export const REPAIR_PIPELINE = [
  "awaiting_receipt",
  "received",
  "diagnosis",
  "in_repair",
  "testing",
  "ready",
  "completed",
];

/**
 * Transiciones no terminales que la UI ofrece al técnico.
 * El backend sigue siendo la autoridad; esto solo refleja la máquina de estados.
 */
export const NEXT_TRANSITIONS = {
  awaiting_receipt: [
    { value: "received", label: "Marcar equipo recibido", iconName: "package" },
  ],
  received: [{ value: "diagnosis", label: "Iniciar diagnóstico", iconName: "scan-search" }],
  diagnosis: [
    { value: "in_repair", label: "Iniciar reparación", iconName: "wrench" },
    { value: "waiting_part", label: "Esperando repuesto", iconName: "package" },
  ],
  waiting_customer: [
    { value: "in_repair", label: "Reanudar reparación", iconName: "wrench" },
    { value: "diagnosis", label: "Volver a diagnóstico", iconName: "scan-search" },
  ],
  waiting_part: [
    { value: "in_repair", label: "Reanudar reparación", iconName: "wrench" },
    { value: "waiting_customer", label: "Esperando al cliente", iconName: "clock" },
  ],
  in_repair: [
    { value: "testing", label: "Iniciar pruebas", iconName: "clipboard-check" },
    { value: "waiting_part", label: "Esperando repuesto", iconName: "package" },
  ],
  testing: [{ value: "ready", label: "Marcar listo", iconName: "check" }],
  ready: [{ value: "testing", label: "Volver a pruebas", iconName: "clipboard-check" }],
};

export function technicalStatusStepper(status) {
  const currentIndex = REPAIR_PIPELINE.indexOf(status);
  const cancelled = status === "cancelled";
  return h(
    "div",
    { class: "flex flex-wrap gap-2" },
    REPAIR_PIPELINE.map((step, index) => {
      const active = status === step;
      const done = !cancelled && currentIndex > index;
      const reached = active || done;
      // El estado final usa check (como los pasos ya superados); el resto, reloj.
      const activeIcon = step === "completed" ? "check" : "clock";
      return h(
        "span",
        {
          class: `inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${
            active
              ? "bg-blue-700 text-white"
              : done
                ? "bg-emerald-50 text-emerald-700"
                : "bg-slate-100 text-slate-500"
          }`,
        },
        icon(active ? activeIcon : done ? "check" : "clock", { size: 12 }),
        statusLabel(step),
      );
    }),
  );
}
