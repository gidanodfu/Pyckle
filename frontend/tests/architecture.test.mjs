import assert from "node:assert/strict";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const SRC = fileURLToPath(new URL("../src", import.meta.url));

function walk(dir) {
  return readdirSync(dir).flatMap((name) => {
    const full = path.join(dir, name);
    if (statSync(full).isDirectory()) return walk(full);
    return name.endsWith(".js") ? [full] : [];
  });
}

const files = walk(SRC);

test("la estructura vive en app/ y domains/", () => {
  assert.ok(existsSync(path.join(SRC, "app", "router.js")));
  assert.ok(existsSync(path.join(SRC, "app", "routes.js")));
  assert.ok(existsSync(path.join(SRC, "app", "bootstrap.js")));
  assert.ok(existsSync(path.join(SRC, "domains")));
  assert.ok(!existsSync(path.join(SRC, "pages")));
  assert.ok(!existsSync(path.join(SRC, "components", "ui.js")));
  assert.ok(!existsSync(path.join(SRC, "components", "layout.js")));
});

test("main.js es solo el entrypoint", () => {
  // El encabezado de licencia es un comentario, no código del entrypoint.
  const source = readFileSync(path.join(SRC, "main.js"), "utf8").replace(
    /\/\*[\s\S]*?\*\//g,
    "",
  );
  const lines = source.split("\n").filter((line) => line.trim());
  assert.ok(lines.length <= 6, `main.js tiene ${lines.length} líneas con contenido`);
  assert.doesNotMatch(lines.join("\n"), /addEventListener|fetch\(|render\(|navigate\(/);
});

test("las rutas SPA no están hardcodeadas fuera de paths.js y el router", () => {
  const allowed = new Set([
    path.join(SRC, "lib", "paths.js"),
    path.join(SRC, "main.js"),
    path.join(SRC, "app", "routes.js"),
    path.join(SRC, "app", "router.js"),
  ]);
  const violations = [];
  // Detecta rutas SPA literales en contextos de navegación/atributos, con
  // comillas dobles, simples o template literals. El literal debe empezar por
  // `/` para no marcar identificadores (routes.*, endpoints.*, ws.*), URLs
  // externas, assets ni otros valores que no son rutas del router.
  const pattern =
    /(?:navigate\(|href\s*[:=]|path\s*[:=]|location\.(?:assign|replace)\(\s*|location\.href\s*=)[^;\n]*?["'`](\/[^"'`]*)["'`]/g;
  for (const file of files) {
    if (allowed.has(file)) continue;
    const text = readFileSync(file, "utf8");
    for (const match of text.matchAll(pattern)) {
      if (match[1].startsWith("/api")) continue;
      violations.push(`${path.relative(SRC, file)}: ${match[0]}`);
    }
  }
  assert.deepEqual(violations, []);
});

test("las rutas WebSocket están centralizadas en lib/paths.js", () => {
  // `/ws/ticket` en api/endpoints.js es el endpoint HTTP que emite el ticket,
  // no una ruta de socket; las rutas de socket viven en lib/paths.js.
  const allowed = new Set([
    path.join(SRC, "lib", "paths.js"),
    path.join(SRC, "api", "endpoints.js"),
  ]);
  const violations = [];
  for (const file of files) {
    if (allowed.has(file)) continue;
    const text = readFileSync(file, "utf8");
    for (const match of text.matchAll(/["'`]\/ws\//g)) {
      violations.push(`${path.relative(SRC, file)}: ${match[0]}`);
    }
  }
  assert.deepEqual(violations, []);
});

test("el frontend no implementa OAuth de Google", () => {
  // El frontend solo navega al endpoint backend; nunca habla con Google.
  const forbidden = [
    "google.accounts",
    "accounts.google.com",
    "oauth2.googleapis.com",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_CLIENT_ID",
    "authorization_code",
    "Google Identity",
    "gsi/client",
  ];
  const violations = [];
  for (const file of files) {
    const text = readFileSync(file, "utf8");
    for (const needle of forbidden) {
      if (text.includes(needle)) {
        violations.push(`${path.relative(SRC, file)}: ${needle}`);
      }
    }
  }
  assert.deepEqual(violations, []);
});

test("classList solo recibe tokens individuales (sin cadenas con espacios)", () => {
  // classList.toggle/add/remove exigen UN token; usar toggleClasses para colecciones.
  const pattern = /classList\.(?:toggle|add|remove)\([^)]*[`'"][^`'"]*\s[^`'"]*[`'"]/;
  const violations = [];
  for (const file of files) {
    const lines = readFileSync(file, "utf8").split("\n");
    lines.forEach((line, index) => {
      if (pattern.test(line)) {
        violations.push(`${path.relative(SRC, file)}:${index + 1}: ${line.trim()}`);
      }
    });
  }
  assert.deepEqual(violations, []);
});

test("las llamadas HTTP viven en el cliente centralizado", () => {
  const violations = [];
  for (const file of files) {
    const relative = path.relative(SRC, file);
    if (relative.startsWith("api/")) continue;
    const text = readFileSync(file, "utf8");
    if (/\bfetch\(/.test(text)) violations.push(relative);
  }
  assert.deepEqual(violations, []);
});

test("los métodos api.* usados están definidos en el cliente HTTP", () => {
  // Evita usar api.put/api.delete/etc. sin implementarlos en client.js.
  const clientPath = path.join(SRC, "api", "client.js");
  const clientText = readFileSync(clientPath, "utf8");
  const block = clientText.match(/export const api\s*=\s*{([\s\S]*?)\n};/);
  assert.ok(block, "no se encontró el objeto export const api en client.js");
  const defined = new Set(
    [...block[1].matchAll(/(?:^|\n)\s*([A-Za-z_$][\w$]*)\s*[:,]/g)].map((match) => match[1]),
  );

  const used = new Map();
  for (const file of files) {
    if (file === clientPath) continue;
    const text = readFileSync(file, "utf8");
    for (const match of text.matchAll(/api\.([A-Za-z_$][\w$]*)\s*\(/g)) {
      if (!used.has(match[1])) used.set(match[1], path.relative(SRC, file));
    }
  }

  const missing = [...used.entries()]
    .filter(([method]) => !defined.has(method))
    .map(([method, file]) => `${file}: api.${method} no existe en client.js`);
  assert.deepEqual(missing, []);
});
