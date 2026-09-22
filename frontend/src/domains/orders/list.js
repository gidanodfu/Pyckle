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

import { api } from "../../api/client.js";
import { endpoints } from "../../api/endpoints.js";
import { formatDateTime, formatMoney, h } from "../../components/dom.js";
import { Container } from "../../components/layout/index.js";
import {
  alert,
  badge,
  button,
  card,
  emptyState,
  field,
  input,
  pageHeader,
  select,
  table,
  verifiedBadge,
  withBusy,
} from "../../components/ui/index.js";
import { routes } from "../../lib/paths.js";
import { navigate } from "../../lib/navigation.js";
import { downloadOrderReport } from "./components/report-download.js";

const PAGE_SIZE = 20;

const STATUS_OPTIONS = [
  { value: "", label: "Todos los estados" },
  { value: "awaiting_receipt", label: "Pendiente de recepción" },
  { value: "received", label: "Equipo recibido" },
  { value: "diagnosis", label: "En diagnóstico" },
  { value: "waiting_customer", label: "Esperando al cliente" },
  { value: "waiting_part", label: "Esperando repuesto" },
  { value: "in_repair", label: "En reparación" },
  { value: "testing", label: "En pruebas" },
  { value: "ready", label: "Listo para entrega" },
  { value: "completed", label: "Completada" },
  { value: "cancelled", label: "Cancelada" },
];

const RESULT_OPTIONS = [
  { value: "", label: "Todos los resultados" },
  { value: "repaired", label: "Reparado" },
  { value: "not_repairable", label: "No reparable" },
  { value: "cancelled", label: "Cancelado" },
];

function reportButton(order) {
  if (!order.has_report) {
    return h("span", { class: "text-xs text-slate-500" }, "-");
  }
  return button("Informe", {
    variant: "outline",
    iconName: "file-down",
    onClick: (event) =>
      withBusy(event.currentTarget, async () => {
        try {
          await downloadOrderReport(order);
        } catch (error) {
          window.alert(error.message || "No se pudo descargar el informe");
        }
      }),
  });
}

function orderCard(order, { admin }) {
  return card(
    h(
      "div",
      { class: "flex items-start justify-between gap-3" },
      h(
        "div",
        {},
        h("p", { class: "font-semibold text-slate-800" }, order.request.title),
        h(
          "p",
          { class: "text-xs text-slate-500" },
          `${order.request.specialty_name || "General"} · ${formatDateTime(order.created_at)}`,
        ),
        admin
          ? h(
              "p",
              { class: "mt-1 text-xs text-slate-500" },
              `Cliente: ${order.customer.full_name} · Técnico: ${order.technician.full_name}`,
            )
          : null,
        h(
          "div",
          { class: "mt-2 flex flex-wrap items-center gap-2" },
          badge(order.status),
          order.result ? badge(order.result) : null,
        ),
        h(
          "p",
          { class: "mt-2 text-sm font-semibold text-slate-900" },
          formatMoney(order.final_price),
        ),
      ),
      h(
        "div",
        { class: "flex shrink-0 flex-col items-end gap-2" },
        button("Ver", {
          variant: "outline",
          iconName: "eye",
          onClick: () => navigate(routes.orderDetail(order.id)),
        }),
        admin && order.has_report ? reportButton(order) : null,
      ),
    ),
  );
}

