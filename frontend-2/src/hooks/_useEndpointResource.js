import { useEffect, useState } from "react";

/**
 * useEndpointResource — DRY wrapper for the URL-status / keyword-scan hooks.
 * They had been 80% identical: cache by endpoint, fetch JSON, normalise into
 * a { byId, summary } map. Keeping them as one helper keeps cache hygiene
 * and the loading/error lifecycle consistent without copy-paste.
 */

const _urlStatusCache = new Map();
const _keywordScanCache = new Map();

// Folder name (PL frontend) → ISO kod (backend)
const COUNTRY_TO_ISO = {
  "Polska": "PL", "Czechy": "CZ", "Słowacja": "SK", "Słowenia": "SI",
  "Chorwacja": "HR", "Bułgaria": "BG", "Rumunia": "RO", "Mołdawia": "MD",
  "Serbia": "RS", "Litwa": "LT", "Łotwa": "LV", "Estonia": "EE",
  "Francja": "FR",
};

/**
 * @param {string} basePath  "/api/url-status" or "/api/keyword-scan"
 * @param {string} country   "Polska" / "PL" / "Wszystkie" / ""
 * @param {number} refreshKey
 * @param {(item: any) => any} mapItem   per-item shape (e.g. url-status vs keyword fields)
 */
export function useEndpointResource(basePath, country, refreshKey, mapItem) {
  const isAll = !country || country === "Wszystkie";
  const iso = isAll ? null : (COUNTRY_TO_ISO[country] || country);
  const endpoint = isAll ? basePath : `${basePath}?country=${encodeURIComponent(iso)}`;

  const cache = basePath === "/api/keyword-scan" ? _keywordScanCache : _urlStatusCache;
  const cached = refreshKey === 0 ? cache.get(endpoint) : null;
  const [data, setData] = useState(() => cached || { byId: {}, summary: null });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (refreshKey === 0 && cache.has(endpoint)) {
      setData(cache.get(endpoint));
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
            byId[item.id] = mapItem(item);
          }
        }
        const result = { byId, summary: json.summary || null };
        cache.set(endpoint, result);
        setData(result);
      })
      .catch((e) => !cancelled && setError(String(e)))
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [endpoint, refreshKey]); // eslint-disable-line react-hooks/exhaustive-deps

  return { ...data, loading, error };
}
