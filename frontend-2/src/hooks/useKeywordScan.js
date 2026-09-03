import { useEndpointResource } from "./_useEndpointResource";

/**
 * useKeywordScan(country) — pobiera mapę {id: scanObj} z /api/keyword-scan.
 *
 * Returns: { byId, summary, loading, error }
 *
 * scanObj: { score_pct, keywords_found, keywords_total, scanned_at, http_code, html_size }
 */
export function useKeywordScan(country, refreshKey = 0) {
  return useEndpointResource(
    "/api/keyword-scan",
    country,
    refreshKey,
    (item) => ({
      score_pct: item.score_pct || 0,
      keywords_found: item.keywords_found || [],
      keywords_total: item.keywords_total || 0,
      scanned_at: item.scanned_at,
      http_code: item.http_code,
      html_size: item.html_size,
    }),
  );
}
