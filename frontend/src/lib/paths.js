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

import logo from "../../assets/img/Icono/Pyckle-256.png";
import logo64 from "../../assets/img/Icono/Pyckle-64.png";

/**
 * Fuente única de assets, rutas internas y datos de sitio.
 *
 * Vite resuelve los imports de imagen, así que los componentes nunca deben
 * escribir rutas de assets a mano: consumen `assets.*` desde aquí.
 */
export const assets = {
  logo,
  logo64,
  favicon: "/favicon.png",
  appleTouchIcon: "/apple-touch-icon.png",
};

/**
 * Rutas internas del router. Fuente única para los consumidores: los
 * componentes no deben escribir paths de navegación a mano.
 * Los patrones con `:param` se definen en `app/routes.js` usando los builders.
 */
/**
 * Rutas de WebSocket. Fuente única para los consumidores.
 */
export const ws = {
  notifications: "/ws/notifications",
  chat: (conversationId) => `/ws/chat/${conversationId}`,
};

export const routes = {
  home: "/",
  login: "/login",
  register: "/register",
  registerTechnician: "/register?role=technician",
  oauthCallback: "/auth/callback",
  dashboard: "/dashboard",
  technicianDashboard: "/technician",
  technicianRepairs: "/technician/repairs",
  technicianQuotations: "/technician/quotations",
  technicianReports: "/technician/reports",
  admin: "/admin",
  adminUsers: "/admin/users",
  adminOrders: "/admin/orders",
  requests: "/requests",
  requestNew: "/requests/new",
  requestDetail: (id) => `/requests/${id}`,
  orders: "/orders",
  orderDetail: (id) => `/orders/${id}`,
  chat: "/chat",
  chatWith: (conversationId) => `/chat?conversation=${conversationId}`,
  profileCustomer: "/profile/customer",
  profileTechnician: "/profile/technician",
  technicians: "/technicians",
  technicianProfile: (id) => `/technicians/${id}`,
  legal: "/legal",
  privacy: "/legal/privacy",
  terms: "/legal/terms",
  dataTreatment: "/legal/data-treatment",
  contact: "/contact",
};

/**
 * Datos de sitio pendientes de configuración legal.
 * Los placeholders se muestran marcados en las páginas legales hasta que
 * existan los datos reales.
 */
export const site = {
  name: "Pyckle",
  legalReviewPending: true,
  legalEntity: "[RAZÓN SOCIAL PENDIENTE]",
  taxId: "[RUC PENDIENTE]",
  fiscalAddress: "[DOMICILIO FISCAL PENDIENTE]",
  contactEmail: "[CORREO DE CONTACTO PENDIENTE]",
  privacyEmail: "[CORREO DE PRIVACIDAD PENDIENTE]",
  legalEmail: "[CORREO LEGAL PENDIENTE]",
};
