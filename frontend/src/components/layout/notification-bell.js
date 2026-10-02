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
import { badge, button, toast, withBusy } from "../ui/index.js";
import { store } from "../../state/store.js";

export function notificationBell() {
  const badgeNode = h("span", {
    "data-notif-count": "true",
    class:
      "absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1 text-[11px] font-bold text-primary-foreground",
  });
  const panel = h("div", {
    "data-notif-panel": "true",
    class:
      "absolute right-0 mt-2 hidden max-h-96 w-[min(20rem,calc(100vw-2rem))] overflow-y-auto scrollbar-hidden rounded-lg border border-border bg-surface-elevated p-2 shadow-floating",
  });
  const trigger = h(
    "button",
    {
      class:
        "relative inline-flex min-h-11 min-w-11 items-center justify-center rounded-md p-2 text-foreground-secondary hover:bg-surface-hover hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-background",
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
      panel.append(h("p", { class: "p-3 text-sm text-muted" }, "Sin notificaciones"));
      return;
    }
    for (const item of notifications.slice(0, 20)) {
      panel.append(
        h(
          "div",
          { class: `rounded-md p-3 ${item.is_read ? "" : "bg-primary-tint"}` },
          h(
            "div",
            { class: "flex items-center justify-between gap-2" },
            h("p", { class: "text-sm font-semibold text-foreground" }, item.title),
            badge(item.type, ""),
          ),
          h("p", { class: "mt-1 text-xs text-foreground-secondary" }, item.body),
          h("p", { class: "mt-1 text-[11px] text-muted" }, formatDateTime(item.created_at)),
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
            try {
              await api.post(endpoints.notifications.readAll, {});
              const updated = store.get().notifications.map((item) => ({ ...item, is_read: true }));
              store.setNotifications(updated);
              toast("Notificaciones marcadas como leídas", { type: "success", duration: 2500 });
            } catch (error) {
              toast(error.message || "No se pudieron marcar las notificaciones", { type: "error" });
            }
          }),
      }),
    );
  }

  renderPanel();
  return { node: wrapper, update: renderPanel };
}