/** Vista de órdenes reutilizable (cliente, técnico y administrador) con filtros. */
export async function ordersView({
  title,
  subtitle,
  defaults = {},
  endpoint = endpoints.orders.list,
  admin = false,
}) {
  const specialties = await api.get(endpoints.specialties.list, { auth: false }).catch(() => []);

  const statusSelect = select("status", STATUS_OPTIONS, { value: defaults.status || "" });
  const resultSelect = select("result", RESULT_OPTIONS, { value: defaults.result || "" });
  const specialtySelect = select(
    "specialty_id",
    [
      { value: "", label: "Todas las categorías" },
      ...specialties.map((item) => ({ value: item.id, label: item.name })),
    ],
    { value: defaults.specialty_id || "" },
  );
  const fromDateInput = input({ name: "from_date", type: "date" });
  const toDateInput = input({ name: "to_date", type: "date" });

  const results = h("div", { class: "mt-6" });
  const filterButton = button("Filtrar", { iconName: "filter" });
  const clearButton = button("Limpiar", { variant: "ghost", iconName: "x" });
  let offset = 0;

  function params() {
    return {
      limit: PAGE_SIZE,
      offset,
      status: statusSelect.value,
      result: resultSelect.value,
      specialty_id: specialtySelect.value,
      from_date: fromDateInput.value,
      to_date: toDateInput.value,
    };
  }

  function pagination(data, reload) {
    const from = data.total === 0 ? 0 : data.offset + 1;
    const to = data.offset + data.items.length;
    return h(
      "div",
      { class: "mt-4 flex flex-wrap items-center justify-between gap-3" },
      h("p", { class: "text-xs text-slate-500" }, `Mostrando ${from}-${to} de ${data.total}`),
      h(
        "div",
        { class: "flex gap-2" },
        button("Anterior", {
          variant: "ghost",
          iconName: "chevron-left",
          disabled: data.offset <= 0,
          onClick: () => reload(Math.max(0, data.offset - PAGE_SIZE)),
        }),
        button("Siguiente", {
          variant: "ghost",
          iconName: "chevron-right",
          disabled: data.offset + data.items.length >= data.total,
          onClick: () => reload(data.offset + PAGE_SIZE),
        }),
      ),
    );
  }

  async function load(nextOffset = 0) {
    offset = nextOffset;
    await withBusy(filterButton, async () => {
      let data;
      try {
        data = await api.get(endpoint(params()));
      } catch (error) {
        results.replaceChildren(alert(error.message || "No se pudieron cargar las órdenes"));
        return;
      }
      if (!data.items.length) {
        results.replaceChildren(
          emptyState(
            "Sin reparaciones",
            "Cuando se acepte una cotización aparecerá aquí.",
            null,
            { iconName: "receipt-text" },
          ),
        );
        return;
      }
      const columns = admin
        ? [
            "Orden",
            "Solicitud",
            "Cliente",
            "Técnico",
            { label: "Estado", align: "center" },
            { label: "Resultado", align: "center" },
            { label: "Final", align: "right" },
            "Fecha",
            { label: "", align: "right" },
          ]
        : [
            "Orden",
            "Solicitud",
            { label: "Estado", align: "center" },
            { label: "Resultado", align: "center" },
            { label: "Final", align: "right" },
            "Fecha",
            { label: "", align: "right" },
          ];
      const rowFor = (order) => {
        const base = [
          h("span", { class: "font-mono text-xs text-slate-500" }, order.id.slice(0, 8)),
          h(
            "span",
            {},
            h("span", { class: "block font-medium text-slate-800" }, order.request.title),
            h(
              "span",
              { class: "text-xs text-slate-500" },
              order.request.specialty_name || "General",
            ),
          ),
        ];
        if (admin) {
          base.push(
            h("span", { class: "text-sm text-slate-700" }, order.customer.full_name),
            h(
              "span",
              { class: "inline-flex items-center gap-1.5 text-sm text-slate-700" },
              order.technician.full_name,
              verifiedBadge(order.technician.is_verified),
            ),
          );
        }
        base.push(
          badge(order.status),
          order.result ? badge(order.result) : h("span", { class: "text-xs text-slate-500" }, "-"),
          formatMoney(order.final_price),
          formatDateTime(order.created_at),
          h(
            "span",
            { class: "inline-flex items-center gap-2" },
            admin ? reportButton(order) : null,
            button("Ver", {
              variant: "outline",
              iconName: "eye",
              onClick: () => navigate(routes.orderDetail(order.id)),
            }),
          ),
        );
        return base;
      };

      results.replaceChildren(
        h(
          "div",
          {},
          // Móvil: tarjetas apiladas. Escritorio: tabla.
          h("div", { class: "space-y-3 md:hidden" }, data.items.map((order) => orderCard(order, { admin }))),
          h("div", { class: "hidden md:block" }, table(columns, data.items.map(rowFor))),
          pagination(data, load),
        ),
      );
    });
  }

  clearButton.addEventListener("click", () => {
    statusSelect.value = "";
    resultSelect.value = "";
    specialtySelect.value = "";
    fromDateInput.value = "";
    toDateInput.value = "";
    load(0);
  });
  filterButton.addEventListener("click", () => load(0));

  const view = Container(
    pageHeader(title, subtitle),
    card(
      h(
        "div",
        { class: "grid gap-4 md:grid-cols-[1fr_1fr_1fr_1fr_1fr_auto]" },
        field("Categoría", specialtySelect),
        field("Estado", statusSelect),
        field("Resultado", resultSelect),
        field("Desde", fromDateInput),
        field("Hasta", toDateInput),
        h("div", { class: "flex items-end gap-2" }, filterButton, clearButton),
      ),
    ),
  );

  await load(0);
  view.append(results);
  return view;
}

export async function OrdersList() {
  return ordersView({
    title: "Órdenes",
    subtitle: "Seguimiento de tus reparaciones aceptadas.",
  });
}
