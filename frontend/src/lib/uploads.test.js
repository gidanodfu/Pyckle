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

import { MAX_IMAGE_BYTES, MAX_IMAGE_MB, MAX_IMAGES, validateImageSize } from "./uploads.js";

test("acepta archivos dentro del límite", () => {
  assert.equal(validateImageSize({ name: "ok.png", size: MAX_IMAGE_BYTES }), null);
  assert.equal(validateImageSize({ name: "small.jpg", size: 1024 }), null);
});

test("rechaza archivos por encima del límite", () => {
  const message = validateImageSize({ name: "grande.png", size: MAX_IMAGE_BYTES + 1 });
  assert.match(message, /grande\.png/);
  assert.match(message, /5 MB/);
});

test("las constantes reflejan los límites documentados", () => {
  assert.equal(MAX_IMAGE_MB, 5);
  assert.equal(MAX_IMAGE_BYTES, 5 * 1024 * 1024);
  assert.equal(MAX_IMAGES, 6);
});

test("un archivo nulo no produce error", () => {
  assert.equal(validateImageSize(null), null);
});
