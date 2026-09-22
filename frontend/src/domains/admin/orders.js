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

import { endpoints } from "../../api/endpoints.js";
import { ordersView } from "../orders/list.js";

/**
 * Vista administrativa de todas las órdenes (solo lectura). Reutiliza la misma
 * tabla, filtros y paginación de `ordersView`, apuntando al endpoint admin.
 */
export async function AdminOrders() {
  return ordersView({
    title: "Órdenes",
    subtitle: "Supervisión de todas las órdenes del marketplace (solo lectura).",
    endpoint: endpoints.admin.orders,
    admin: true,
  });
}
