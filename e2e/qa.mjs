/*
 * Copyright (C) 2026 Josue David (gidanodfu)
 * https://github.com/gidanodfu
 *
 * This file is part of Pyckle.
 * GNU Affero General Public License v3.0 (see LICENSE).
 *
 * QA de navegador de Pyckle con Playwright + Chromium.
 *
 * Recorre las rutas reales de la SPA por rol (publico/cliente/tecnico/admin) en
 * los seis viewports objetivo y registra errores de consola, pageerrors, fallos
 * de red, respuestas HTTP >=400, overflow horizontal, iconos faltantes y
 * screenshots. Escribe un report.json y devuelve codigo != 0 si hay hallazgos.
 *
 * Uso:
 *   cd e2e && npm install && npx playwright install chromium
 *   QA_DEMO_PASSWORD=... QA_ADMIN_PASSWORD=... \
 *   QA_REQUEST_ID=... QA_ORDER_ID=... QA_TECH_ID=... \
 *   npm run qa
 *   QA_DARK=1 npm run qa            # valida dark mode
 *   QA_VIEWPORTS=375x812 npm run qa # subconjunto de viewports
 *
 * Requiere el stack levantado en QA_BASE (por defecto http://localhost).
 * Nunca imprime secretos: las credenciales llegan por variables de entorno.
 */

import { chromium } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const BASE = process.env.QA_BASE || "http://localhost";
const OUT =
  process.env.QA_OUT ||
  join(dirname(fileURLToPath(import.meta.url)), "artifacts", process.env.QA_LABEL || "run");
const PW = process.env.QA_DEMO_PASSWORD;

const ALL_VIEWPORTS = [
  { name: "375x812", width: 375, height: 812 },
  { name: "390x844", width: 390, height: 844 },
  { name: "768x1024", width: 768, height: 1024 },
  { name: "1024x768", width: 1024, height: 768 },
  { name: "1440x900", width: 1440, height: 900 },
  { name: "1920x1080", width: 1920, height: 1080 },
];
const VIEWPORTS = process.env.QA_VIEWPORTS
  ? ALL_VIEWPORTS.filter((v) => process.env.QA_VIEWPORTS.split(",").includes(v.name))
  : ALL_VIEWPORTS;

const ROLES = [
  { role: "public", email: null, password: null },
  {
    role: "customer",
    email: process.env.QA_CUSTOMER_EMAIL || "demo.customer.001@pyckle.dev",
    password: PW,
    routes: [
      "/dashboard",
      "/requests",
      "/requests/new",
      process.env.QA_REQUEST_ID ? `/requests/${process.env.QA_REQUEST_ID}` : null,
      "/orders",
      process.env.QA_ORDER_ID ? `/orders/${process.env.QA_ORDER_ID}` : null,
      "/chat",
      "/profile/customer",
    ],
  },
  {
    role: "technician",
    email: process.env.QA_TECH_EMAIL || "demo.technician.002@pyckle.dev",
    password: PW,
    routes: [
      "/technician",
      "/technician/repairs",
      "/technician/quotations",
      "/technician/reports",
      "/profile/technician",
      "/requests",
    ],
  },
  {
    role: "admin",
    email: process.env.QA_ADMIN_EMAIL || "admin@pyckle.quokio.com",
    password: process.env.QA_ADMIN_PASSWORD,
    routes: ["/admin", "/admin/users", "/admin/orders"],
  },
];

const PUBLIC_ROUTES = [
  "/",
  "/login",
  "/register",
  "/technicians",
  process.env.QA_TECH_ID ? `/technicians/${process.env.QA_TECH_ID}` : null,
  "/legal",
  "/legal/privacy",
  "/legal/terms",
  "/legal/data-treatment",
  "/contact",
  "/ruta-inexistente",
];

