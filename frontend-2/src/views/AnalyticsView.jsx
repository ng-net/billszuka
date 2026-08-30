import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Bird, BarChart3, AlertCircle, Loader2, Layers, MapPin, Building2, Tag } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { parseCsvUrl } from "@/lib/csv";
import { groupBy, deriveStatus, COUNTRY_COLORS, colorFor, topByCountry, claimDistributors, powerMaticListings } from "@/lib/analytics";
import { classifyBrand } from "@/lib/brand";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * AnalyticsView — real dashboard with cards driven by /api/master.csv.
 *
 * Six tiles:
 *   - Summary counts (total rows, countries, brands, FROZEN %)
 *   - Per-country bar chart (rows per Kraj, colored by COUNTRY_COLORS)
 *   - Per-tier distribution (hurtownik / producent / autoryzowany / marketplace / …)
 *   - Brand classifier breakdown (PowerMatic, PowerMatic + Hawk, Hawk, Inna)
 *   - Verification status mix (FROZEN / DO-WERYFIKACJI / PENDING_API / OTHER)
 *   - Verification coverage per country (Kraj × Status)
 *
 * Data is fetched once on mount. If the fetch fails, we fall back to a
 * compact empty state with the same "W przygotowaniu…" copy as before.
 */

const MASTER_URL = "/api/master.csv";

function Bar({ value, max, color, label, count }) {
  const pct = max > 0 ? Math.max(2, (value / max) * 100) : 0;
  return (
    <div className="flex items-center gap-3 text-sm">
      <div className="w-28 shrink-0 truncate text-muted-foreground" title={label}>{label}</div>
      <div className="relative h-5 flex-1 overflow-hidden rounded bg-muted">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="absolute inset-y-0 left-0 rounded"
          style={{ background: color }}
        />
      </div>
      <div className="w-12 shrink-0 text-right tabular-nums">{count.toLocaleString("pl-PL")}</div>
    </div>
  );
}

