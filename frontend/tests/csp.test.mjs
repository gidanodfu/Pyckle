import assert from "node:assert/strict";
import { existsSync, readFileSync } from "node:fs";
import test from "node:test";
import { fileURLToPath } from "node:url";

const indexPath = fileURLToPath(new URL("../index.html", import.meta.url));
const themeInitPath = fileURLToPath(new URL("../public/theme-init.js", import.meta.url));
const distThemeInitPath = fileURLToPath(new URL("../dist/theme-init.js", import.meta.url));
const nginxPath = fileURLToPath(new URL("../../infra/nginx/nginx.prod.conf", import.meta.url));

test("index.html carga el tema como script externo y sin scripts inline", () => {
  const html = readFileSync(indexPath, "utf8");
  assert.match(html, /<script src="\/theme-init\.js"><\/script>/);
  const inline = html.match(/<script(?![^>]*\bsrc=)[^>]*>[\s\S]*?<\/script>/);
  assert.equal(inline, null, "no debe quedar ningún script inline");
});

test("index.html no usa atributos style inline", () => {
  const html = readFileSync(indexPath, "utf8");
  assert.doesNotMatch(html, /\sstyle="/);
});

test("theme-init.js define el arranque del tema y se copia al bundle", () => {
  const source = readFileSync(themeInitPath, "utf8");
  assert.match(source, /pyckle_theme/);
  assert.match(source, /prefers-color-scheme/);
  assert.ok(existsSync(distThemeInitPath), "dist/theme-init.js debe existir tras el build");
});

test(
  "nginx.prod.conf define una CSP Report-Only compatible con la SPA",
  { skip: !existsSync(nginxPath) },
  () => {
    const config = readFileSync(nginxPath, "utf8");
    assert.match(config, /Content-Security-Policy-Report-Only/);
    for (const directive of [
      "default-src 'self'",
      "script-src 'self'",
      "style-src 'self'",
      "object-src 'none'",
      "frame-ancestors 'none'",
      "base-uri 'self'",
      "connect-src 'self'",
    ]) {
      assert.ok(config.includes(directive), `CSP debe incluir: ${directive}`);
    }
    assert.ok(!config.includes("unsafe-eval"), "CSP no debe permitir unsafe-eval");
    assert.ok(!config.includes("unsafe-inline"), "CSP no debe permitir unsafe-inline");
  },
);