function slug(route) {
  return route === "/" ? "home" : route.replace(/^\//, "").replace(/[^a-z0-9]+/gi, "_");
}

async function login(context, email, password) {
  const page = await context.newPage();
  await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForFunction(() => !location.pathname.startsWith("/login"), null, {
    timeout: 15000,
  });
  await page.waitForTimeout(500);
  const state = await context.storageState();
  await page.close();
  return state;
}

async function auditRoute(browser, storageState, route, vp) {
  const context = await browser.newContext({
    viewport: { width: vp.width, height: vp.height },
    storageState,
  });
  if (process.env.QA_DARK) {
    await context.addInitScript(() => {
      try {
        localStorage.setItem("pyckle_theme", "dark");
      } catch {}
    });
  }
  if (process.env.QA_THEME) {
    const theme = process.env.QA_THEME;
    await context.addInitScript((t) => {
      try {
        localStorage.setItem("pyckle_theme", t);
      } catch {}
    }, theme);
  }
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  const failedRequests = [];
  const badResponses = [];
  page.on("console", (m) => {
    if (m.type() === "error") consoleErrors.push(m.text().slice(0, 400));
  });
  page.on("pageerror", (e) => pageErrors.push(String(e.message || e).slice(0, 400)));
  page.on("requestfailed", (r) => {
    const f = r.failure();
    failedRequests.push(`${r.method()} ${r.url()} :: ${f ? f.errorText : "?"}`);
  });
  page.on("response", (r) => {
    if (r.status() >= 400) badResponses.push(`${r.status()} ${r.request().method()} ${r.url()}`);
  });

  let loadError = null;
  try {
    await page.goto(`${BASE}${route}`, { waitUntil: "load", timeout: 20000 });
    await page
      .waitForFunction(
        () => {
          const v = document.querySelector("#view");
          return v && v.textContent && !v.textContent.includes("Cargando...");
        },
        null,
        { timeout: 12000 },
      )
      .catch(() => {});
    await page.waitForTimeout(700);
  } catch (e) {
    loadError = String(e.message || e).slice(0, 300);
  }

  const metrics = await page.evaluate(() => {
    const de = document.documentElement;
    const overflow = de.scrollWidth - window.innerWidth;
    let worst = null;
    if (overflow > 1) {
      for (const el of document.querySelectorAll("body *")) {
        const r = el.getBoundingClientRect();
        if (r.right > window.innerWidth + 1 && r.width > 40) {
          const cls = (el.className && String(el.className).slice(0, 60)) || el.tagName;
          worst = { tag: el.tagName, cls, right: Math.round(r.right) };
          break;
        }
      }
    }
    return {
      title: document.title,
      viewLen: (document.querySelector("#view")?.textContent || "").trim().length,
      overflow,
      worst,
      missingIcons: document.querySelectorAll("[data-icon-missing]").length,
    };
  });

  const shotDir = join(OUT, "shots", slug(vp.name));
  mkdirSync(shotDir, { recursive: true });
  const fullPage = vp.width <= 390 || vp.width >= 1440;
  if (process.env.QA_SHOTS !== "0") {
    try {
      await page.screenshot({ path: join(shotDir, `${slug(route)}.png`), fullPage });
    } catch {}
  }

  await context.close();
  return {
    route,
    viewport: vp.name,
    ...metrics,
    pageErrors,
    consoleErrors,
    failedRequests,
    badResponses,
    loadError,
  };
}

const browser = await chromium.launch();
mkdirSync(OUT, { recursive: true });
const results = [];
const storageByRole = {};

for (const r of ROLES) {
  if (!r.email) continue;
  const ctx = await browser.newContext();
  try {
    storageByRole[r.role] = await login(ctx, r.email, r.password);
    console.log(`login ${r.role}: OK`);
  } catch (e) {
    console.log(`login ${r.role}: FAIL ${e.message.split("\n")[0]}`);
  }
  await ctx.close();
}

for (const r of ROLES) {
  const routes = (r.role === "public" ? PUBLIC_ROUTES : r.routes || []).filter(Boolean);
  const storageState = r.role === "public" ? undefined : storageByRole[r.role];
  if (r.role !== "public" && !storageState) {
    console.log(`skip ${r.role}: no session`);
    continue;
  }
  for (const vp of VIEWPORTS) {
    for (const route of routes) {
      const res = await auditRoute(browser, storageState, route, vp);
      res.role = r.role;
      results.push(res);
      const flags = [];
      if (res.pageErrors.length) flags.push(`pageerr:${res.pageErrors.length}`);
      if (res.consoleErrors.length) flags.push(`console:${res.consoleErrors.length}`);
      if (res.badResponses.length) flags.push(`http:${res.badResponses.length}`);
      if (res.failedRequests.length) flags.push(`reqfail:${res.failedRequests.length}`);
      if (res.overflow > 1) flags.push(`overflow:${res.overflow}`);
      if (res.missingIcons) flags.push(`icons:${res.missingIcons}`);
      console.log(`${r.role.padEnd(10)} ${vp.name.padEnd(9)} ${route.padEnd(34)} ${flags.join(" ") || "ok"}`);
    }
  }
}

await browser.close();
writeFileSync(join(OUT, "report.json"), JSON.stringify(results, null, 2));
const bad = results.filter(
  (r) =>
    r.pageErrors.length ||
    r.consoleErrors.length ||
    r.badResponses.length ||
    r.failedRequests.length ||
    r.overflow > 1 ||
    r.missingIcons,
);
console.log(`\nTOTAL ${results.length} page loads; with findings: ${bad.length}`);
console.log(`Report: ${join(OUT, "report.json")}`);
process.exit(bad.length ? 1 : 0);
