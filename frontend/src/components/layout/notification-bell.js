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
import { formatDateTime, h } from "../dom.js";
import { icon } from "../icons.js";
import { createPopover } from "../popover.js";
import { badge, button, withBusy } from "../ui/index.js";
import { store } from "../../state/store.js";

export function notificationBell() {
  const badgeNode = h("span", {
    "data-notif-count": "true",
    class: "absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-emerald-600 px-1 text-[11px] font-bold text-white",
  });
  const panel = h("div", {
    "data-notif-panel": "true",
    class:
      "absolute right-0 mt-2 hidden max-h-96 w-[min(20rem,calc(100vw-2rem))] overflow-y-auto scrollbar-hidden rounded-xl border border-slate-200 bg-white p-2 shadow-lg",
  });
  const trigger = h(
    "button",
    {
      class:
        "relative inline-flex min-h-11 min-w-11 items-center justify-center rounded-lg p-2 text-slate-600 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2",
      "aria-label": "Notificaciones",
    },
    icon("bell", { size: 18 }),
    badgeNode,
  );
  const wrapper = h("div", { class: "relative" }, trigger, panel);
  createPopover({ trigger, panel, wrapper });

  function renderPanel() {
    const { notifications, unread } = store.get();
    badgeNode.textContent = String(unread);
    badgeNode.classList.toggle("hidden", unread === 0);
    panel.replaceChildren();
    if (notifications.length === 0) {
      panel.append(h("p", { class: "p-3 text-sm text-slate-500" }, "Sin notificaciones"));
      return;
    }
    for (const item of notifications.slice(0, 20)) {
      panel.append(
        h(
          "div",
          { class: `rounded-lg p-3 ${item.is_read ? "" : "bg-blue-50"}` },
          h(
            "div",
            { class: "flex items-center justify-between gap-2" },
            h("p", { class: "text-sm font-semibold" }, item.title),
            badge(item.type, ""),
          ),
          h("p", { class: "mt-1 text-xs text-slate-600" }, item.body),
          h("p", { class: "mt-1 text-[11px] text-slate-500" }, formatDateTime(item.created_at)),
        ),
      );
    }
    panel.append(
      button("Marcar todas como leídas", {
        variant: "ghost",
        class: "mt-2 w-full",
        iconName: "check",
        disabled: unread === 0,
        onClick: (event) =>
          withBusy(event.currentTarget, async () => {
            if (store.get().unread === 0) return;
            await api.post(endpoints.notifications.readAll, {});
            const updated = store.get().notifications.map((item) => ({ ...item, is_read: true }));
            store.setNotifications(updated);
          }),
      }),
    );
  }

  renderPanel();
  return { node: wrapper, update: renderPanel };
}
