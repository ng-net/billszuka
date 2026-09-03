const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").trim().replace(/\/+$/, "");

import { getActiveProfile } from "./auth";

export function apiUrl(path) {
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return API_BASE ? `${API_BASE}${normalized}` : normalized;
}

export function getAuthHeader() {
  const profile = getActiveProfile();
  return profile ? { "X-Billszuka-User": profile } : {};
}

export function authFetch(url, options = {}) {
  const headers = {
    ...getAuthHeader(),
    ...(options.headers || {}),
  };
  return fetch(apiUrl(url), {
    credentials: "include",
    ...options,
    headers,
  });
}
