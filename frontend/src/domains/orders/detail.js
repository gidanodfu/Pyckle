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
import { formatDateTime, formatMoney, h, statusLabel } from "../../components/dom.js";
import { icon } from "../../components/icons.js";
import { Container } from "../../components/layout/index.js";
import {
  badge,
  button,
  card,
  pageHeader,
  verifiedBadge,
  withBusy,
} from "../../components/ui/index.js";
import { routes } from "../../lib/paths.js";
import { navigate } from "../../lib/navigation.js";
import { hasPermission, store } from "../../state/store.js";
import { closeActionsCard } from "./components/closure-actions.js";
import { costsCard } from "./components/costs.js";
import { customerProfileModal } from "./components/customer-profile-modal.js";
import { detailsCard } from "./components/repair-details-card.js";
import { managementPanel } from "./components/management-panel.js";
import { priceChangesCard } from "./components/price-changes.js";
import { downloadOrderReport } from "./components/report-download.js";
import { reviewForm } from "./components/review-form.js";
import { technicalStatusStepper } from "./components/technical-status.js";
import { orderTimeline } from "./components/timeline.js";

const TERMINAL = ["completed", "cancelled"];

export async function OrderDetail({ id }) {
  const order = await api.get(endpoints.orders.byId(id));
  const me = store.get().me;
  const isAssigned = Boolean(me.technician_id && me.technician_id === order.technician.id);
  const isAdmin = hasPermission("order:read_all") || hasPermission("admin:orders");
  const isCustomer = order.customer.id === me.user.id;
  // El administrador supervisa en solo lectura: nunca gestiona ni actúa.
  const canManage = isAssigned;
  const canAct = canManage && !TERMINAL.includes(order.status);
  const reload = () => navigate(routes.orderDetail(id));

  // El administrador no usa el chat: ni siquiera se consulta la conversación.
  const conversation = isAdmin
    ? null
    : await api
        .get(endpoints.conversations.list({ request_id: order.request_id }))
        .then((items) => items.find((item) => item.order_id === id))
        .catch(() => null);

  const actions = h("div", { class: "flex flex-wrap gap-2" });
  if (conversation) {
    actions.append(
      button("Abrir chat", {
        variant: "outline",
        iconName: "message-square",
        onClick: () => navigate(routes.chatWith(conversation.id)),
      }),
    );
  }
  actions.append(
    button("Ver solicitud", {
      variant: "ghost",
      iconName: "clipboard-list",
      onClick: () => navigate(routes.requestDetail(order.request_id)),
    }),
  );
  if (canManage || isAdmin) {
    actions.append(
      button("Perfil del cliente", {
        variant: "outline",
        iconName: "user",
        onClick: (event) =>
          withBusy(event.currentTarget, async () => {
            try {
              const profile = await api.get(endpoints.orders.customerProfile(id));
              // Evita añadir el modal si el usuario navegó durante el await.
              if (window.location.pathname === routes.orderDetail(id)) {
                document.body.append(customerProfileModal(profile));
              }
            } catch (error) {
              window.alert(error.message || "No se pudo cargar el perfil del cliente");
            }
          }),
      }),
    );
  }
  if (order.report) {
    actions.append(
      button("Descargar informe", {
        variant: "success",
        iconName: "file-down",
        onClick: (event) =>
          withBusy(event.currentTarget, async () => {
            try {
              await downloadOrderReport(order);
            } catch (error) {
              window.alert(error.message || "No se pudo descargar el informe");
            }
          }),
      }),
    );
  }

  const location =
    [order.request.district_name, order.request.province_name, order.request.department_name]
      .filter(Boolean)
      .join(", ") || "-";

  const summary = card(
    h(
      "div",
      { class: "flex flex-wrap items-center justify-between gap-2" },
      h("h3", { class: "text-lg font-semibold text-slate-900" }, "Resumen"),
      h(
        "div",
        { class: "flex flex-wrap items-center gap-2" },
        badge(order.status),
        order.result ? badge(order.result) : null,
      ),
    ),
    h("div", { class: "mt-4" }, technicalStatusStepper(order.status)),
    h(
      "dl",
      { class: "mt-4 grid gap-3 text-sm sm:grid-cols-2" },
      item("Cliente", order.customer.full_name),
      item(
        "Técnico",
        h(
          "span",
          { class: "inline-flex items-center gap-1.5" },
          order.technician.full_name,
          verifiedBadge(order.technician.is_verified),
        ),
      ),
      item("Solicitud", order.request.title),
      item("Categoría", order.request.specialty_name || "General"),
      item("Modalidad", statusLabel(order.request.modality)),
      item("Ubicación", location),
      item("Precio final", formatMoney(order.final_price)),
      item("Recibido", order.received_at ? formatDateTime(order.received_at) : "-"),
      item("Completado", order.completed_at ? formatDateTime(order.completed_at) : "-"),
    ),
    order.service_address
      ? h(
          "p",
          {
            class: "mt-4 inline-flex items-center gap-2 rounded-lg bg-blue-50 px-3 py-2 text-sm text-blue-900",
          },
          icon("map-pin", { size: 15 }),
          order.service_address,
        )
      : null,
  );

  const timelineCard = card(
    h("h3", { class: "mb-4 text-lg font-semibold text-slate-900" }, "Seguimiento"),
    orderTimeline(order.events),
  );

  const reportCard = order.report
    ? card(
        h(
          "h3",
          { class: "mb-2 flex items-center gap-2 text-lg font-semibold text-slate-900" },
          icon("file-text", { size: 18 }),
          "Informe de reparación",
        ),
        h(
          "p",
          { class: "text-sm text-slate-600" },
          `Versión ${order.report.version} · ${formatDateTime(order.report.generated_at)}`,
        ),
        h(
          "ul",
          { class: "mt-3 space-y-2" },
          order.diagnosis ? detailRow("Diagnóstico", order.diagnosis) : null,
          order.work_performed ? detailRow("Trabajo realizado", order.work_performed) : null,
          order.tests_performed ? detailRow("Pruebas", order.tests_performed) : null,
        ),
      )
    : null;

  const reviewCard =
    isCustomer && order.status === "completed" && !order.has_review ? reviewForm(id) : null;
  const reviewShown =
    isCustomer && order.has_review
      ? card(h("p", { class: "text-sm text-emerald-700" }, "Gracias por calificar este servicio."))
      : null;

  const columns = [summary, timelineCard];
  if (canAct) {
    columns.unshift(managementPanel(order, reload));
    columns.push(detailsCard(order, { canManage: true, onChanged: reload }));
  } else if (isAdmin) {
    // El administrador ve los detalles técnicos, siempre en solo lectura.
    columns.push(detailsCard(order, { canManage: false, onChanged: reload }));
  }

  const side = [
    priceChangesCard(order, { isCustomer, canManage, onChanged: reload }),
    costsCard(order, { canManage, onChanged: reload }),
  ];
  if (canAct) {
    side.push(closeActionsCard(order, reload));
  }

  return Container(
    pageHeader(
      `Reparación ${order.id.slice(0, 8)}`,
      `${order.request.title} · ${formatMoney(order.final_price)}`,
      actions,
    ),
    h(
      "div",
      { class: "mt-6 grid gap-6 lg:grid-cols-3" },
      h("div", { class: "space-y-6 lg:col-span-2" }, ...columns),
      h("div", { class: "space-y-6" }, ...side, reportCard, reviewCard, reviewShown),
    ),
  );
}

function detailRow(label, value) {
  return h(
    "li",
    {},
    h("p", { class: "text-xs uppercase tracking-wide text-slate-500" }, label),
    h("p", { class: "whitespace-pre-line text-sm text-slate-700" }, value),
  );
}

function item(label, value) {
  return h(
    "div",
    {},
    h("dt", { class: "text-xs uppercase tracking-wide text-slate-500" }, label),
    h("dd", { class: "font-medium text-slate-700" }, value),
  );
}
