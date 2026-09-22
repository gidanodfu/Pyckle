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
import { formatDateTime, h } from "../../components/dom.js";
import { Container } from "../../components/layout/index.js";
import { alert, badge, button, emptyState, pageHeader } from "../../components/ui/index.js";
import { navigate } from "../../lib/navigation.js";
import { store } from "../../state/store.js";
import { connectWebSocket } from "../../services/ws.js";
import { routes, ws } from "../../lib/paths.js";

let activeSocket = null;
// Generación de render del chat: si otra navegación/render arranca mientras este
// await está en vuelo, el render obsoleto no debe abrir un socket huérfano.
let chatGeneration = 0;

export function teardownChat() {
  chatGeneration += 1;
  if (activeSocket) {
    activeSocket.close();
    activeSocket = null;
  }
}

export async function ChatPage() {
  teardownChat();
  const generation = chatGeneration;

  const conversations = await api.get(endpoints.conversations.list());
  if (generation !== chatGeneration) return null;
  if (!conversations.length) {
    return Container(
      pageHeader("Chat", "Conversaciones con clientes y técnicos."),
      h(
        "div",
        { class: "mt-6" },
        emptyState(
          "Sin conversaciones",
          "Las conversaciones se crean al aceptar una cotización.",
          null,
          { iconName: "message-square" },
        ),
      ),
    );
  }

  const params = new URLSearchParams(window.location.search);
  const selectedId = params.get("conversation") || conversations[0].id;
  const selected = conversations.find((item) => item.id === selectedId) || conversations[0];
  const me = store.get().me;

  const messages = await api.get(endpoints.conversations.messages(selected.id));
  if (generation !== chatGeneration) return null;
  const messagesBox = h("div", { class: "flex-1 space-y-3 overflow-y-auto p-4" });
  const rendered = new Set();

  function appendMessage(message) {
    if (rendered.has(message.id)) return;
    rendered.add(message.id);
    messagesBox.append(messageBubble(message, me.user.id));
    messagesBox.scrollTop = messagesBox.scrollHeight;
  }
  for (const message of messages) appendMessage(message);

  const isOpen = selected.status === "open";
  const input = h("input", {
    name: "body",
    class: "field-input",
    placeholder: isOpen ? "Escribe un mensaje..." : "Conversación finalizada",
    autocomplete: "off",
    disabled: !isOpen,
  });
  const sendButton = button("Enviar", { type: "submit", iconName: "send", disabled: !isOpen });
  const form = h("form", { class: "flex gap-2 border-t border-slate-200 p-3" }, input, sendButton);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const body = input.value.trim();
    if (!body || !isOpen) return;
    sendButton.disabled = true;
    try {
      const message = await api.post(endpoints.conversations.send(selected.id), { body });
      appendMessage(message);
      input.value = "";
    } catch (error) {
      window.alert(error.message || "No se pudo enviar el mensaje");
    } finally {
      sendButton.disabled = false;
    }
  });

  const activeConversations = conversations.filter((item) => item.status === "open");
  const archivedConversations = conversations.filter((item) => item.status !== "open");

  function conversationButton(conversation) {
    const other =
      conversation.customer.id === me.user.id
        ? conversation.technician.full_name
        : conversation.customer.full_name;
    const active = conversation.id === selected.id;
    return h(
      "button",
      {
        class: `w-full rounded-lg border px-3 py-2 text-left text-sm transition ${
          active ? "border-blue-300 bg-blue-50" : "border-slate-200 hover:bg-slate-50"
        }`,
        onClick: () => navigate(routes.chatWith(conversation.id)),
      },
      h(
        "div",
        { class: "flex items-center justify-between gap-2" },
        h("p", { class: "truncate font-medium text-slate-800" }, other),
        conversation.status !== "open" ? badge("archived") : null,
      ),
      h(
        "p",
        { class: "text-xs text-slate-500" },
        conversation.last_message_at ? formatDateTime(conversation.last_message_at) : "Sin mensajes",
      ),
    );
  }

  const sidebar = h(
    "div",
    { class: "space-y-2 lg:max-h-[70vh] lg:overflow-y-auto" },
    activeConversations.length
      ? h("p", { class: "px-1 text-xs font-semibold uppercase tracking-wide text-slate-500" }, "Activos")
      : null,
    activeConversations.map(conversationButton),
    archivedConversations.length
      ? h("p", { class: "px-1 pt-3 text-xs font-semibold uppercase tracking-wide text-slate-500" }, "Archivados")
      : null,
    archivedConversations.map(conversationButton),
  );

  const other =
    selected.customer.id === me.user.id ? selected.technician.full_name : selected.customer.full_name;
  const pane = h(
    "div",
    { class: "flex h-[70vh] flex-col rounded-xl border border-slate-200 bg-white" },
    h(
      "div",
      { class: "flex items-center justify-between gap-3 border-b border-slate-200 px-4 py-3" },
      h(
        "div",
        {},
        h("p", { class: "font-semibold text-slate-900" }, other),
        h("p", { class: "text-xs text-slate-500" }, isOpen ? "Mensajes en tiempo real" : "Conversación finalizada"),
      ),
      selected.status !== "open" ? badge("archived") : null,
    ),
    messagesBox,
    isOpen
      ? form
      : h(
          "div",
          { class: "border-t border-slate-200 p-3" },
          alert("Esta conversación finalizó porque la reparación se completó. El historial permanece disponible.", "info"),
        ),
  );

  if (isOpen && generation === chatGeneration) {
    const socket = connectWebSocket(ws.chat(selected.id), {
      onMessage(event) {
        if (generation !== chatGeneration) {
          socket.close();
          return;
        }
        if (event.event === "message.new") appendMessage(event.message);
      },
    });
    activeSocket = socket;
  }

  return Container(
    pageHeader("Chat", "Comunicación directa entre cliente y técnico."),
    h("div", { class: "mt-6 grid gap-4 lg:grid-cols-[280px_1fr]" }, sidebar, pane),
  );
}

function messageBubble(message, ownId) {
  const own = message.sender.id === ownId;
  return h(
    "div",
    { class: `flex ${own ? "justify-end" : "justify-start"}` },
    h(
      "div",
      {
        class: `max-w-[75%] rounded-2xl px-4 py-2 text-sm ${
          own ? "bg-blue-700 text-white" : "bg-slate-100 text-slate-800"
        }`,
      },
      h("p", { class: "whitespace-pre-line" }, message.body),
      h(
        "p",
        { class: `mt-1 text-[10px] ${own ? "text-blue-100" : "text-slate-600"}` },
        formatDateTime(message.created_at),
      ),
    ),
  );
}
