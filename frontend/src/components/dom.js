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

export function h(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value == null || value === false) continue;
    if (key === "class") node.className = value;
    else if (key === "dataset") Object.assign(node.dataset, value);
    else if (key === "html") node.innerHTML = value;
    else if (key.startsWith("on") && typeof value === "function") {
      node.addEventListener(key.slice(2).toLowerCase(), value);
    } else if (key in node && key !== "list" && key !== "form") {
      node[key] = value;
    } else {
      node.setAttribute(key, value);
    }
  }
  append(node, children);
  return node;
}

/**
 * Normaliza una colección de clases a tokens individuales.
 * Acepta string, array o anidados; separa por espacios y descarta vacíos.
 */
function toClassTokens(classes) {
  return (Array.isArray(classes) ? classes : [classes])
    .flat(Infinity)
    .flatMap((item) => String(item ?? "").trim().split(/\s+/))
    .filter(Boolean);
}

/**
 * Alterna varias clases sobre un elemento.
 *
 * `classList.toggle/add/remove` operan con UN token; una cadena con espacios
 * produce DOMException. Para colecciones usa siempre este helper, que aplica
 * cada clase como token independiente.
 */
export function toggleClasses(node, classes, force) {
  for (const token of toClassTokens(classes)) node.classList.toggle(token, force);
  return node;
}

export function append(node, children) {
  for (const child of children.flat(Infinity)) {
    if (child == null || child === false || child === "") continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
}

export function clear(node) {
  node.replaceChildren();
  return node;
}

export function on(node, event, handler) {
  node.addEventListener(event, handler);
  return node;
}

const STATUS_LABELS = {
  open: "Abierta",
  quoted: "Cotizada",
  accepted: "Aceptada",
  in_progress: "En progreso",
  completed: "Completada",
  cancelled: "Cancelada",
  pending: "Pendiente",
  rejected: "Rechazada",
  withdrawn: "Retirada",
  home: "A domicilio",
  workshop: "En taller",
  archived: "Archivada",
  closed: "Cerrada",
  // Estado técnico de la reparación
  awaiting_receipt: "Pendiente de recepción",
  received: "Equipo recibido",
  diagnosis: "En diagnóstico",
  waiting_customer: "Esperando al cliente",
  waiting_part: "Esperando repuesto",
  in_repair: "En reparación",
  testing: "En pruebas",
  ready: "Listo para entrega",
  // Resultado
  repaired: "Reparado",
  not_repairable: "No reparable",
  // Eventos
  status_changed: "Estado actualizado",
  diagnosis_started: "Diagnóstico iniciado",
  diagnosis_completed: "Diagnóstico completado",
  part_requested: "Repuesto solicitado",
  repair_started: "Reparación iniciada",
  testing_started: "Pruebas iniciadas",
  price_change_proposed: "Nuevo costo propuesto",
  price_change_approved: "Cambio de precio aprobado",
  price_change_rejected: "Cambio de precio rechazado",
  report_generated: "Informe generado",
  approved: "Aprobado",
  note: "Nota del técnico",
  repair_received: "Equipo recibido",
  repair_in_progress: "Reparación en curso",
  repair_ready: "Reparación lista",
  repair_completed: "Reparación completada",
  repair_not_repairable: "Reparación no reparable",
  repair_cancelled: "Reparación cancelada",
  price_change_requested: "Aprobación de nuevo costo",
  report_available: "Informe disponible",
  // Costos
  part: "Repuestos",
  labor: "Servicio técnico",
  other: "Otros",
  // Notificaciones
  quotation_created: "Cotización recibida",
  quotation_accepted: "Cotización aceptada",
  order_status_changed: "Orden actualizada",
  message_new: "Mensaje nuevo",
  review_created: "Reseña recibida",
  system: "Sistema",
};

export function statusLabel(value) {
  return STATUS_LABELS[value] || value;
}

export function formatMoney(value) {
  const number = Number(value ?? 0);
  return `S/ ${number.toFixed(2)}`;
}

export function formatDate(value) {
  if (!value) return "-";
  return new Date(value).toLocaleDateString("es-PE", { day: "2-digit", month: "short", year: "numeric" });
}

export function formatDateTime(value) {
  if (!value) return "-";
  return new Date(value).toLocaleString("es-PE", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
