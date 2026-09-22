import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import { click, goto, jsonResponse, page, setupDom, sleep, waitFor } from "./dom_env.mjs";

const window = setupDom();
window.localStorage.setItem("pyckle_access_token", "test-token");

const counts = { readAll: 0 };
let notifications = [
  {
    id: "n1",
    type: "system",
    title: "Aviso de prueba",
    body: "Contenido",
    data: null,
    is_read: false,
    created_at: "2026-01-01T00:00:00Z",
  },
];

const me = {
  user: {
    id: "u1",
    email: "demo@pyckle.dev",
    full_name: "Demo Cliente",
    phone: "+51999123456",
    is_active: true,
    is_verified: true,
    created_at: "2026-01-01T00:00:00Z",
    roles: [
      { id: "r1", name: "customer" },
      { id: "r2", name: "admin" },
    ],
  },
  customer_profile: {
    id: "cp1",
    address: "Av. Demo 1",
    district: "José Leonardo Ortiz",
    city: "Lambayeque",
    department_id: "d1",
    province_id: "p1",
    district_id: "x1",
    department_name: "Lambayeque",
    province_name: "Chiclayo",
    district_name: "José Leonardo Ortiz",
  },
  technician_id: null,
  permissions: ["admin:users"],
};

function requestItem(title) {
  return {
    id: `req-${title}`,
    title,
    description: "Solicitud de prueba",
    status: "open",
    modality: "home",
    address: null,
    district_name: "José Leonardo Ortiz",
    province_name: "Chiclayo",
    department_name: "Lambayeque",
    specialty: { id: "s1", name: "Laptops", slug: "laptops", is_active: true },
    customer: { id: "u1", full_name: "Demo Cliente" },
    assigned_technician: null,
    images: [],
    created_at: "2026-01-02T00:00:00Z",
    updated_at: "2026-01-02T00:00:00Z",
  };
}

const SLOW_TITLE = "LISTA LENTA";
const FAST_TITLE = "LISTA RAPIDA";

const SPECIALTIES = [
  { id: "s1", name: "Celulares", slug: "celulares", description: null, is_active: true },
  { id: "s2", name: "Computadoras de escritorio", slug: "computadoras-de-escritorio", description: null, is_active: true },
  { id: "s3", name: "Consolas", slug: "consolas", description: null, is_active: true },
  { id: "s4", name: "Impresoras", slug: "impresoras", description: null, is_active: true },
  { id: "s5", name: "Laptops", slug: "laptops", description: null, is_active: true },
  { id: "s6", name: "Tablets", slug: "tablets", description: null, is_active: true },
  { id: "s7", name: "Televisores", slug: "televisores", description: null, is_active: true },
];

const userItem = {
  id: "u1",
  email: "demo@pyckle.dev",
  full_name: "Demo Cliente",
  phone: "+51999123456",
  is_active: true,
  is_verified: true,
  created_at: "2026-01-01T00:00:00Z",
  roles: [{ id: "r1", name: "customer" }],
};

