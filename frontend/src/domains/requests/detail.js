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
import { badge, button, card, emptyState, pageHeader, verifiedBadge, withBusy } from "../../components/ui/index.js";
import { routes } from "../../lib/paths.js";
import { navigate } from "../../lib/navigation.js";
import { hasRole, store } from "../../state/store.js";
import { quotationCard, quoteFormCard } from "./components/quotation-card.js";

export async function RequestDetail({ id }) {
  const request = await api.get(endpoints.requests.byId(id));
  const me = store.get().me;
  const isOwner = request.customer.id === me.user.id;
  const isAdmin = hasRole("admin");
  const isTechnician = hasRole("technician");

  let quotations = [];
  try {
    quotations = await api.get(endpoints.quotations.byRequest(id));
  } catch {
    quotations = [];
  }

  let order = null;
  try {
    const orders = await api.get(endpoints.orders.list({ request_id: id, limit: 1 }));
    order = orders.items[0] || null;
  } catch {
    order = null;
  }

  // El administrador no usa el chat: no se consultan conversaciones.
  let conversation = null;
  if (!isAdmin) {
    try {
      const conversations = await api.get(endpoints.conversations.list({ request_id: id }));
      conversation = conversations.find((item) => item.request_id === id) || null;
    } catch {
      conversation = null;
    }
  }

  const locationLabel =
    [request.district_name || request.district, request.province_name, request.department_name]
      .filter(Boolean)
      .join(", ") || "-";

  const info = card(
    h(
      "div",
      { class: "flex flex-wrap items-center justify-between gap-2" },
      h("h2", { class: "text-xl font-bold text-slate-900" }, request.title),
      badge(request.status),
    ),
    h("p", { class: "mt-3 whitespace-pre-line text-sm text-slate-600" }, request.description),
    h(
      "dl",
      { class: "mt-4 grid gap-3 text-sm sm:grid-cols-2" },
      detailItem("Especialidad", request.specialty?.name || "General"),
      detailItem("Modalidad", statusLabel(request.modality)),
      detailItem("Ubicación", locationLabel),
      detailItem("Presupuesto", request.budget_min || request.budget_max ? `${formatMoney(request.budget_min || 0)} - ${formatMoney(request.budget_max || 0)}` : "A convenir"),
      detailItem("Cliente", request.customer.full_name),
      detailItem(
        "Técnico asignado",
        request.assigned_technician
          ? h(
              "span",
              { class: "inline-flex items-center gap-1.5" },
              request.assigned_technician.full_name,
              verifiedBadge(request.assigned_technician.is_verified),
            )
          : "Sin asignar",
      ),
    ),
    request.address
      ? h(
          "p",
          { class: "mt-4 inline-flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-600" },
          icon("map-pin", { size: 15 }),
          request.address,
        )
      : isTechnician && !isOwner
        ? h("p", { class: "mt-4 text-xs text-slate-500" }, "La dirección exacta se muestra al aceptar la cotización.")
        : null,
    (request.images || []).length
      ? h(
          "div",
          { class: "mt-4 grid grid-cols-3 gap-3 sm:grid-cols-4" },
          request.images.map((image) =>
            h(
              "a",
              { href: image.url, target: "_blank", rel: "noopener", class: "block" },
              h("img", { src: image.url, alt: `Imagen de ${request.title}`, loading: "lazy", class: "h-24 w-full rounded-lg border border-slate-200 object-cover" }),
            ),
          ),
        )
      : null,
  );

  const actions = h("div", { class: "flex flex-wrap gap-2" });
  if (order) actions.append(button("Ver orden", { variant: "success", iconName: "receipt-text", onClick: () => navigate(routes.orderDetail(order.id)) }));
  if (conversation) actions.append(button("Abrir chat", { variant: "outline", iconName: "message-square", onClick: () => navigate(routes.chatWith(conversation.id)) }));
  if (isOwner && ["open", "quoted"].includes(request.status)) {
    actions.append(
      button("Cancelar solicitud", {
        variant: "danger",
        iconName: "ban",
        onClick: (event) =>
          withBusy(event.currentTarget, async () => {
            if (!window.confirm("¿Deseas cancelar esta solicitud?")) return;
            try {
              await api.post(endpoints.requests.cancel(id), {});
              navigate(routes.requestDetail(id));
            } catch (error) {
              window.alert(error.message || "No se pudo cancelar la solicitud");
            }
          }),
      }),
    );
  }

  const quotationSection = h(
    "section",
    { class: "mt-8 space-y-3" },
    h("h3", { class: "text-lg font-semibold text-slate-900" }, `Cotizaciones (${quotations.length})`),
    quotations.length
      ? quotations.map((quotation) => quotationCard(quotation, { isOwner }))
      : emptyState(
          "Sin cotizaciones",
          isTechnician ? "Envía la primera cotización para esta solicitud." : "Aún no hay cotizaciones de técnicos.",
          null,
          { iconName: "file-text" },
        ),
  );

  const quoteForm =
    isTechnician && !isOwner && ["open", "quoted"].includes(request.status)
      ? quoteFormCard(id)
      : null;

  return Container(
    pageHeader("Detalle de solicitud", `Publicada el ${formatDateTime(request.created_at)}`, actions),
    h(
      "div",
      { class: "mt-6 grid gap-6 lg:grid-cols-3" },
      h("div", { class: "lg:col-span-2" }, info, quotationSection),
      h("div", { class: "space-y-6" }, quoteForm),
    ),
  );
}

function detailItem(label, value) {
  return h(
    "div",
    {},
    h("dt", { class: "text-xs uppercase tracking-wide text-slate-500" }, label),
    h("dd", { class: "font-medium text-slate-700" }, value),
  );
}
