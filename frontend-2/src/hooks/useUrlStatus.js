import { useEffect, useState } from "react";

// Folder name (PL frontend) → ISO kod (backend)
const COUNTRY_TO_ISO = {
  "Polska": "PL", "Czechy": "CZ", "Słowacja": "SK", "Słowenia": "SI",
  "Chorwacja": "HR", "Bułgaria": "BG", "Rumunia": "RO", "Mołdawia": "MD",
  "Serbia": "RS", "Litwa": "LT", "Łotwa": "LV", "Estonia": "EE",
  "Francja": "FR",
};

/**
 * useUrlStatus(country) — pobiera mapę {id_unikalne: statusObj} z /api/url-status.
 *
 * `country` może być nazwą ("Polska") albo ISO ("PL") — mapujemy.
 * "Wszystkie" / pusty → pusty stan, nic nie fetchuje.
 *
 * Returns: { byId, summary, loading, error }
 */
export function useUrlStatus(country, refreshKey = 0) {
  const [data, setData] = useState({ byId: {}, summary: null });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!country || country === "Wszystkie") {
      setData({ byId: {}, summary: null });
      return;
    }
    const iso = COUNTRY_TO_ISO[country] || country;
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetch(`/api/url-status?country=${encodeURIComponent(iso)}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then((json) => {
        if (cancelled) return;
        const byId = {};
        for (const item of json.items || []) {
          if (!(item.id_unikalne in byId)) {
            byId[item.id_unikalne] = {
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
