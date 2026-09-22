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

/**
 * Guardia de vigencia para operaciones asíncronas.
 *
 * Cada llamada a `next()` invalida los tokens anteriores. Una operación async
 * debe comprobar el chequeo devuelto por `next()` después de cada `await` antes
 * de tocar el DOM: solo la operación más reciente puede aplicar resultados.
 */
export function createLatestGuard() {
  let current = 0;
  return {
    next() {
      current += 1;
      const token = current;
      return () => token === current;
    },
    invalidate() {
      current += 1;
    },
  };
}