globalThis.fetch = async (url, options = {}) => {
  const target = String(url).replace("http://localhost", "");
  const method = (options.method || "GET").toUpperCase();

  if (target.includes("/notifications/read-all") && method === "POST") {
    counts.readAll += 1;
    notifications = notifications.map((item) => ({ ...item, is_read: true }));
    return jsonResponse({ updated: 1, unread: 0 });
  }
  if (target.startsWith("/api/v1/auth/me")) return jsonResponse(me);
  if (target.startsWith("/api/v1/ws/ticket")) return jsonResponse({ ticket: "test-ticket", expires_in: 60 });
  if (target.startsWith("/api/v1/notifications?limit=20")) return jsonResponse(notifications);
  if (target.startsWith("/api/v1/specialties")) return jsonResponse(SPECIALTIES);
  if (target.includes("/admin/requests?limit=50")) {
    await sleep(300);
    return jsonResponse(page([requestItem(SLOW_TITLE)]));
  }
  if (target.includes("/repair-requests?limit=50")) {
    await sleep(300);
    return jsonResponse(page([requestItem(SLOW_TITLE)]));
  }
  if (target.includes("/repair-requests?limit=5")) return jsonResponse(page([requestItem(FAST_TITLE)]));
  if (target.includes("/repair-requests/available?limit=5")) {
    return jsonResponse(page([requestItem(FAST_TITLE)]));
  }
  if (target.includes("/orders?limit=5")) return jsonResponse(page([]));
  if (target.includes("/orders?limit=50")) return jsonResponse(page([]));
  if (target.startsWith("/api/v1/conversations")) return jsonResponse([]);
  if (target.startsWith("/api/v1/quotations/mine")) return jsonResponse([]);
  if (target.startsWith("/api/v1/technicians/me/stats")) {
    return jsonResponse({ active_orders: 1, completed_orders: 2, total_earnings: "150.00", pending_quotations: 1 });
  }
  if (target.startsWith("/api/v1/technicians/me")) {
    return jsonResponse({
      id: "t1",
      user: { id: "u1", full_name: "Demo Cliente" },
      bio: null,
      experience_years: 3,
      is_verified: true,
      offers_home_service: true,
      offers_workshop_service: false,
      workshop_address: null,
      department_id: "d1",
      province_id: "p1",
      district_id: "x1",
      department_name: "Lambayeque",
      province_name: "Chiclayo",
      district_name: "José Leonardo Ortiz",
      rating_avg: "4.5",
      rating_count: 2,
      specialties: [],
      created_at: "2026-01-01T00:00:00Z",
    });
  }
  if (target.startsWith("/api/v1/geo/departments/d1/provinces")) {
    return jsonResponse([{ id: "p1", code: "1401", name: "Chiclayo", department_id: "d1" }]);
  }
  if (target.startsWith("/api/v1/geo/provinces/p1/districts")) {
    return jsonResponse([{ id: "x1", code: "140105", name: "José Leonardo Ortiz", province_id: "p1", department_id: "d1" }]);
  }
  if (target.startsWith("/api/v1/geo/departments")) {
    return jsonResponse([{ id: "d1", code: "14", name: "Lambayeque" }]);
  }
  if (target.startsWith("/api/v1/admin/stats")) {
    return jsonResponse({
      total_users: 1,
      total_customers: 1,
      total_technicians: 0,
      total_requests: 0,
      open_requests: 0,
      total_orders: 0,
      completed_orders: 0,
      total_revenue: "0.00",
      requests_by_status: {},
    });
  }
  if (target.startsWith("/api/v1/admin/roles")) {
    return jsonResponse([{ id: "r1", name: "admin", description: null }]);
  }
  if (target.startsWith("/api/v1/admin/specialties")) return jsonResponse([]);
  if (target.includes("/admin/users?limit=50")) return jsonResponse(page([userItem]));
  if (target.includes("/admin/technicians?limit=50")) return jsonResponse(page([]));
  if (target.includes("/admin/requests?limit=8")) return jsonResponse(page([]));
  if (target.includes("/admin/orders?limit=8")) return jsonResponse(page([]));
  if (target.includes("/technicians?limit=50")) return jsonResponse(page([]));
  return jsonResponse({});
};

const assetsDir = fileURLToPath(new URL("../dist/assets/", import.meta.url));
const asset = readdirSync(assetsDir).find((name) => name.endsWith(".js"));
await import(pathToFileURL(path.join(assetsDir, asset)).href);

await waitFor(() => (window.document.querySelector("#view")?.textContent || "").includes("Repara"));
await sleep(30);

test("la navbar y el footer persisten entre navegaciones", async () => {
  const header = window.document.querySelector("header");
  const footer = window.document.querySelector("footer");

  goto(window, "/dashboard");
  await sleep(60);
  goto(window, "/requests");
  await sleep(60);

  assert.equal(window.document.querySelector("header"), header);
  assert.equal(window.document.querySelector("footer"), footer);
});

test("una respuesta lenta anterior no sobrescribe la navegación vigente", async () => {
  goto(window, "/requests");
  await sleep(30);
  goto(window, "/dashboard");
  await sleep(450);

  const text = window.document.querySelector("#view").textContent;
  assert.match(text, /Hola, Demo/);
  assert.match(text, new RegExp(FAST_TITLE));
  assert.doesNotMatch(text, new RegExp(SLOW_TITLE));
});

test("el caso inverso también respeta la navegación vigente", async () => {
  goto(window, "/dashboard");
  await sleep(30);
  goto(window, "/requests");
  await sleep(450);

  const text = window.document.querySelector("#view").textContent;
  assert.match(text, new RegExp(SLOW_TITLE));
  assert.doesNotMatch(text, /Hola, Demo/);
});

test("tras varias navegaciones, marcar como leídas dispara una sola petición", async () => {
  for (const route of ["/dashboard", "/requests", "/", "/dashboard", "/requests", "/dashboard"]) {
    goto(window, route);
    await sleep(50);
  }
  counts.readAll = 0;

  click(window.document.querySelector('button[aria-label="Notificaciones"]'));
  await sleep(20);
  const panel = window.document.querySelector("[data-notif-panel]");
  assert.ok(panel, "el panel de notificaciones debe existir");
  const markAll = [...panel.querySelectorAll("button")].find((node) =>
    node.textContent.includes("Marcar todas"),
  );
  assert.ok(markAll, "debe existir el botón de marcar todas como leídas");

  click(markAll);
  await sleep(80);
  assert.equal(counts.readAll, 1);
});

