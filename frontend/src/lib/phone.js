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

export const PHONE_ERROR =
  "Ingresa un celular peruano válido de 9 dígitos, por ejemplo +51 999 123 456";

export function normalizePhone(raw) {
  if (raw == null) return null;
  const value = String(raw).trim();
  if (!value) return null;
  let digits = value.replace(/\D/g, "");
  if (digits.startsWith("00")) digits = digits.slice(2);
  if (digits.length > 9 && digits.startsWith("51")) digits = digits.slice(2);
  if (digits.length !== 9 || !digits.startsWith("9")) {
    throw new Error(PHONE_ERROR);
  }
  return `+51${digits}`;
}

export function isValidPhone(raw) {
  try {
    normalizePhone(raw);
    return true;
  } catch {
    return false;
  }
}

export function formatPhone(raw) {
  let canonical;
  try {
    canonical = normalizePhone(raw);
  } catch {
    return raw || "";
  }
  if (!canonical) return "";
  const national = canonical.slice(3);
  return `+51 ${national.slice(0, 3)} ${national.slice(3, 6)} ${national.slice(6)}`;
}
