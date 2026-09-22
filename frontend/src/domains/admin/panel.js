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
import { formatDate, formatMoney, h } from "../../components/dom.js";
import { Container } from "../../components/layout/index.js";
import { alert, badge, button, card, emptyState, field, input, pageHeader, statCard, table, withBusy } from "../../components/ui/index.js";
import { navigate } from "../../lib/navigation.js";
import { routes } from "../../lib/paths.js";

export async function AdminPanel() {
  const [stats, specialties, technicians, requests, orders] = await Promise.all([
    api.get(endpoints.admin.stats),
    api.get(endpoints.admin.specialties),
    api.get(endpoints.admin.technicians({ limit: 50 })),
    api.get(endpoints.admin.requests({ limit: 8 })),
    api.get(endpoints.admin.orders({ limit: 8 })),
  ]);

  const specialtyList = h("div", { class: "mt-4 space-y-2" });
  function renderSpecialties(items) {
    specialtyList.replaceChildren(
      ...(items.length
        ? items.map((specialty) =>
            h(
              "div",
              { class: "flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2" },
              h(
                "div",
                {},
                h("p", { class: "text-sm font-medium text-slate-800" }, specialty.name),
                h("p", { class: "text-xs text-slate-500" }, specialty.description || ""),
              ),
              h(
                "div",
                { class: "flex items-center gap-2" },
                specialty.is_active ? badge("completed", "Activa") : badge("cancelled", "Inactiva"),
                button(specialty.is_active ? "Desactivar" : "Activar", {
                  variant: "ghost",
                  onClick: (event) =>
                    withBusy(event.currentTarget, async () => {
                      try {
                        await api.patch(endpoints.admin.specialty(specialty.id), { is_active: !specialty.is_active });
                        renderSpecialties(await api.get(endpoints.admin.specialties));
                      } catch (error) {
                        window.alert(error.message || "No se pudo actualizar la especialidad");
                      }
                    }),
                }),
                button("Eliminar", {
                  variant: "danger",
                  iconName: "trash-2",
                  onClick: (event) =>
                    withBusy(event.currentTarget, async () => {
                      if (!window.confirm(`¿Eliminar la especialidad ${specialty.name}?`)) return;
                      try {
                        await api.del(endpoints.admin.specialty(specialty.id));
                        renderSpecialties(await api.get(endpoints.admin.specialties));
                      } catch (error) {
                        window.alert(error.message || "No se pudo eliminar la especialidad");
                      }
                    }),
                }),
              ),
            ),
          )
        : [emptyState("Sin especialidades", "Crea la primera especialidad.")]),
    );
  }
  renderSpecialties(specialties);

  const createForm = h(
    "form",
    { class: "mt-4 space-y-3" },
    h("div", { "data-error": "true" }),
    field("Nombre", input({ name: "name", required: true, placeholder: "Ej: Drones" })),
    field("Descripción", input({ name: "description", placeholder: "Opcional" })),
    button("Crear especialidad", { type: "submit", variant: "success", iconName: "plus" }),
  );
  createForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const errorBox = createForm.querySelector("[data-error]");
    const data = new FormData(createForm);
    try {
      await api.post(endpoints.admin.specialties, { name: data.get("name"), description: data.get("description") || null });
      createForm.reset();
      renderSpecialties(await api.get(endpoints.admin.specialties));
    } catch (error) {
      errorBox.replaceChildren(alert(error.message || "No se pudo crear la especialidad"));
    }
  });

  const verifyBox = h("div", { class: "mt-4 space-y-2" });
  verifyBox.replaceChildren(
    ...technicians.items.map((technician) =>
      h(
        "div",
        { class: "flex items-center justify-between rounded-lg border border-slate-200 px-3 py-2" },
        h(
          "div",
          {},
          h("p", { class: "text-sm font-medium text-slate-800" }, technician.full_name),
          h(
            "p",
            { class: "text-xs text-slate-500" },
            `${technician.experience_years} años · ${Number(technician.rating_avg).toFixed(1)}/5${
              technician.district_name ? ` · ${technician.district_name}` : ""
            }`,
          ),
        ),
        button(technician.is_verified ? "Quitar verificación" : "Verificar", {
          variant: technician.is_verified ? "ghost" : "success",
          iconName: technician.is_verified ? "x" : "badge-check",
          onClick: (event) =>
            withBusy(event.currentTarget, async () => {
              try {
                await api.patch(
                  endpoints.admin.verifyTechnician(technician.id, !technician.is_verified),
                  {},
                );
                navigate(routes.admin);
              } catch (error) {
                window.alert(error.message || "No se pudo verificar al técnico");
              }
            }),
        }),
      ),
    ),
  );

  return Container(
    pageHeader("Panel administrativo", "Estadísticas, moderación y administración del marketplace."),
    h(
      "div",
      { class: "mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4" },
      statCard("Usuarios", stats.total_users, { iconName: "users" }),
      statCard("Técnicos", stats.total_technicians, { iconName: "wrench" }),
      statCard("Solicitudes abiertas", stats.open_requests, { accent: "text-amber-700", iconName: "clipboard-list" }),
      statCard("Ingresos", formatMoney(stats.total_revenue), { accent: "text-emerald-700", iconName: "circle-dollar-sign" }),
    ),
    h(
      "div",
      { class: "mt-8 grid gap-6 lg:grid-cols-2" },
      card(
        h(
          "div",
          { class: "flex items-center justify-between" },
          h("h2", { class: "text-lg font-semibold text-slate-900" }, "Especialidades"),
          button("Usuarios", { variant: "ghost", iconName: "users", onClick: () => navigate(routes.adminUsers) }),
        ),
        createForm,
        specialtyList,
      ),
      card(h("h2", { class: "text-lg font-semibold text-slate-900" }, "Verificación de técnicos"), verifyBox),
    ),
    h("h2", { class: "mt-8 mb-3 text-lg font-semibold text-slate-900" }, "Solicitudes recientes"),
    requests.items.length
      ? table(
          ["Título", "Cliente", { label: "Estado", align: "center" }, "Fecha", { label: "", align: "right" }],
          requests.items.map((request) => [
            request.title,
            request.customer.full_name,
            badge(request.status),
            formatDate(request.created_at),
            button("Ver", { variant: "outline", iconName: "eye", onClick: () => navigate(routes.requestDetail(request.id)) }),
          ]),
        )
      : emptyState("Sin solicitudes", "No hay solicitudes registradas."),
    h(
      "div",
      { class: "mt-8 mb-3 flex items-center justify-between" },
      h("h2", { class: "text-lg font-semibold text-slate-900" }, "Órdenes recientes"),
      button("Ver todas", {
        variant: "ghost",
        iconName: "receipt-text",
        onClick: () => navigate(routes.adminOrders),
      }),
    ),
    orders.items.length
      ? table(
          [
            "Orden",
            "Técnico",
            { label: "Estado", align: "center" },
            { label: "Total", align: "right" },
            { label: "", align: "right" },
          ],
          orders.items.map((order) => [
            order.id.slice(0, 8),
            order.technician.full_name,
            badge(order.status),
            formatMoney(order.final_price),
            button("Ver", { variant: "outline", iconName: "eye", onClick: () => navigate(routes.orderDetail(order.id)) }),
          ]),
        )
      : emptyState("Sin órdenes", "No hay órdenes registradas."),
  );
}
