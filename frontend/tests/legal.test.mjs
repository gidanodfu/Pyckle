import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import { click, goto, jsonResponse, page, setupDom, sleep, waitFor } from "./dom_env.mjs";

const window = setupDom();
const counts = { register: 0 };
let registerBody = null;

globalThis.fetch = async (url, options = {}) => {
  const target = String(url).replace("http://localhost", "");
  const method = (options.method || "GET").toUpperCase();

  if (target.startsWith("/api/v1/auth/register") && method === "POST") {
    counts.register += 1;
    registerBody = JSON.parse(options.body);
    return jsonResponse({ id: "u1", email: registerBody.email, roles: [{ id: "r1", name: "customer" }] }, 201);
  }
  if (target.startsWith("/api/v1/auth/login") && method === "POST") {
    return jsonResponse({ access_token: "a", refresh_token: "r", token_type: "bearer", expires_in: 900 });
  }
  if (target.startsWith("/api/v1/auth/me")) {
    return jsonResponse({ detail: "no auth" }, 401);
  }
  if (target.startsWith("/api/v1/ws/ticket")) {
    return jsonResponse({ ticket: "test-ticket", expires_in: 60 });
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
  if (target.startsWith("/api/v1/specialties")) return jsonResponse([]);
  if (target.startsWith("/api/v1/notifications?limit=20")) return jsonResponse([]);
  if (target.includes("/repair-requests?limit=5")) return jsonResponse(page([]));
  if (target.includes("/orders?limit=5")) return jsonResponse(page([]));
  return jsonResponse({});
};

const assetsDir = fileURLToPath(new URL("../dist/assets/", import.meta.url));
const asset = readdirSync(assetsDir).find((name) => name.endsWith(".js"));
await import(pathToFileURL(path.join(assetsDir, asset)).href);
await waitFor(() => (window.document.querySelector("#view")?.textContent || "").includes("Repara"));

const LEGAL_PAGES = [
  ["/legal", "Información legal"],
  ["/legal/privacy", "Política de Privacidad"],
  ["/legal/terms", "Términos y Condiciones"],
  ["/legal/data-treatment", "Tratamiento de Datos Personales"],
  ["/contact", "Contacto"],
];

test("las páginas legales son públicas y renderizan su contenido", async () => {
  for (const [route, heading] of LEGAL_PAGES) {
    goto(window, route);
    await waitFor(() => {
      const view = window.document.querySelector("#view");
      return view && view.textContent.includes(heading) && !view.textContent.includes("Cargando...");
    });
    const text = window.document.querySelector("#view").textContent;
    assert.ok(text.includes(heading), `${route} no mostró "${heading}"`);
    assert.ok(text.includes("Borrador informativo"), `${route} sin aviso de borrador`);
    assert.equal(window.document.querySelectorAll("[data-icon-missing]").length, 0);
  }
});

test("el footer enlaza los 5 documentos y navega sin recarga", async () => {
  goto(window, "/");
  await waitFor(() => window.document.querySelector('footer nav[aria-label="Enlaces legales"]'));
  const links = [...window.document.querySelectorAll('footer nav[aria-label="Enlaces legales"] a')];
  assert.equal(links.length, 5);
  const hrefs = links.map((link) => link.getAttribute("href"));
  assert.deepEqual(hrefs, [
    "/legal",
    "/legal/privacy",
    "/legal/terms",
    "/legal/data-treatment",
    "/contact",
  ]);

  // Iconos decorativos secundarios: uno por enlace y nunca anunciados dos veces.
  assert.equal(links.filter((link) => link.querySelector('[aria-hidden="true"] svg')).length, 5);
  assert.ok(links.every((link) => link.className.includes("text-sm")));
  assert.ok(links.every((link) => link.className.includes("hover:text-blue-700")));
  assert.ok(links.every((link) => link.className.includes("focus-visible:ring-2")));
  assert.equal(window.document.querySelector("footer").querySelectorAll("[data-icon-missing]").length, 0);

  const footer = window.document.querySelector("footer");
  // La marca se muestra solo como isotipo: el wordmark "Pyckle" no es texto.
  assert.doesNotMatch(footer.textContent, /Pyckle/);
  assert.match(footer.textContent, /Reparación de dispositivos en Perú/);
  assert.match(footer.textContent, new RegExp(String(new Date().getFullYear())));

  const terms = links.find((link) => link.textContent.includes("Términos"));
  click(terms);
  await waitFor(() => window.location.pathname === "/legal/terms");
  await waitFor(() => (window.document.querySelector("#view")?.textContent || "").includes("Términos y Condiciones"));
  assert.equal(window.location.pathname, "/legal/terms");
});

test("el logo oficial aparece en navbar, login, registro y footer", async () => {
  goto(window, "/");
  await waitFor(() => window.document.querySelector('header img[alt="Pyckle"]'));
  const navbarLogo = window.document.querySelector('header img[alt="Pyckle"]');
  assert.ok(navbarLogo.getAttribute("src").includes("Pyckle-256"));
  assert.equal(navbarLogo.getAttribute("width"), "34");

  const footerLogo = window.document.querySelector('footer img[alt="Pyckle"]');
  assert.ok(footerLogo.getAttribute("src").includes("Pyckle-64"));

  goto(window, "/login");
  await waitFor(() => (window.document.querySelector("#view")?.textContent || "").includes("Iniciar sesión"));
  assert.ok(window.document.querySelector('#view img[alt="Pyckle"]'));

  goto(window, "/register");
  await waitFor(() => (window.document.querySelector("#view")?.textContent || "").includes("Crear cuenta"));
  assert.ok(window.document.querySelector('#view img[alt="Pyckle"]'));
});

test("el registro exige aceptar los Términos y Condiciones", async () => {
  counts.register = 0;
  registerBody = null;

  goto(window, "/register");
  await waitFor(() => (window.document.querySelector("#view")?.textContent || "").includes("Crear cuenta"));
  await waitFor(
    () => (window.document.querySelector('select[name="department_id"]')?.options.length || 0) > 1,
  );

  const form = window.document.querySelector("#view form");
  const department = form.querySelector('select[name="department_id"]');
  department.value = "d1";
  department.dispatchEvent(new window.Event("change"));
  await waitFor(() => (form.querySelector('select[name="province_id"]')?.options.length || 0) > 1);
  const province = form.querySelector('select[name="province_id"]');
  province.value = "p1";
  province.dispatchEvent(new window.Event("change"));
  await waitFor(() => (form.querySelector('select[name="district_id"]')?.options.length || 0) > 1);
  form.querySelector('select[name="district_id"]').value = "x1";

  form.querySelector('input[name="full_name"]').value = "Términos Prueba";
  form.querySelector('input[name="email"]').value = "terms@test.dev";
  form.querySelector('input[name="phone"]').value = "+51 999 111 222";
  form.querySelector('input[name="password"]').value = "password12345";

  const termsLink = form.querySelector('a[href="/legal/terms"]');
  assert.ok(termsLink, "debe existir el enlace a Términos");
  assert.equal(termsLink.getAttribute("target"), "_blank");
  assert.equal(termsLink.hasAttribute("data-link"), false);

  form.dispatchEvent(new window.Event("submit", { bubbles: true, cancelable: true }));
  await sleep(40);
  const error = window.document.getElementById("register-terms-error");
  assert.ok(!error.classList.contains("hidden"), "debe mostrarse el error de términos");
  assert.equal(counts.register, 0, "no debe registrar sin aceptar");
  assert.equal(form.querySelector('input[name="email"]').value, "terms@test.dev", "el formulario no se pierde");

  const checkbox = form.querySelector('input[name="terms"]');
  checkbox.checked = true;
  checkbox.dispatchEvent(new window.Event("change"));
  form.dispatchEvent(new window.Event("submit", { bubbles: true, cancelable: true }));
  await waitFor(() => counts.register === 1);
  assert.equal(registerBody.accept_terms, true);
  await sleep(60);
});
