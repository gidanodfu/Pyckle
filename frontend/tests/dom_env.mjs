import { Window } from "happy-dom";

export const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/** Prepara un DOM aislado y los globales que usa el bundle del frontend. */
export function setupDom({ url = "http://localhost/" } = {}) {
  const window = new Window({ url });
  window.document.body.innerHTML = '<div id="app"></div>';
  globalThis.window = window;
  globalThis.document = window.document;
  globalThis.location = window.location;
  globalThis.history = window.history;
  globalThis.localStorage = window.localStorage;
  globalThis.Node = window.Node;
  globalThis.HTMLElement = window.HTMLElement;
  globalThis.CustomEvent = window.CustomEvent;
  globalThis.Event = window.Event;
  globalThis.KeyboardEvent = window.KeyboardEvent;
  globalThis.MouseEvent = window.MouseEvent;
  // Node expone su propio FormData (undici); el bundle necesita el del DOM.
  globalThis.FormData = window.FormData;
  globalThis.WebSocket = class {
    send() {}
    close() {}
  };
  return window;
}

export function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

export function page(items, extra = {}) {
  return { items, total: items.length, limit: 20, offset: 0, scope: null, expanded: false, ...extra };
}

/** Navega como lo haría el router (pushState + popstate). */
export function goto(window, path) {
  window.history.pushState({}, "", path);
  window.dispatchEvent(new window.Event("popstate"));
}

export function click(node) {
  node.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
}

export async function waitFor(predicate, { timeout = 2000, interval = 10 } = {}) {
  const started = Date.now();
  while (Date.now() - started < timeout) {
    if (predicate()) return true;
    await sleep(interval);
  }
  return false;
}
