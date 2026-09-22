import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import { goto, jsonResponse, page, setupDom, sleep, waitFor } from "./dom_env.mjs";

const window = setupDom();

const calls = { providers: 0, onboarding: 0, complete: 0, register: 0, login: 0 };
let googleEnabled = true;
let onboardingResponse = () =>
  jsonResponse({ email: "google@test.dev", full_name: "Google Test", provider: "google" });
let registerResponse = () =>
  jsonResponse({ id: "u1", email: "x@test.dev", roles: [{ id: "r1", name: "customer" }] }, 201);
let lastOnboardingUrl = null;
let lastOnboardingBody = null;
let lastRegisterBody = null;

const tokens = { access_token: "a", refresh_token: "r", token_type: "bearer", expires_in: 900 };

globalThis.fetch = async (url, options = {}) => {
  const target = String(url).replace("http://localhost", "");
  const method = (options.method || "GET").toUpperCase();

  if (target.startsWith("/api/v1/auth/providers")) {
    calls.providers += 1;
    return jsonResponse({ google: googleEnabled });
  }
  if (target.startsWith("/api/v1/auth/oauth/onboarding") && method === "POST") {
    calls.onboarding += 1;
    lastOnboardingUrl = target;
    lastOnboardingBody = JSON.parse(options.body);
    return onboardingResponse();
  }
  if (target.startsWith("/api/v1/auth/oauth/complete") && method === "POST") {
    calls.complete += 1;
    return jsonResponse(tokens);
  }
  if (target.startsWith("/api/v1/auth/register") && method === "POST") {
    calls.register += 1;
    lastRegisterBody = JSON.parse(options.body);
    return registerResponse();
  }
  if (target.startsWith("/api/v1/auth/login") && method === "POST") {
    calls.login += 1;
    return jsonResponse(tokens);
  }
  if (target.startsWith("/api/v1/auth/me")) return jsonResponse({ detail: "no auth" }, 401);
  if (target.startsWith("/api/v1/ws/ticket")) {
    return jsonResponse({ ticket: "t", expires_in: 60 });
  }
  if (target.startsWith("/api/v1/notifications")) return jsonResponse([]);
  if (target.startsWith("/api/v1/geo/departments/d1/provinces")) {
    return jsonResponse([{ id: "p1", code: "1401", name: "Chiclayo", department_id: "d1" }]);
  }
  if (target.startsWith("/api/v1/geo/provinces/p1/districts")) {
    return jsonResponse([
      { id: "x1", code: "140105", name: "José Leonardo Ortiz", province_id: "p1", department_id: "d1" },
    ]);
  }
  if (target.startsWith("/api/v1/geo/departments")) {
    return jsonResponse([{ id: "d1", code: "14", name: "Lambayeque" }]);
  }
  if (target.startsWith("/api/v1/specialties")) return jsonResponse([]);
  if (target.includes("/repair-requests?limit=5")) return jsonResponse(page([]));
  if (target.includes("/orders?limit=5")) return jsonResponse(page([]));
  return jsonResponse({});
};

const assetsDir = fileURLToPath(new URL("../dist/assets/", import.meta.url));
const asset = readdirSync(assetsDir).find((name) => name.endsWith(".js"));
await import(pathToFileURL(path.join(assetsDir, asset)).href);

const { googleAuthUrl } = await import("../src/services/auth.js");

function view() {
  return window.document.querySelector("#view");
}

function resetCalls() {
  for (const key of Object.keys(calls)) calls[key] = 0;
  lastOnboardingUrl = null;
  lastOnboardingBody = null;
  lastRegisterBody = null;
  onboardingResponse = () =>
    jsonResponse({ email: "google@test.dev", full_name: "Google Test", provider: "google" });
  registerResponse = () =>
    jsonResponse({ id: "u1", email: "x@test.dev", roles: [{ id: "r1", name: "customer" }] }, 201);
}

async function waitForView(text) {
  return waitFor(() => (view()?.textContent || "").includes(text));
}

async function fillTraditionalRegister() {
  await waitFor(
    () => (view().querySelector('select[name="department_id"]')?.options.length || 0) > 1,
  );
  const form = view().querySelector("form");
  const department = form.querySelector('select[name="department_id"]');
  department.value = "d1";
  department.dispatchEvent(new window.Event("change"));
  await waitFor(() => (form.querySelector('select[name="province_id"]')?.options.length || 0) > 1);
  const province = form.querySelector('select[name="province_id"]');
  province.value = "p1";
  province.dispatchEvent(new window.Event("change"));
  await waitFor(() => (form.querySelector('select[name="district_id"]')?.options.length || 0) > 1);
  form.querySelector('select[name="district_id"]').value = "x1";
  form.querySelector('input[name="full_name"]').value = "Prueba Registro";
  form.querySelector('input[name="email"]').value = "x@test.dev";
  form.querySelector('input[name="phone"]').value = "+51 999 111 222";
  form.querySelector('input[name="password"]').value = "password12345";
  const checkbox = form.querySelector('input[name="terms"]');
  checkbox.checked = true;
  checkbox.dispatchEvent(new window.Event("change"));
  return form;
}

