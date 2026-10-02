/*
 * Copyright (C) 2026 Josue David (gidanodfu)
 * https://github.com/gidanodfu
 *
 * This file is part of Pyckle.
 * GNU Affero General Public License v3.0 (see LICENSE).
 *
 * Auditoría de accesibilidad con axe-core sobre las páginas reales, en dark y
 * light. Registra violaciones por página e impacto. Devuelve código != 0 si hay
 * violaciones critical/serious.
 *
 * Uso: QA_DEMO_PASSWORD=... QA_ADMIN_PASSWORD=... node a11y.mjs
 */

import { chromium } from "@playwright/test";
import { AxeBuilder } from "@axe-core/playwright";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const BASE = process.env.QA_BASE || "http://localhost";
const OUT = join(dirname(fileURLToPath(import.meta.url)), "artifacts", "a11y");
const PW = process.env.QA_DEMO_PASSWORD;

const ROUTES = [
  { role: "public", path: "/" },
  { role: "public", path: "/login" },
  { role: "public", path: "/register" },
  { role: "public", path: "/technicians" },
  { role: "public", path: "/legal" },
  { role: "public", path: "/contact" },
  { role: "customer", path: "/dashboard" },
  { role: "customer", path: "/requests" },
  { role: "customer", path: process.env.QA_REQUEST_ID ? `/requests/${process.env.QA_REQUEST_ID}` : null },
  { role: "customer", path: "/orders" },
  { role: "customer", path: process.env.QA_ORDER_ID ? `/orders/${process.env.QA_ORDER_ID}` : null },
  { role: "customer", path: "/chat" },
  { role: "customer", path: "/profile/customer" },
  { role: "technician", path: "/technician" },
  { role: "technician", path: "/technician/repairs" },
  { role: "technician", path: "/profile/technician" },
  { role: "admin", path: "/admin" },
  { role: "admin", path: "/admin/users" },
].filter((r) => r.path);

const CREDS = {
  customer: { email: "demo.customer.001@pyckle.dev", password: PW },
  technician: { email: "demo.technician.002@pyckle.dev", password: PW },
  admin: { email: "admin@pyckle.quokio.com", password: process.env.QA_ADMIN_PASSWORD },
};

async function login(context, email, password) {
  const page = await context.newPage();
  await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForFunction(() => !location.pathname.startsWith("/login"), null, { timeout: 15000 });
  await page.waitForTimeout(400);
  const state = await context.storageState();
  await page.close();
  return state;
}

const browser = await chromium.launch();
mkdirSync(OUT, { recursive: true });
const storage = {};
for (const [role, creds] of Object.entries(CREDS)) {
  const ctx = await browser.newContext();
  storage[role] = await login(ctx, creds.email, creds.password);
  await ctx.close();
}

const report = [];
for (const theme of ["dark", "light"]) {
  for (const { role, path } of ROUTES) {
    const context = await browser.newContext({
      viewport: { width: 1280, height: 900 },
      storageState: role === "public" ? undefined : storage[role],
    });
    await context.addInitScript((t) => {
      try {
        localStorage.setItem("pyckle_theme", t);
      } catch {}
    }, theme);
    const page = await context.newPage();
    await page.goto(`${BASE}${path}`, { waitUntil: "load", timeout: 20000 });
    await page.waitForTimeout(900);
    let violations = [];
    try {
      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
        .analyze();
      violations = results.violations.map((v) => ({
        id: v.id,
        impact: v.impact,
        help: v.help,
        nodes: v.nodes.length,
        target: v.nodes[0]?.target?.join(" ") || "",
      }));
    } catch (error) {
      violations = [{ id: "axe-error", impact: "serious", help: String(error.message).slice(0, 120), nodes: 0, target: "" }];
    }
    report.push({ theme, role, path, violations });
    const summary = violations.length
      ? violations.map((v) => `${v.id}(${v.impact},${v.nodes})`).join(" ")
      : "ok";
    console.log(`${theme.padEnd(5)} ${role.padEnd(10)} ${path.padEnd(30)} ${summary}`);
    await context.close();
  }
}

await browser.close();
writeFileSync(join(OUT, "report.json"), JSON.stringify(report, null, 2));
const blocking = report.filter((r) =>
  r.violations.some((v) => v.impact === "critical" || v.impact === "serious"),
);
console.log(`\nPáginas con violaciones critical/serious: ${blocking.length}/${report.length}`);
process.exit(blocking.length ? 1 : 0);
