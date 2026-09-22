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

import { formatPhone, isValidPhone, normalizePhone } from "./phone.js";

test("normaliza formatos equivalentes", () => {
  const expected = "+51999123456";
  for (const raw of [
    "999123456",
    "999 123 456",
    "999-123-456",
    "+51999123456",
    "+51 999 123 456",
    "+51-999-123-456",
    "0051999123456",
    "(+51) 999 123 456",
  ]) {
    assert.equal(normalizePhone(raw), expected, raw);
  }
});

test("rechaza números inválidos", () => {
  for (const raw of ["123456789", "899123456", "99912345", "9991234567", "abc"]) {
    assert.equal(isValidPhone(raw), false, raw);
    assert.throws(() => normalizePhone(raw));
  }
});

test("vacio y nulo devuelven null", () => {
  assert.equal(normalizePhone(null), null);
  assert.equal(normalizePhone("   "), null);
});

test("formatea para mostrar", () => {
  assert.equal(formatPhone("+51999123456"), "+51 999 123 456");
});
