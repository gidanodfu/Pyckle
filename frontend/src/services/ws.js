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

import { api, getTokens } from "../api/client.js";
import { endpoints } from "../api/endpoints.js";

/**
 * Abre un WebSocket autenticado por ticket efímero. El JWT nunca viaja en la
 * URL: se pide un ticket por REST, se usa una vez y el backend lo consume.
 */
export function connectWebSocket(path, { onMessage, onOpen, onClose } = {}) {
  let socket = null;
  let closedByUser = false;
  let attempts = 0;
  let timer = null;

  function scheduleReconnect() {
    if (closedByUser) return;
    attempts += 1;
    timer = window.setTimeout(open, Math.min(1000 * attempts, 10000));
  }

  function url(ticket) {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.host}${path}?ticket=${encodeURIComponent(ticket)}`;
  }

  async function open() {
    if (closedByUser) return;
    if (!getTokens().access) {
      scheduleReconnect();
      return;
    }
    let ticket = null;
    try {
      const response = await api.post(endpoints.ws.ticket);
      ticket = response?.ticket || null;
    } catch {
      ticket = null;
    }
    if (closedByUser) return;
    if (!ticket) {
      scheduleReconnect();
      return;
    }
    socket = new WebSocket(url(ticket));
    socket.onopen = () => {
      attempts = 0;
      if (onOpen) onOpen();
    };
    socket.onmessage = (event) => {
      try {
        if (onMessage) onMessage(JSON.parse(event.data));
      } catch {
        // Ignora mensajes no JSON.
      }
    };
    socket.onclose = () => {
      if (onClose) onClose();
      scheduleReconnect();
    };
    socket.onerror = () => socket && socket.close();
  }

  open();

  return {
    send(payload) {
      if (socket && socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify(payload));
    },
    close() {
      closedByUser = true;
      if (timer) window.clearTimeout(timer);
      if (socket) socket.close();
    },
  };
}
