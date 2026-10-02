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
 * Tema claro/oscuro. La preferencia se guarda en localStorage. Dark es el tema
 * por defecto de Pyckle; solo se aplica light si el usuario lo eligió. Ambos
 * temas comparten los tokens semánticos (ver styles/style.css).
 */
const STORAGE_KEY = "pyckle_theme";

export function isDark() {
  return document.documentElement.classList.contains("dark");
}

export function applyTheme(theme) {
  const dark = theme === "dark";
  document.documentElement.classList.toggle("dark", dark);
  try {
    localStorage.setItem(STORAGE_KEY, dark ? "dark" : "light");
  } catch {
    // Sin almacenamiento (modo privado): el tema aplica solo a esta sesión.
  }
}

export function initTheme() {
  let stored = null;
  try {
    stored = localStorage.getItem(STORAGE_KEY);
  } catch {
    stored = null;
  }
  const dark = stored ? stored === "dark" : true;
  document.documentElement.classList.toggle("dark", dark);
}

export function toggleTheme() {
  applyTheme(isDark() ? "light" : "dark");
  return isDark() ? "dark" : "light";
}
