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

import { api } from "../api/client.js";
import { endpoints } from "../api/endpoints.js";
import { teardownChat } from "../domains/chat/page.js";
import { connectWebSocket } from "../services/ws.js";
import { ws } from "../lib/paths.js";
import { store } from "../state/store.js";

let notificationSocket = null;

function setupRealtime() {
  if (notificationSocket) return;
  notificationSocket = connectWebSocket(ws.notifications, {
    onMessage(event) {
      if (event.event === "notification.new") store.addNotification(event.notification);
    },
  });
}

export function closeRealtime() {
  if (notificationSocket) {
    notificationSocket.close();
    notificationSocket = null;
  }
  teardownChat();
}

async function loadNotifications() {
  try {
    const notifications = await api.get(endpoints.notifications.list({ limit: 20 }));
    store.setNotifications(notifications);
  } catch {
    // Silencioso: las notificaciones no deben bloquear la app.
  }
}

export function onAuthenticated() {
  loadNotifications();
  setupRealtime();
}
