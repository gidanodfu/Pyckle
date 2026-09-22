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

import { AdminOrders } from "../domains/admin/orders.js";
import { AdminPanel } from "../domains/admin/panel.js";
import { UsersPage } from "../domains/admin/users.js";
import { Login, OAuthCallback, Register } from "../domains/auth/index.js";
import { ChatPage } from "../domains/chat/page.js";
import { CustomerDashboard } from "../domains/dashboards/page.js";
import { TechnicianDashboard } from "../domains/technicians/dashboard.js";
import { ContactPage, DataTreatmentPage, LegalIndexPage, PrivacyPolicyPage, TermsPage } from "../domains/legal/index.js";
import { Landing } from "../domains/landing/page.js";
import { NotFound } from "../domains/notfound/page.js";
import { OrderDetail, OrdersList } from "../domains/orders/index.js";
import { CustomerProfilePage } from "../domains/profile/page.js";
import { RequestCreate, RequestDetail, RequestsList } from "../domains/requests/index.js";
import {
  TechnicianOwnProfile,
  TechnicianProfile,
  TechnicianQuotations,
  TechnicianRepairs,
  TechnicianReports,
  TechniciansList,
} from "../domains/technicians/index.js";
import { routes } from "../lib/paths.js";

/**
 * Tabla de rutas del router. Es la única fuente de patrones `:param`;
 * los consumidores navegan con los builders de `lib/paths.js`.
 */
export const appRoutes = [
  { path: routes.home, page: Landing, title: "Marketplace de reparaciones" },
  { path: routes.login, page: Login, guest: true, title: "Iniciar sesión" },
  { path: routes.register, page: Register, guest: true, title: "Crear cuenta" },
  { path: routes.oauthCallback, page: OAuthCallback, title: "Autenticando" },
  { path: routes.dashboard, page: CustomerDashboard, auth: true, title: "Mi panel" },
  { path: routes.technicianDashboard, page: TechnicianDashboard, auth: true, title: "Panel técnico" },
  { path: routes.technicianRepairs, page: TechnicianRepairs, auth: true, title: "Mis reparaciones" },
  { path: routes.technicianQuotations, page: TechnicianQuotations, auth: true, title: "Mis cotizaciones" },
  { path: routes.technicianReports, page: TechnicianReports, auth: true, title: "Informes" },
  { path: routes.admin, page: AdminPanel, auth: true, permission: "admin:users", title: "Administración" },
  { path: routes.adminUsers, page: UsersPage, auth: true, permission: "admin:users", title: "Usuarios" },
  { path: routes.adminOrders, page: AdminOrders, auth: true, permission: "admin:orders", title: "Órdenes" },
  { path: routes.requests, page: RequestsList, auth: true, title: "Solicitudes" },
  { path: routes.requestNew, page: RequestCreate, auth: true, title: "Nueva solicitud" },
  { path: routes.requestDetail(":id"), page: RequestDetail, auth: true, title: "Detalle de solicitud" },
  { path: routes.orders, page: OrdersList, auth: true, title: "Órdenes" },
  { path: routes.orderDetail(":id"), page: OrderDetail, auth: true, title: "Detalle de orden" },
  { path: routes.chat, page: ChatPage, auth: true, deniedRoles: ["admin"], title: "Chat" },
  { path: routes.profileCustomer, page: CustomerProfilePage, auth: true, title: "Mi perfil" },
  { path: routes.profileTechnician, page: TechnicianOwnProfile, auth: true, title: "Perfil profesional" },
  { path: routes.technicians, page: TechniciansList, title: "Técnicos" },
  { path: routes.technicianProfile(":id"), page: TechnicianProfile, title: "Perfil del técnico" },
  { path: routes.legal, page: LegalIndexPage, title: "Información legal" },
  { path: routes.privacy, page: PrivacyPolicyPage, title: "Política de Privacidad" },
  { path: routes.terms, page: TermsPage, title: "Términos y Condiciones" },
  { path: routes.dataTreatment, page: DataTreatmentPage, title: "Tratamiento de Datos" },
  { path: routes.contact, page: ContactPage, title: "Contacto" },
];