test("googleAuthUrl apunta al endpoint backend de Pyckle (no a Google)", () => {
  assert.equal(googleAuthUrl("login"), "/api/v1/auth/google?intent=login");
  assert.equal(googleAuthUrl("register"), "/api/v1/auth/google?intent=register");
  assert.doesNotMatch(googleAuthUrl("login"), /google\.com/);
});

test("login muestra el botón de Google cuando el backend lo habilita", async () => {
  googleEnabled = true;
  goto(window, "/login");
  await waitForView("Continuar con Google");
  const button = [...window.document.querySelectorAll("button")].find((node) =>
    node.textContent.includes("Continuar con Google"),
  );
  assert.ok(button, "debe existir el botón de Google");
  const paths = button.querySelectorAll("svg path");
  assert.equal(paths.length, 4, "el icono debe ser la G multicolor (4 paths)");
  const fills = [...paths].map((node) => node.getAttribute("fill"));
  assert.ok(fills.includes("#4285F4") && fills.includes("#EA4335"));
});

test("login oculta el botón de Google si el backend lo deshabilita", async () => {
  googleEnabled = false;
  goto(window, "/login");
  await waitForView("Ingresar");
  await sleep(30);
  assert.doesNotMatch(view().textContent, /Continuar con Google/);
  googleEnabled = true;
});

test("register muestra Google arriba y conserva el formulario tradicional", async () => {
  resetCalls();
  goto(window, "/register");
  await waitForView("Crear cuenta con Google");
  await waitFor(() => view().querySelector('input[name="email"]'));

  const nodes = [...view().querySelectorAll("button, input")];
  const googleIndex = nodes.findIndex((node) =>
    node.textContent?.includes("Crear cuenta con Google"),
  );
  const emailIndex = nodes.findIndex((node) => node.getAttribute("name") === "email");
  const nameIndex = nodes.findIndex((node) => node.getAttribute("name") === "full_name");
  assert.ok(googleIndex >= 0, "debe existir el botón de Google");
  assert.ok(emailIndex > googleIndex, "Google debe ir antes del correo");
  assert.ok(nameIndex > googleIndex, "Google debe ir antes del nombre");

  assert.ok(view().querySelector('input[name="password"]'), "el registro tradicional sigue");
});

test("registro tradicional con email duplicado muestra el mensaje", async () => {
  resetCalls();
  registerResponse = () =>
    jsonResponse(
      { detail: "Este correo ya ha sido registrado, prueba con otro", code: "email_already_registered" },
      409,
    );
  goto(window, "/register");
  await waitForView("Crear cuenta");
  const form = await fillTraditionalRegister();
  form.dispatchEvent(new window.Event("submit", { bubbles: true, cancelable: true }));
  await waitForView("Este correo ya ha sido registrado, prueba con otro");
  assert.equal(calls.register, 1);
  assert.equal(calls.login, 0);
  assert.equal(lastRegisterBody.accept_terms, true);
});

test("oauth_token activa onboarding, consulta al backend y muestra el email", async () => {
  resetCalls();
  goto(window, "/register?oauth_token=tok-123");
  await waitForView("Cuenta de Google verificada");
  await waitForView("google@test.dev");

  assert.equal(calls.onboarding, 1, "debe consultar el peek del backend");
  assert.deepEqual(lastOnboardingBody, { oauth_token: "tok-123" });
  assert.doesNotMatch(lastOnboardingUrl, /oauth_token/, "el token no viaja en la URL");
  assert.equal(view().querySelector('input[name="email"]'), null, "el email no es editable");
  assert.equal(view().querySelector('input[name="password"]'), null);
  const googleButtons = [...view().querySelectorAll("button")].filter((node) =>
    node.textContent.includes("Crear cuenta con Google"),
  );
  assert.equal(googleButtons.length, 0, "no debe reaparecer el login con Google");
  assert.match(view().textContent, /Completa tus datos/);
});

test("onboarding con token expirado muestra error y deshabilita el submit", async () => {
  resetCalls();
  onboardingResponse = () =>
    jsonResponse(
      { detail: "El registro con Google expiró. Intenta nuevamente.", code: "oauth_onboarding_expired" },
      400,
    );
  goto(window, "/register?oauth_token=expirado");
  await waitForView("El registro con Google expiró");
  const submit = view().querySelector('button[type="submit"]');
  assert.ok(submit.disabled, "el submit debe quedar deshabilitado");
  assert.equal(view().querySelector('input[name="email"]'), null);
  await waitForView("Reintentar con Google");
});

test("login muestra el error de correo duplicado y limpia la URL", async () => {
  resetCalls();
  goto(window, "/login?oauth_error=oauth_email_already_registered");
  await waitForView("Este correo ya ha sido registrado, prueba con otro");
  assert.equal(window.location.search, "", "oauth_error debe limpiarse");
});

test("el submit de login no se duplica", async () => {
  resetCalls();
  goto(window, "/login");
  await waitForView("Ingresar");
  const form = view().querySelector("form");
  form.querySelector('input[name="email"]').value = "x@test.dev";
  form.querySelector('input[name="password"]').value = "password12345";
  form.dispatchEvent(new window.Event("submit", { bubbles: true, cancelable: true }));
  form.dispatchEvent(new window.Event("submit", { bubbles: true, cancelable: true }));
  await sleep(50);
  assert.equal(calls.login, 1, "un doble submit no debe lanzar dos requests");
});
