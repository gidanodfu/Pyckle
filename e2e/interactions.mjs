/*
 * Copyright (C) 2026 Josue David (gidanodfu)
 * https://github.com/gidanodfu
 *
 * This file is part of Pyckle.
 * GNU Affero General Public License v3.0 (see LICENSE).
 *
 * Comprobaciones de interaccion y accesibilidad (no solo render):
 * - Menu movil: abre, cierra con Escape y actualiza aria-expanded.
 * - Modal: focus trap, foco inicial dentro, Escape cierra y restaura foco.
 * - Tema claro/oscuro conmuta.
 * - Toast al marcar notificaciones (requiere al menos una no leida).
 *
 * Uso: QA_DEMO_PASSWORD=... QA_ADMIN_PASSWORD=... node interactions.mjs
 */

import { chromium } from "@playwright/test";

const BASE = process.env.QA_BASE || "http://localhost";
const PW = process.env.QA_DEMO_PASSWORD;
const AP = process.env.QA_ADMIN_PASSWORD;
const results = [];
const rec = (name, pass, detail = "") => {
  results.push({ name, pass, detail });
  console.log(`${pass ? "PASS" : "FAIL"}  ${name}${detail ? " :: " + detail : ""}`);
};

async function login(ctx, email, password) {
  const page = await ctx.newPage();
  await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded" });
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await page.waitForFunction(() => !location.pathname.startsWith("/login"), null, {
    timeout: 15000,
  });
  await page.waitForTimeout(600);
  return page;
}

const browser = await chromium.launch();

// 1) Toast + marcar notificaciones como leidas
{
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await login(ctx, process.env.QA_NOTIF_EMAIL || "demo.customer.003@pyckle.dev", PW);
  await page.click('button[aria-label="Notificaciones"]');
  await page.waitForTimeout(300);
  const btn = page.locator('button:has-text("Marcar todas como leídas")');
  if (await btn.isDisabled()) {
    rec("toast mark-all", false, "botón deshabilitado (sin no leídas)");
  } else {
    await btn.click();
    await page.waitForTimeout(700);
    const toastText = await page.locator("[data-toast-region]").textContent().catch(() => "");
    rec("toast mark-all", /marcadas como leídas/i.test(toastText || ""));
  }
  await ctx.close();
}

// 2) Menu movil + Escape
{
  const ctx = await browser.newContext({ viewport: { width: 375, height: 812 } });
  const page = await login(ctx, "demo.customer.001@pyckle.dev", PW);
  const menu = page.locator('button[aria-controls="main-nav"]');
  await menu.click();
  await page.waitForTimeout(150);
  const open = await page.locator("#main-nav").isVisible();
  const expanded = await menu.getAttribute("aria-expanded");
  await page.keyboard.press("Escape");
  await page.waitForTimeout(150);
  const closed = await page.locator("#main-nav").isHidden();
  const expandedAfter = await menu.getAttribute("aria-expanded");
  rec("menú móvil abre y cierra con Escape", open && expanded === "true" && closed && expandedAfter === "false");
  await ctx.close();
}

// 3) Modal: focus trap + Escape + restauracion
{
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await login(ctx, "admin@pyckle.quokio.com", AP);
  await page.goto(`${BASE}/admin/users`, { waitUntil: "load" });
  await page.waitForTimeout(1200);
  await page.locator('button:has-text("Editar")').first().click();
  await page.waitForTimeout(300);
  const modalCount = await page.locator("[data-modal]").count();
  const focusInModal = await page.evaluate(() => !!document.activeElement?.closest("[data-modal]"));
  for (let i = 0; i < 8; i++) await page.keyboard.press("Tab");
  const stillInModal = await page.evaluate(() => !!document.activeElement?.closest("[data-modal]"));
  await page.keyboard.press("Escape");
  await page.waitForTimeout(300);
  const closedCount = await page.locator("[data-modal]").count();
  const focusRestored = await page.evaluate(() =>
    (document.activeElement?.textContent || "").includes("Editar"),
  );
  rec("modal focus trap + Escape", modalCount === 1 && focusInModal && stillInModal && closedCount === 0);
  rec("modal restaura foco al cerrar", focusRestored);
  await ctx.close();
}

// 4) Tema
{
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await login(ctx, "demo.customer.001@pyckle.dev", PW);
  const before = await page.evaluate(() => document.documentElement.classList.contains("dark"));
  await page.click('button[aria-label="Activar tema oscuro"], button[aria-label="Activar tema claro"]');
  await page.waitForTimeout(200);
  const after = await page.evaluate(() => document.documentElement.classList.contains("dark"));
  rec("theme toggle cambia de modo", before !== after);
  await ctx.close();
}

await browser.close();
const failed = results.filter((r) => !r.pass);
console.log(`\n${results.length - failed.length}/${results.length} PASS`);
process.exit(failed.length ? 1 : 0);
