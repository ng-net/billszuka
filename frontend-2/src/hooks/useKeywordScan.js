import { useEffect, useState } from "react";

// Folder name (PL frontend) → ISO kod (backend)
const COUNTRY_TO_ISO = {
  "Polska": "PL", "Czechy": "CZ", "Słowacja": "SK", "Słowenia": "SI",
  "Chorwacja": "HR", "Bułgaria": "BG", "Rumunia": "RO", "Mołdawia": "MD",
  "Serbia": "RS", "Litwa": "LT", "Łotwa": "LV", "Estonia": "EE",
  "Francja": "FR",
};

/**
 * useKeywordScan(country) — pobiera mapę {id_unikalne: scanObj} z /api/keyword-scan.
 *
 * Returns: { byId, summary, loading, error }
 *
 * scanObj: { score_pct, keywords_found, keywords_total, scanned_at, http_code, html_size }
 */
export function useKeywordScan(country, refreshKey = 0) {
  const [data, setData] = useState({ byId: {}, summary: null });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const isAll = !country || country === "Wszystkie";
    const iso = isAll ? null : (COUNTRY_TO_ISO[country] || country);
    const endpoint = isAll
      ? "/api/keyword-scan"
      : `/api/keyword-scan?country=${encodeURIComponent(iso)}`;

    let cancelled = false;
    setLoading(true);
    setError(null);
    fetch(endpoint)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then((json) => {
        if (cancelled) return;
        const byId = {};
        for (const item of json.items || []) {
          if (!(item.id_unikalne in byId)) {
            byId[item.id_unikalne] = {
              score_pct: item.score_pct || 0,
              keywords_found: item.keywords_found || [],
              keywords_total: item.keywords_total || 0,
              scanned_at: item.scanned_at,
              http_code: item.http_code,
              html_size: item.html_size,
            };
          }
        }
        setData({ byId, summary: json.summary || null });
      })
      .catch((e) => !cancelled && setError(String(e)))
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
    };
  }, [country, refreshKey]);

  return { ...data, loading, error };
}
