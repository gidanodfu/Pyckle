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

const state = {
  me: null,
  loaded: false,
  notifications: [],
  unread: 0,
};

const listeners = new Set();

export const store = {
  get: () => state,
  setMe(me) {
    state.me = me;
    state.loaded = true;
    emit();
  },
  reset() {
    state.me = null;
    state.loaded = false;
    state.notifications = [];
    state.unread = 0;
    emit();
  },
  setNotifications(notifications) {
    state.notifications = notifications.slice(0, 50);
    state.unread = state.notifications.filter((item) => !item.is_read).length;
    emit();
  },
  addNotification(notification) {
    if (state.notifications.some((item) => item.id === notification.id)) return;
    state.notifications = [notification, ...state.notifications].slice(0, 50);
    state.unread = state.notifications.filter((item) => !item.is_read).length;
    emit();
  },
  subscribe(listener) {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
};

function emit() {
  for (const listener of listeners) listener(state);
}

export function hasPermission(permission) {
  return (state.me?.permissions || []).includes(permission);
}

export function hasRole(role) {
  return (state.me?.user?.roles || []).some((item) => item.name === role);
}

export function isAuthenticated() {
  return Boolean(state.me);
}
