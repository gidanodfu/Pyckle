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

import { endpoints } from "./endpoints.js";

export const API_BASE = import.meta.env?.VITE_API_BASE_URL || "/api/v1";
const ACCESS_KEY = "pyckle_access_token";
const REFRESH_KEY = "pyckle_refresh_token";

const FIELD_LABELS = {
  email: "Correo",
  password: "Contraseña",
  current_password: "Contraseña actual",
  new_password: "Nueva contraseña",
  full_name: "Nombre",
  phone: "Teléfono",
  role: "Tipo de cuenta",
  department_id: "Departamento",
  province_id: "Provincia",
  district_id: "Distrito",
  address: "Dirección",
  workshop_address: "Dirección del local",
  title: "Título",
  description: "Descripción",
  price: "Precio",
  preliminary_diagnosis: "Diagnóstico",
  estimated_days: "Días estimados",
  rating: "Calificación",
  comment: "Comentario",
  body: "Mensaje",
  budget_min: "Presupuesto mínimo",
  budget_max: "Presupuesto máximo",
  specialty_id: "Especialidad",
  request_id: "Solicitud",
  order_id: "Orden",
};

function translateMessage(message) {
  return message
    .replace(/^Value error,\s*/i, "")
    .replace(/^Field required$/i, "es obligatorio")
    .replace(/^Input should be a valid email address.*$/i, "correo inválido")
    .replace(/^Input should be a valid UUID.*$/i, "selección inválida")
    .replace(/^Input should be a valid/i, "valor inválido")
    .replace(/^String should have at least (\d+) characters?$/i, "debe tener al menos $1 caracteres")
    .replace(/^String should have at most (\d+) characters?$/i, "no debe superar $1 caracteres")
    .replace(/^Number should be greater than or equal to (\S+)$/i, "debe ser mayor o igual a $1")
    .replace(/^Input should be greater than (\S+)$/i, "debe ser mayor a $1");
}

function validationMessage(details) {
  if (!Array.isArray(details) || details.length === 0) return null;
  const parts = details.map((item) => {
    const location = Array.isArray(item?.loc) ? item.loc[item.loc.length - 1] : null;
    const label = FIELD_LABELS[location];
    const message = translateMessage(String(item?.msg || ""));
    if (!message) return null;
    return label ? `${label}: ${message}` : message;
  });
  const unique = [...new Set(parts.filter(Boolean))];
  return unique.length ? unique.join(". ") : null;
}

export class ApiError extends Error {
  constructor(message, status, details) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

const TIMEOUT_MS = 20000;

async function fetchWithTimeout(url, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } catch (error) {
    if (error && error.name === "AbortError") {
      throw new ApiError("La solicitud tardó demasiado. Intenta nuevamente.", 0);
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export function getTokens() {
  return {
    access: localStorage.getItem(ACCESS_KEY),
    refresh: localStorage.getItem(REFRESH_KEY),
  };
}

export function setTokens(tokens) {
  if (tokens?.access_token) localStorage.setItem(ACCESS_KEY, tokens.access_token);
  if (tokens?.refresh_token) localStorage.setItem(REFRESH_KEY, tokens.refresh_token);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

// Single-flight: varias peticiones que reciben 401 a la vez comparten una
// única renovación del refresh token.
let refreshPromise = null;

async function refreshTokens() {
  const { refresh } = getTokens();
  if (!refresh) return false;
  if (!refreshPromise) {
    refreshPromise = fetchWithTimeout(`${API_BASE}${endpoints.auth.refresh}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    })
      .then(async (response) => {
        if (!response.ok) throw new Error("No se pudo refrescar");
        setTokens(await response.json());
        return true;
      })
      .catch(() => {
        clearTokens();
        return false;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

async function request(path, { method = "GET", body, auth = true, form = false, retry = true } = {}) {
  const headers = {};
  const { access } = getTokens();
  if (auth && access) headers.Authorization = `Bearer ${access}`;
  let payload = body;
  if (body != null && !form) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  const response = await fetchWithTimeout(`${API_BASE}${path}`, {
    method,
    headers,
    body: payload,
  });

  if (response.status === 401 && auth && retry) {
    // Un solo reintento por petición tras renovar, para no entrar en bucle.
    const refreshed = await refreshTokens();
    if (refreshed) return request(path, { method, body, auth, form, retry: false });
    window.dispatchEvent(new CustomEvent("auth:expired"));
  }

  const data = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    const message =
      validationMessage(data?.details) ||
      (Array.isArray(data?.detail) ? "Datos inválidos" : data?.detail) ||
      `Error ${response.status}`;
    throw new ApiError(message, response.status, data?.details);
  }
  return data;
}

async function download(path, { retry = true } = {}) {
  const { access } = getTokens();
  const headers = access ? { Authorization: `Bearer ${access}` } : {};
  const response = await fetchWithTimeout(`${API_BASE}${path}`, { headers });
  if (response.status === 401 && retry) {
    const refreshed = await refreshTokens();
    if (refreshed) return download(path, { retry: false });
    window.dispatchEvent(new CustomEvent("auth:expired"));
  }
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new ApiError(data?.detail || `Error ${response.status}`, response.status);
  }
  return response.blob();
}

export const api = {
  get: (path, options) => request(path, options),
  post: (path, body, options) => request(path, { method: "POST", body, ...options }),
  put: (path, body, options) => request(path, { method: "PUT", body, ...options }),
  patch: (path, body, options) => request(path, { method: "PATCH", body, ...options }),
  del: (path, options) => request(path, { method: "DELETE", ...options }),
  delete: (path, options) => request(path, { method: "DELETE", ...options }),
  download,
  upload: (path, file, options) => {
    const formData = new FormData();
    formData.append("file", file);
    return request(path, { method: "POST", body: formData, form: true, ...options });
  },
};
