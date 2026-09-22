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

import { API_BASE, api, clearTokens, getTokens, setTokens } from "../api/client.js";
import { endpoints } from "../api/endpoints.js";
import { store } from "../state/store.js";

/**
 * URL del endpoint backend que inicia OAuth con Google. El frontend NO conoce
 * ni genera URLs de Google: solo navega a este endpoint de Pyckle.
 */
export function googleAuthUrl(intent = "login") {
  return `${API_BASE}${endpoints.auth.google}?intent=${encodeURIComponent(intent)}`;
}

/**
 * Mensajes para los codigos de error OAuth que el backend puede devolver en
 * el redirect del callback. Los conflictos de correo comparten un unico texto
 * (tradicional y Google); nunca se muestran detalles internos.
 */
const OAUTH_ERROR_MESSAGES = {
  oauth_email_already_registered: "Este correo ya ha sido registrado, prueba con otro",
  oauth_onboarding_expired: "El registro con Google expiró. Intenta nuevamente.",
  oauth_onboarding_invalid: "El registro con Google es inválido. Intenta nuevamente.",
  oauth_exchange_expired: "El inicio de sesión con Google expiró. Intenta nuevamente.",
  oauth_exchange_invalid: "No se pudo completar el inicio de sesión con Google.",
};

export function oauthErrorMessage(code) {
  return (
    OAUTH_ERROR_MESSAGES[code] ||
    "No se pudo completar el inicio de sesión con Google. Intenta nuevamente."
  );
}

export const auth = {
  async googleProviders() {
    try {
      return await api.get(endpoints.auth.providers, { auth: false });
    } catch {
      return { google: false };
    }
  },

  startGoogle(intent = "login") {
    window.location.assign(googleAuthUrl(intent));
  },

  async exchangeOAuth(code) {
    const tokens = await api.post(endpoints.auth.oauthExchange, { code }, { auth: false });
    setTokens(tokens);
    return this.loadMe();
  },

  async oauthOnboarding(oauthToken) {
    return api.post(
      endpoints.auth.oauthOnboarding,
      { oauth_token: oauthToken },
      { auth: false },
    );
  },

  async completeOAuth(payload) {
    const tokens = await api.post(endpoints.auth.oauthComplete, payload, { auth: false });
    setTokens(tokens);
    return this.loadMe();
  },

  async login(email, password) {
    const tokens = await api.post(endpoints.auth.login, { email, password }, { auth: false });
    setTokens(tokens);
    return this.loadMe();
  },

  async register(payload) {
    return api.post(endpoints.auth.register, payload, { auth: false });
  },

  async loadMe() {
    try {
      const me = await api.get(endpoints.auth.me);
      store.setMe(me);
      return me;
    } catch {
      store.setMe(null);
      return null;
    }
  },

  async logout() {
    const { refresh } = getTokens();
    try {
      if (refresh) await api.post(endpoints.auth.logout, { refresh_token: refresh });
    } catch {
      // La sesión local se cierra igual aunque el backend no responda.
    }
    clearTokens();
    store.reset();
    window.dispatchEvent(new CustomEvent("auth:logout"));
  },
};
