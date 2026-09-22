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

import { routes } from "./paths.js";

/**
 * Destino canónico del "panel" para un usuario autenticado.
 *
 * Solo decide navegación; la autorización de cada ruta vive en el router y el
 * backend. En multi-rol prevalece admin > technician > customer, de modo que un
 * usuario con rol admin nunca cae en el panel de otro rol.
 */
export function panelPath(me) {
  const roles = (me?.user?.roles || []).map((role) => role.name);
  if (roles.includes("admin")) return routes.admin;
  if (roles.includes("technician")) return routes.technicianDashboard;
  if (roles.includes("customer")) return routes.dashboard;
  return routes.home;
}
