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

import assert from "node:assert/strict";
import test from "node:test";

import { createLatestGuard } from "./latest.js";

test("solo el token más reciente queda vigente", () => {
  const guard = createLatestGuard();
  const first = guard.next();
  assert.equal(first(), true);

  const second = guard.next();
  assert.equal(first(), false);
  assert.equal(second(), true);

  guard.invalidate();
  assert.equal(second(), false);
});

test("resultado viejo no puede aplicar sobre una operación posterior", async () => {
  const guard = createLatestGuard();
  const applied = [];
  const load = (name, delay) => {
    const isCurrent = guard.next();
    return new Promise((resolve) => {
      setTimeout(() => {
        if (isCurrent()) applied.push(name);
        resolve();
      }, delay);
    });
  };

  await Promise.all([load("perfil", 30), load("dashboard", 5)]);
  assert.deepEqual(applied, ["dashboard"]);
});

test("cada operación independiente tiene su propia vigencia", () => {
  const listGuard = createLatestGuard();
  const otherGuard = createLatestGuard();
  const list = listGuard.next();
  otherGuard.next();
  assert.equal(list(), true);
});