test("un modal abierto se cierra al navegar", async () => {
  goto(window, "/admin/users");
  await waitFor(() => (window.document.querySelector("#view")?.textContent || "").includes("Gestión de usuarios"));
  const edit = [...window.document.querySelectorAll("button")].find((node) =>
    node.textContent.includes("Editar"),
  );
  assert.ok(edit, "debe existir el botón Editar");
  click(edit);
  await sleep(20);
  assert.equal(window.document.querySelectorAll("[data-modal]").length, 1);

  goto(window, "/dashboard");
  await sleep(120);
  assert.equal(window.document.querySelectorAll("[data-modal]").length, 0);
});

test("todas las rutas renderizan sin errores", async () => {
  const routes = [
    "/",
    "/login",
    "/register",
    "/dashboard",
    "/technician",
    "/requests",
    "/requests/new",
    "/chat",
    "/orders",
    "/technicians",
    "/profile/customer",
    "/profile/technician",
    "/admin",
    "/admin/users",
    "/legal",
    "/legal/privacy",
    "/legal/terms",
    "/legal/data-treatment",
    "/contact",
    "/ruta-inexistente",
  ];
  for (const route of routes) {
    goto(window, route);
    await waitFor(
      () => !(window.document.querySelector("#view")?.textContent || "").includes("Cargando..."),
      { timeout: 2000 },
    );
    await sleep(40);
    const text = window.document.querySelector("#view").textContent;
    assert.ok(text.length > 0, `${route} no renderizó contenido`);
    assert.doesNotMatch(text, /Ocurrió un error/, `${route} mostró error de página`);
  }
  assert.equal(window.document.querySelectorAll("[data-icon-missing]").length, 0);
  assert.ok(window.document.querySelectorAll("svg.lucide").length > 0);
});

test("la Landing conserva sus tres secciones y ejes alineados", async () => {
  goto(window, "/");
  await waitFor(() => (window.document.querySelector("#view")?.textContent || "").includes("Especialidades disponibles"));
  const view = window.document.querySelector("#view");
  assert.match(view.textContent, /¿Cómo funciona\?/);
  assert.match(view.textContent, /Especialidades disponibles/);
  assert.match(view.textContent, /¿Reparas dispositivos\?/);
  assert.equal(view.querySelectorAll("h2").length, 3);

  const sections = [...view.querySelectorAll(":scope > div > section")];
  const axes = sections.map((section) => {
    const container = section.firstElementChild.getBoundingClientRect();
    return `${Math.round(container.left)}:${Math.round(container.right)}`;
  });
  assert.equal(new Set(axes).size, 1, `ejes distintos: ${axes.join(", ")}`);
});

test("la sección de especialidades muestra 7 categorías informativas con iconos", async () => {
  goto(window, "/");
  await waitFor(() =>
    (window.document.querySelector("#view")?.textContent || "").includes(
      "Selecciona el tipo de equipo",
    ),
  );
  const view = window.document.querySelector("#view");
  const sections = [...view.querySelectorAll(":scope > div > section")];
  // "Especialidades disponibles" también aparece en una tarjeta del hero:
  // localiza la sección por su h2 para no confundirla con esa stat.
  const spec = sections.find((section) =>
    [...section.querySelectorAll("h2")].some(
      (heading) => heading.textContent.trim() === "Especialidades disponibles",
    ),
  );
  assert.ok(spec, "debe existir la sección de especialidades");
  assert.match(
    spec.textContent,
    /Selecciona el tipo de equipo y encuentra técnicos que trabajan con él\./,
  );

  const grid = spec.querySelector("div.flex.flex-wrap.justify-center");
  const tiles = [...grid.children];
  assert.equal(tiles.length, 7);
  assert.deepEqual(
    tiles.map((tile) => tile.querySelector("span:last-child").textContent),
    SPECIALTIES.map((item) => item.name),
  );

  const expectedIcons = [
    "lucide-smartphone",
    "lucide-monitor",
    "lucide-gamepad-2",
    "lucide-printer",
    "lucide-laptop",
    "lucide-tablet",
    "lucide-tv",
  ];
  expectedIcons.forEach((className, index) => {
    assert.ok(tiles[index].querySelector(`svg.${className}`), `falta ${className}`);
  });
  assert.equal(grid.querySelectorAll('[aria-hidden="true"]').length, 7);
  assert.equal(grid.querySelectorAll("button, a").length, 0);
  assert.equal(view.querySelectorAll("[data-icon-missing]").length, 0);
});

test("el layout del footer vive en #app (flex column, outlet flexible)", () => {
  const css = readFileSync(new URL("../src/styles/style.css", import.meta.url), "utf8");
  assert.match(css, /#app\s*\{[^}]*display:\s*flex/s);
  assert.match(css, /#app\s*\{[^}]*flex-direction:\s*column/s);
  assert.match(css, /#app\s*\{[^}]*min-height:\s*100vh/s);
  assert.match(css, /#view\s*\{[^}]*flex:\s*1/s);

  const app = window.document.getElementById("app");
  assert.ok(app.querySelector("header"));
  assert.ok(app.querySelector("#view"));
  assert.ok(app.querySelector("footer"));
});
