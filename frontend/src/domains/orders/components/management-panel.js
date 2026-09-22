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

import { api } from "../../../api/client.js";
import { endpoints } from "../../../api/endpoints.js";
import { h } from "../../../components/dom.js";
import { alert, button, card, withBusy } from "../../../components/ui/index.js";
import { NEXT_TRANSITIONS } from "./technical-status.js";

/** Panel del técnico para avanzar el estado técnico de la reparación. */
export function managementPanel(order, reload) {
  const transitions = NEXT_TRANSITIONS[order.status] || [];
  return card(
    h("h3", { class: "mb-3 text-lg font-semibold text-slate-900" }, "Actualizar proceso"),
    order.has_pending_price_change
      ? alert(
          "Hay un cambio de precio pendiente de aprobación del cliente; no puedes continuar el trabajo facturable.",
          "warning",
        )
      : null,
    h(
      "div",
      { class: "mt-3 flex flex-wrap gap-2" },
      transitions.map((transition) =>
        button(transition.label, {
          iconName: transition.iconName,
          onClick: (event) =>
            withBusy(event.currentTarget, async () => {
              try {
                await api.patch(endpoints.orders.status(order.id), { status: transition.value });
                reload();
              } catch (error) {
                window.alert(error.message || "No se pudo actualizar el estado");
              }
            }),
        }),
      ),
    ),
  );
}
