import { useEffect, useState } from "react";

// Folder name (PL frontend) → ISO kod (backend)
const COUNTRY_TO_ISO = {
  "Polska": "PL", "Czechy": "CZ", "Słowacja": "SK", "Słowenia": "SI",
  "Chorwacja": "HR", "Bułgaria": "BG", "Rumunia": "RO", "Mołdawia": "MD",
  "Serbia": "RS", "Litwa": "LT", "Łotwa": "LV", "Estonia": "EE",
  "Francja": "FR",
};

const _urlStatusCache = new Map();

/**
 * useUrlStatus(country) — pobiera mapę {id: statusObj} z /api/url-status.
 *
 * `country` może być nazwą ("Polska") albo ISO ("PL") — mapujemy.
 * "Wszystkie" / pusty → pusty stan, nic nie fetchuje.
 *
 * Returns: { byId, summary, loading, error }
 */
export function useUrlStatus(country, refreshKey = 0) {
  const isAll = !country || country === "Wszystkie";
  const iso = isAll ? null : (COUNTRY_TO_ISO[country] || country);
  const endpoint = isAll
    ? "/api/url-status"
    : `/api/url-status?country=${encodeURIComponent(iso)}`;

  const cached = refreshKey === 0 ? _urlStatusCache.get(endpoint) : null;
  const [data, setData] = useState(() => cached || { byId: {}, summary: null });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (refreshKey === 0 && _urlStatusCache.has(endpoint)) {
      setData(_urlStatusCache.get(endpoint));
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);
    fetch(endpoint)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then((json) => {
        if (cancelled) return;
        const byId = {};
        for (const item of json.items || []) {
          if (!(item.id in byId)) {
            byId[item.id] = {
              status: item.status,
              state: item.state || "unknown",
              http_code: item.http_code,
              error: item.error,
              redirect_url: item.redirect_url,
              response_ms: item.response_ms,
              checked_at: item.checked_at,
              url: item.url,
            };
          }
        }
        const result = { byId, summary: json.summary || null };
        _urlStatusCache.set(endpoint, result);
        setData(result);
      })
      .catch((e) => !cancelled && setError(String(e)))
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [endpoint, refreshKey]);

  return { ...data, loading, error };
}