function KpiTile({ label, value, hint, icon: Icon }) {
  return (
    <Card>
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <div className="text-xs uppercase tracking-wider text-muted-foreground">{label}</div>
            <div className="mt-2 text-3xl font-bold tabular-nums">{value}</div>
            {hint && <div className="mt-1 text-xs text-muted-foreground">{hint}</div>}
          </div>
          {Icon && (
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-muted">
              <Icon className="h-4 w-4 text-muted-foreground" />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export function AnalyticsView() {
  const [state, setState] = useState({ status: "loading", rows: [], error: null });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { rows } = await parseCsvUrl(MASTER_URL, { onProgress: () => {} });
        if (cancelled) return;
        setState({ status: "ready", rows, error: null });
      } catch (e) {
        if (cancelled) return;
        setState({ status: "error", rows: [], error: e.message || String(e) });
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const tiles = useMemo(() => {
    const rows = state.rows;
    if (rows.length === 0) return null;

    const byCountry = groupBy(rows, "kraj", { top: 14 });
    const byTier = groupBy(rows, "tier", { top: 10 });

    // Brand classifier — counts via classifyBrand() per row.
    const brandCounts = new Map();
    for (const r of rows) {
      const b = classifyBrand(r);
      if (b === "—") continue;
      brandCounts.set(b, (brandCounts.get(b) || 0) + 1);
    }
    const byBrand = [...brandCounts.entries()]
      .map(([key, count]) => ({ key, count }))
      .sort((a, b) => b.count - a.count);

    // Verification status (FROZEN / DO-WERYFIKACJI / PENDING_API / OTHER).
    const statusCounts = new Map();
    for (const r of rows) {
      const s = deriveStatus(r.flagi);
      statusCounts.set(s, (statusCounts.get(s) || 0) + 1);
    }
    const byStatus = [...statusCounts.entries()]
      .map(([key, count]) => ({ key, count }))
      .sort((a, b) => b.count - a.count);

    // Verification coverage per country: Kraj → { FROZEN, OTHER, total }.
    const coverage = new Map();
    for (const r of rows) {
      const k = (r.kraj || "").trim() || "—";
      if (!coverage.has(k)) coverage.set(k, { FROZEN: 0, OTHER: 0 });
      const slot = coverage.get(k);
      if (deriveStatus(r.flagi) === "FROZEN") slot.FROZEN++;
      else slot.OTHER++;
    }
    const coverageRows = [...coverage.entries()]
      .map(([kraj, v]) => ({ kraj, ...v, total: v.FROZEN + v.OTHER }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 10);

    const countryCount = byCountry.filter((r) => r.key !== "—").length;
    const frozenCount = statusCounts.get("FROZEN") || 0;
    const frozenPct = rows.length ? Math.round((frozenCount / rows.length) * 100) : 0;

    // Highlighted insight tiles
    const claims = claimDistributors(rows);
    const pmListings = powerMaticListings(rows);
    const top5 = topByCountry(rows, 5, "confidence_wolumen");
    const top10 = topByCountry(rows, 10, "confidence_wolumen");

    return {
      total: rows.length,
      countryCount,
      brandCount: byBrand.length,
      frozenCount,
      frozenPct,
      byCountry,
      byTier,
      byBrand,
      byStatus,
      coverageRows,
      claims,
      pmListings,
      top5,
      top10,
    };
  }, [state.rows]);

  // Loading / error states.
  if (state.status === "loading") {
    return (
      <div className="flex h-full items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
        <span>Ładuję master.csv…</span>
      </div>
    );
  }
  if (state.status === "error" || !tiles) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <Card className="max-w-md">
          <CardContent className="p-6 text-center">
            <Bird className="mx-auto mb-3 h-10 w-10 text-rose-500" />
            <p className="font-semibold mb-1">Nie udało się załadować danych</p>
            <p className="text-sm text-muted-foreground">
              Sprawdź, czy backend działa (<code className="text-xs">/api/master.csv</code>).
            </p>
            {state.error && (
              <p className="mt-3 text-xs text-muted-foreground break-all">{state.error}</p>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  const maxByCountry = Math.max(...tiles.byCountry.map((r) => r.count), 1);
  const maxByTier = Math.max(...tiles.byTier.map((r) => r.count), 1);
  const maxByBrand = Math.max(...tiles.byBrand.map((r) => r.count), 1);
  const maxByStatus = Math.max(...tiles.byStatus.map((r) => r.count), 1);
  const frozenPct = tiles.total > 0 ? Math.round((tiles.frozenCount / tiles.total) * 100) : 0;
  const statusColor = (s) => ({
    FROZEN: "#16a34a",
    "DO-WERYFIKACJI": "#eab308",
    PENDING_API: "#0ea5e9",
    OTHER: "#94a3b8",
  })[s] || "#94a3b8";

  return (
    <div className="h-full overflow-auto p-4 sm:p-6 space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Analityka</h1>
          <p className="text-sm text-muted-foreground">
            Podsumowanie <strong>{tiles.total.toLocaleString("pl-PL")}</strong> wierszy z master.csv
          </p>
        </div>
        <Badge variant="outline" className="text-[10px]">
          <BarChart3 className="h-3 w-3 mr-1" /> Na żywo
        </Badge>
      </div>

      {/* KPI strip */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 sm:gap-4">
        <KpiTile
          label="Wiersze"
          value={tiles.total.toLocaleString("pl-PL")}
          icon={Layers}
        />
        <KpiTile
          label="Kraje"
          value={tiles.countryCount}
          icon={MapPin}
        />
        <KpiTile
          label="Marki (brand)"
          value={tiles.brandCount}
          icon={Tag}
        />
        <KpiTile
          label="FROZEN"
          value={`${frozenPct}%`}
          hint={`${tiles.frozenCount.toLocaleString("pl-PL")} zweryfikowanych`}
          icon={Building2}
        />
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Per-country */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Wiersze wg kraju</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {tiles.byCountry.map((row) => (
              <Bar
                key={row.key}
                label={row.key}
                value={row.count}
                max={maxByCountry}
                count={row.count}
                color={COUNTRY_COLORS[row.key] || colorFor(row.key)}
              />
            ))}
          </CardContent>
        </Card>

        {/* Per-tier */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Rozkład tier</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {tiles.byTier.map((row) => (
              <Bar
                key={row.key}
                label={row.key}
                value={row.count}
                max={maxByTier}
                count={row.count}
                color={colorFor(row.key)}
              />
            ))}
          </CardContent>
        </Card>

        {/* Brand breakdown */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Marki (brand classifier)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {tiles.byBrand.length === 0 && (
              <p className="text-sm text-muted-foreground">Brak wierszy z rozpoznawalną marką.</p>
            )}
            {tiles.byBrand.map((row) => (
              <Bar
                key={row.key}
                label={row.key}
                value={row.count}
                max={maxByBrand}
                count={row.count}
                color={row.key === "PowerMatic + Hawk" ? "#7c3aed"
                  : row.key === "PowerMatic" ? "#dc2626"
                  : row.key === "Hawk" ? "#0891b2"
                  : "#64748b"}
              />
            ))}
          </CardContent>
        </Card>

        {/* Verification status */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Status weryfikacji</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {tiles.byStatus.map((row) => (
              <Bar
                key={row.key}
                label={row.key}
                value={row.count}
                max={maxByStatus}
                count={row.count}
                color={statusColor(row.key)}
              />
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Coverage by country */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Pokrycie FROZEN wg kraju (top 10)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {tiles.coverageRows.map((row) => {
            const pct = row.total > 0 ? Math.round((row.FROZEN / row.total) * 100) : 0;
            return (
              <div key={row.kraj} className="flex items-center gap-3 text-sm">
                <div className="w-12 shrink-0 font-medium">{row.kraj}</div>
                <div className="relative h-5 flex-1 overflow-hidden rounded bg-muted">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.5, ease: "easeOut" }}
                    className="absolute inset-y-0 left-0 rounded bg-emerald-500"
                  />
                </div>
                <div className="w-24 shrink-0 text-right tabular-nums text-muted-foreground">
                  {row.FROZEN}/{row.total} · {pct}%
                </div>
              </div>
            );
          })}
          {tiles.coverageRows.length === 0 && (
            <p className="text-sm text-muted-foreground">Brak danych.</p>
          )}
        </CardContent>
      </Card>

      {/* Distributors who claim it in their notes (highlight) */}
      <Card className="border-amber-200/60 dark:border-amber-900/40 bg-amber-50/30 dark:bg-amber-950/20">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-amber-500/20 text-amber-600">★</span>
            Twierdzą że są dystrybutorami
            <span className="ml-auto text-xs font-mono tabular-nums text-muted-foreground">
              {tiles.claims.length} z {tiles.total}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {tiles.claims.length === 0 ? (
            <p className="text-sm text-muted-foreground">Brak firm deklarujących dystrybucję.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {tiles.claims.map((r) => (
                <div
                  key={r.id_unikalne}
                  className="flex items-center gap-3 px-3 py-2 rounded-md bg-white dark:bg-card border border-amber-200 dark:border-amber-900/40"
                >
                  <span className="text-[10px] font-mono font-bold tabular-nums text-amber-700 dark:text-amber-300 bg-amber-100 dark:bg-amber-950/60 px-1.5 py-0.5 rounded">
                    {r.kraj}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium truncate">{r.nazwa_firmy}</div>
                    <div className="text-[11px] text-muted-foreground truncate">
                      {r.tier} · {r.miasto || "—"} · dopasowanie: „{r.match_term}"
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* PowerMatic listings */}
      <Card className="border-violet-200/60 dark:border-violet-900/40 bg-violet-50/30 dark:bg-violet-950/20">
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <span className="inline-flex items-center justify-center w-5 h-5 rounded bg-violet-500/20 text-violet-600 font-bold text-[10px]">PM</span>
            Firmy z PowerMatic w ofercie
            <span className="ml-auto text-xs font-mono tabular-nums text-muted-foreground">
              {tiles.pmListings.length} z {tiles.total}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {tiles.pmListings.length === 0 ? (
            <p className="text-sm text-muted-foreground">Brak firm z PowerMatic w bazie.</p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {tiles.pmListings.map((r) => (
                <div
                  key={r.id_unikalne}
                  className={
                    "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border " +
                    (r.brand_variant === "PowerMatic + Hawk"
                      ? "bg-violet-100 dark:bg-violet-950/60 text-violet-700 dark:text-violet-300 border-violet-300 dark:border-violet-800"
                      : "bg-white dark:bg-card text-violet-700 dark:text-violet-300 border-violet-200 dark:border-violet-900/40")
                  }
                  title={`${r.nazwa_firmy} · ${r.marki_nabijarki}`}
                >
                  <span className="font-mono text-[10px] opacity-60">{r.kraj}</span>
                  <span className="truncate max-w-[180px]">{r.nazwa_firmy}</span>
                  <span className="text-[9px] uppercase tracking-wider opacity-70">·{r.brand_variant}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Top 5 / Top 10 per country */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Bird className="h-4 w-4 text-indigo-500" />
              Top 5 per kraj
              <span className="ml-auto text-[11px] text-muted-foreground font-normal">
                wg wolumenu
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {tiles.top5.map((g) => (
              <div key={g.country} className="border-l-2 border-indigo-300 dark:border-indigo-800 pl-3">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-[10px] font-mono font-bold tabular-nums bg-indigo-100 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 px-1.5 py-0.5 rounded">
                    {g.country}
                  </span>
                  <span className="text-[11px] text-muted-foreground">
                    {g.rows.length} firm
                  </span>
                </div>
                <ol className="space-y-1">
                  {g.rows.map((r, i) => (
                    <li key={r.id_unikalne} className="flex items-center gap-2 text-[12px]">
                      <span className="text-[10px] font-mono tabular-nums text-muted-foreground w-4">
                        {i + 1}.
                      </span>
                      <span className="flex-1 truncate font-medium">{r.nazwa_firmy}</span>
                      <span className="text-[10px] text-muted-foreground tabular-nums">
                        {r.confidence_wolumen || r.wolumen}
                      </span>
                    </li>
                  ))}
                </ol>
              </div>
            ))}
            {tiles.top5.length === 0 && (
              <p className="text-sm text-muted-foreground">Brak danych.</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Layers className="h-4 w-4 text-emerald-500" />
              Top 10 per kraj
              <span className="ml-auto text-[11px] text-muted-foreground font-normal">
                pełna lista
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {tiles.top10.map((g) => (
                <details key={g.country} className="group border border-slate-200 dark:border-border rounded-md">
                  <summary className="cursor-pointer px-3 py-1.5 flex items-center gap-2 text-[12px] font-medium hover:bg-slate-50 dark:hover:bg-muted/40">
                    <span className="font-mono text-[10px] tabular-nums bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 px-1.5 py-0.5 rounded">
                      {g.country}
                    </span>
                    <span className="text-muted-foreground">{g.rows.length}</span>
                    <span className="ml-auto text-[10px] group-open:rotate-90 transition-transform">▶</span>
                  </summary>
                  <ol className="px-3 py-2 space-y-0.5 text-[11.5px]">
                    {g.rows.map((r, i) => (
                      <li key={r.id_unikalne} className="flex items-center gap-2 truncate">
                        <span className="font-mono tabular-nums text-muted-foreground w-5">{i + 1}.</span>
                        <span className="truncate">{r.nazwa_firmy}</span>
                        <span className="ml-auto text-[10px] text-muted-foreground tabular-nums">
                          {r.confidence_wolumen || ""}
                        </span>
                      </li>
                    ))}
                  </ol>
                </details>
              ))}
            </div>
            {tiles.top10.length === 0 && (
              <p className="text-sm text-muted-foreground">Brak danych.</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Footer hint */}
      <div className="flex items-center gap-2 text-xs text-muted-foreground pt-2">
        <AlertCircle className="h-3.5 w-3.5" />
        Karty liczone są z aktualnego <code>master.csv</code>. Wykresy pojawią się po załadowaniu ≥1 wiersza.
      </div>
    </div>
  );
}