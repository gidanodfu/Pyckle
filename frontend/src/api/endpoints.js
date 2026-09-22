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

function query(params = {}) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    search.set(key, String(value));
  }
  const suffix = search.toString();
  return suffix ? `?${suffix}` : "";
}

export const endpoints = {
  auth: {
    login: "/auth/login",
    register: "/auth/register",
    refresh: "/auth/refresh",
    logout: "/auth/logout",
    me: "/auth/me",
    providers: "/auth/providers",
    // Flujo OAuth server-side: el frontend solo navega a este endpoint.
    google: "/auth/google",
    oauthExchange: "/auth/oauth/exchange",
    // Peek no consumible de la identidad pendiente de onboarding.
    oauthOnboarding: "/auth/oauth/onboarding",
    oauthComplete: "/auth/oauth/complete",
  },
  users: {
    me: "/users/me",
    updateMe: "/users/me",
    changePassword: "/users/me/change-password",
    customerProfile: "/users/me/customer-profile",
  },
  geo: {
    departments: "/geo/departments",
    provinces: (departmentId) => `/geo/departments/${departmentId}/provinces`,
    districts: (provinceId) => `/geo/provinces/${provinceId}/districts`,
  },
  specialties: {
    list: "/specialties",
  },
  technicians: {
    list: (params) => `/technicians${query(params)}`,
    me: "/technicians/me",
    updateMe: "/technicians/me",
    stats: "/technicians/me/stats",
    summary: "/technicians/me/summary",
    byId: (id) => `/technicians/${id}`,
    reviews: (id, params) => `/technicians/${id}/reviews${query(params)}`,
  },
  requests: {
    create: "/repair-requests",
    list: (params) => `/repair-requests${query(params)}`,
    available: (params) => `/repair-requests/available${query(params)}`,
    byId: (id) => `/repair-requests/${id}`,
    update: (id) => `/repair-requests/${id}`,
    cancel: (id) => `/repair-requests/${id}/cancel`,
    images: (id) => `/repair-requests/${id}/images`,
  },
  quotations: {
    create: "/quotations",
    mine: "/quotations/mine",
    byRequest: (requestId) => `/quotations/request/${requestId}`,
    accept: (id) => `/quotations/${id}/accept`,
    withdraw: (id) => `/quotations/${id}/withdraw`,
  },
  orders: {
    list: (params) => `/orders${query(params)}`,
    byId: (id) => `/orders/${id}`,
    status: (id) => `/orders/${id}/status`,
    repairDetails: (id) => `/orders/${id}/repair-details`,
    complete: (id) => `/orders/${id}/complete`,
    notRepairable: (id) => `/orders/${id}/not-repairable`,
    cancel: (id) => `/orders/${id}/cancel`,
    priceChanges: (id) => `/orders/${id}/price-changes`,
    approvePriceChange: (id, changeId) => `/orders/${id}/price-changes/${changeId}/approve`,
    rejectPriceChange: (id, changeId) => `/orders/${id}/price-changes/${changeId}/reject`,
    costs: (id) => `/orders/${id}/costs`,
    reports: (id) => `/orders/${id}/reports`,
    report: (id) => `/orders/${id}/report`,
    customerProfile: (id) => `/orders/${id}/customer-profile`,
  },
  conversations: {
    list: (params) => `/conversations${query(params)}`,
    byId: (id) => `/conversations/${id}`,
    messages: (id, params) => `/conversations/${id}/messages${query(params)}`,
    send: (id) => `/conversations/${id}/messages`,
  },
  reviews: {
    create: "/reviews",
    technician: (id) => `/reviews/technician/${id}`,
  },
  notifications: {
    list: (params) => `/notifications${query(params)}`,
    unreadCount: "/notifications/unread-count",
    readAll: "/notifications/read-all",
  },
  media: (url) => url,
  ws: {
    ticket: "/ws/ticket",
  },
  admin: {
    stats: "/admin/stats",
    users: (params) => `/admin/users${query(params)}`,
    user: (id) => `/admin/users/${id}`,
    roles: "/admin/roles",
    permissions: "/admin/permissions",
    requests: (params) => `/admin/requests${query(params)}`,
    request: (id) => `/admin/requests/${id}`,
    orders: (params) => `/admin/orders${query(params)}`,
    technicians: (params) => `/admin/technicians${query(params)}`,
    verifyTechnician: (id, verified = true) =>
      `/admin/technicians/${id}/verify${query({ verified })}`,
    specialties: "/admin/specialties",
    specialty: (id) => `/admin/specialties/${id}`,
  },
};
