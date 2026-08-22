/**
 * Typed client for /api/settings/* — manages OpenRouter + Gemini API keys
 * stored server-side in tools/api_secrets.json.
 *
 * IMPORTANT: This client never logs or displays full keys. The server redacts
 * keys before sending responses; we just display the fingerprint.
 */

const BASE = "/api/settings";

async function jsonFetch(path, init = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* not JSON */
    }
    throw new Error(detail);
  }
  return res.json();
}

/**
 * GET /api/settings — returns the redacted vault snapshot.
 * { openrouter: [{alias, fingerprint, created, last_ok, last_err}],
 *   gemini: [...], priority: ["openrouter", "gemini", "mock"] }
 */
export async function fetchSettings() {
  return jsonFetch("");
}

/**
 * POST /api/settings/{provider} — adds a key.
 * provider: "openrouter" | "gemini"
 * body: { alias, key, project? }   (project only for gemini)
 */
export async function addKey(provider, { alias, key, project }) {
  return jsonFetch(`/${provider}`, {
    method: "POST",
    body: JSON.stringify({ alias, key, project }),
  });
}

/**
 * DELETE /api/settings/{provider}/{alias}
 */
export async function deleteKey(provider, alias) {
  return jsonFetch(`/${provider}/${encodeURIComponent(alias)}`, {
    method: "DELETE",
  });
}

/**
 * POST /api/settings/{provider}/{alias}/test — validates the key with the provider.
 * Returns { ok, latency_ms, model?, error? }
 */
export async function testKey(provider, alias) {
  return jsonFetch(`/${provider}/${encodeURIComponent(alias)}/test`, {
    method: "POST",
  });
}

/**
 * PUT /api/settings/priority — reorders the fallback chain.
 * body: { priority: ["openrouter", "gemini", "mock"] }
 */
export async function setPriority(priority) {
  return jsonFetch("/priority", {
    method: "PUT",
    body: JSON.stringify({ priority }),
  });
}

/**
 * Convenience: re-order keys within a provider by "last_ok desc, last_err asc".
 * Backend endpoint: POST /api/settings/rotate-all
 */
export async function rotateAll() {
  return jsonFetch("/rotate-all", { method: "POST" });
}