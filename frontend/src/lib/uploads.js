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
 * Límites de subida de imágenes.
 *
 * Espejo de la configuración del backend (`MAX_UPLOAD_SIZE_MB`,
 * `MAX_IMAGES_PER_REQUEST`). El frontend valida antes de subir como primera
 * barrera de UX; el backend sigue validando como frontera de seguridad.
 */
export const MAX_IMAGE_MB = 5;
export const MAX_IMAGE_BYTES = MAX_IMAGE_MB * 1024 * 1024;
export const MAX_IMAGES = 6;

/** Devuelve un mensaje si el archivo excede el límite; `null` si es válido. */
export function validateImageSize(file) {
  if (!file) return null;
  if (file.size > MAX_IMAGE_BYTES) {
    return `"${file.name}" supera el máximo de ${MAX_IMAGE_MB} MB.`;
  }
  return null;
}
