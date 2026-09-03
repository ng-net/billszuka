import { useEndpointResource } from "./_useEndpointResource";

/**
 * useUrlStatus(country) — pobiera mapę {id: statusObj} z /api/url-status.
 *
 * `country` może być nazwą ("Polska") albo ISO ("PL") — mapujemy.
 * "Wszystkie" / pusty → pusty stan, nic nie fetchuje.
 *
 * Returns: { byId, summary, loading, error }
 */
export function useUrlStatus(country, refreshKey = 0) {
  return useEndpointResource(
    "/api/url-status",
    country,
    refreshKey,
    (item) => ({
      status: item.status,
      state: item.state || "unknown",
      http_code: item.http_code,
      error: item.error,
      redirect_url: item.redirect_url,
      response_ms: item.response_ms,
      checked_at: item.checked_at,
      url: item.url,
    }),
  );
}
