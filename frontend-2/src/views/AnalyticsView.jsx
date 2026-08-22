import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Loader2, BarChart3, AlertTriangle, RefreshCw } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { groupBy, histogram, deriveStatus, COUNTRY_COLORS, colorFor } from "@/lib/analytics";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

/**
 * AnalyticsView — fixed BILLSzuka dashboards + dynamic column distributions.
 *
 * Loads data from /api/dataset/master.csv (backend FastAPI). Does NOT share
 * state with TableView — each view reads master.csv independently. This is
 * cheap (one network request) and avoids a deep refactor of RawTable.
 */
export function AnalyticsView() {
  const [data, setData] = useState({ columns: [], rows: [] });
  const [status, setStatus] = useState("loading");
  const [error, setError] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(null);

  const loadData = () => {
    const ac = new AbortController();
    setStatus("loading");
    setError(null);
    fetch("/api/dataset/master.csv?limit=1000", { signal: ac.signal })
      .then(async (res) => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        const body = await res.json();
        const rows = (body.data || []).map((arr) => {
          const obj = {};
          body.columns.forEach((c, i) => (obj[c] = arr[i] ?? ""));
          return obj;
        });
        setData({ columns: body.columns || [], rows });
        setStatus("ready");
        setLastRefresh(new Date());
      })
      .catch((e) => {
        if (e.name === "AbortError") return;
        setError(e.message || String(e));
        setStatus("error");
      });
    return ac.abort;
  };

  useEffect(() => { const cleanup = loadData(); return cleanup; }, []);

  if (status === "loading") {
    return (
      <div className="flex h-full items-center justify-center gap-2 text-muted-foreground">
        <Loader2 className="h-5 w-5 animate-spin" />
        <span>Ładowanie master.csv…</span>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="flex h-full items-center justify-center">
        <Card className="max-w-md border-destructive/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-destructive">
              <AlertTriangle className="h-5 w-5" />
              Błąd pobierania danych
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{error}</p>
            <p className="mt-2 text-xs text-muted-foreground">
              Upewnij się, że backend działa na{" "}
              <code className="rounded bg-muted px-1">python3 tools/api_server.py</code>{" "}
              (port 8000).
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { rows, columns } = data;
  const has = (col) => columns.includes(col);
  const total = rows.length;
  const activeCountries = rows.reduce((s, r) => s + (has("kraj") && r.kraj ? 1 : 0), 0);
  const refreshTime = lastRefresh
    ? lastRefresh.toLocaleTimeString("pl-PL", { hour: "2-digit", minute: "2-digit", second: "2-digit" })
    : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.18 }}
      className="mx-auto max-w-7xl p-6 space-y-5"
    >
      {/* Compact one-line header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-xl font-semibold tracking-tight flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-muted-foreground" />
            Analityka
          </h1>
          <p className="text-xs text-muted-foreground mt-0.5">
            {total.toLocaleString("pl-P")} firm &middot; {activeCountries} krajów
            {refreshTime && (
              <span className="ml-2 text-muted-foreground/50">
                &middot; odśw. {refreshTime}
              </span>
            )}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs hidden sm:inline-flex">
            master.csv
          </Badge>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            onClick={loadData}
            disabled={status === "loading"}
            title="Odśwież dane"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${status === "loading" ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Unified 4-column grid — all fixed charts */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        <CountryDistribution rows={rows} total={total} />
        <StatusDonut rows={rows} total={total} />
        <TierByCountry rows={rows} />
        <VolumeByCountry rows={rows} />
      </div>

      {/* Dynamic distributions — only shown when there are any */}
      <DynamicDistributions rows={rows} columns={columns} />
    </motion.div>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Shared chart constants
// ──────────────────────────────────────────────────────────────────────────

// Single tooltip style shared across all charts — DRY.
const T = { backgroundColor: "hsl(var(--popover))", border: "1px solid hsl(var(--border))", borderRadius: 6, fontSize: 12 };

// ──────────────────────────────────────────────────────────────────────────
// Fixed charts
// ──────────────────────────────────────────────────────────────────────────

function CountryDistribution({ rows, total }) {
  const data = useMemo(
    () =>
      groupBy(rows, "kraj").map((d) => ({
        ...d,
        pct: total > 0 ? (d.count / total) * 100 : 0,
      })),
    [rows, total]
  );
  if (data.length === 0) return <EmptyPanel title="Rozkład wg kraju" hint="Brak kolumny 'kraj'." />;
  return (
    <ChartCard title="Rozkład wg kraju" subtitle="Liczba firm per kraj">
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 4 }}>
          <XAxis dataKey="key" stroke="#888" fontSize={11} />
          <YAxis stroke="#888" fontSize={11} />
          <Tooltip
            contentStyle={T}
            formatter={(v, _n, p) => [`${v} (${p.payload.pct.toFixed(1)}%)`, "Firmy"]}
          />
          <Bar dataKey="count" radius={[3, 3, 0, 0]}>
            {data.map((d) => (
              <Cell key={d.key} fill={COUNTRY_COLORS[d.key] || colorFor(d.key)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

function StatusDonut({ rows, total }) {
  const data = useMemo(() => {
    const counts = { FROZEN: 0, "DO-WERYFIKACJI": 0, PENDING_API: 0, OTHER: 0 };
    for (const r of rows) {
      const s = deriveStatus(r.flagi);
      counts[s] = (counts[s] || 0) + 1;
    }
    return Object.entries(counts)
      .filter(([, n]) => n > 0)
      .map(([key, count]) => ({ key, count }));
  }, [rows]);
  if (data.length === 0) return <EmptyPanel title="Status weryfikacji" hint="Brak danych w kolumnie 'flagi'." />;
  const palette = ["#16a34a", "#eab308", "#3b82f6", "#a3a3a3"];
  return (
    <ChartCard title="Status weryfikacji" subtitle="FROZEN / DO-WERYFIKACJI / PENDING_API / OTHER">
      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie
            data={data}
            dataKey="count"
            nameKey="key"
            innerRadius={50}
            outerRadius={90}
            paddingAngle={2}
            label={(e) => `${e.key}: ${e.count}`}
            labelLine={false}
          >
            {data.map((d, i) => (
              <Cell key={d.key} fill={palette[i % palette.length]} />
            ))}
          </Pie>
          <Legend wrapperStyle={{ fontSize: 11 }} />
          <Tooltip
            contentStyle={T}
          />
        </PieChart>
      </ResponsiveContainer>
      <p className="text-xs text-muted-foreground mt-2 text-center">
        Łącznie {total} wierszy
      </p>
    </ChartCard>
  );
}

function TierByCountry({ rows }) {
  const data = useMemo(() => {
    const tiers = ["wyłączność", "autoryzowany", "reseller", "hurtownik", "producent", "detalista", "marketplace"];
    const countries = [...new Set(rows.map((r) => r.kraj).filter(Boolean))].sort();
    const matrix = countries.map((kraj) => {
      const out = { kraj };
      for (const t of tiers) out[t] = 0;
      for (const r of rows) {
        if (r.kraj !== kraj) continue;
        const t = (r.tier || "").trim();
        if (tiers.includes(t)) out[t] += 1;
      }
      return out;
    });
    return { tiers, countries, matrix };
  }, [rows]);
  if (!hasCol(rows, "kraj") || !hasCol(rows, "tier"))
    return <EmptyPanel title="Tier × kraj" hint="Brak kolumn 'kraj' lub 'tier'." />;
  const { tiers, matrix } = data;
  const tierColors = {
    wyłączność: "#dc2626",
    autoryzowany: "#ea580c",
    reseller: "#0891b2",
    hurtownik: "#2563eb",
    producent: "#16a34a",
    detalista: "#9333ea",
    marketplace: "#ca8a04",
  };
  return (
    <ChartCard
      title="Tier × kraj"
      subtitle="Macierz: ile firm w danym kraju ma dany tier"
    >
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b">
              <th className="text-left p-2 font-medium text-muted-foreground">Kraj</th>
              {tiers.map((t) => (
                <th key={t} className="text-right p-2 font-medium text-muted-foreground">
                  {t}
                </th>
              ))}
              <th className="text-right p-2 font-semibold">Σ</th>
            </tr>
          </thead>
          <tbody>
            {matrix.map((row) => {
              const total = Object.values(row).reduce(
                (s, v) => (typeof v === "number" ? s + v : s),
                0
              );
              const max = Math.max(...tiers.map((t) => row[t] || 0), 1);
              return (
                <tr key={row.kraj} className="border-b hover:bg-muted/30">
                  <td className="p-2 font-medium">
                    <span
                      className="inline-block h-2 w-2 rounded-full mr-1.5"
                      style={{ backgroundColor: COUNTRY_COLORS[row.kraj] || colorFor(row.kraj) }}
                    />
                    {row.kraj}
                  </td>
                  {tiers.map((t) => {
                    const v = row[t] || 0;
                    const intensity = v / max;
                    return (
                      <td
                        key={t}
                        className="text-right p-1.5 tabular-nums"
                        style={{
                          backgroundColor: v > 0 ? `${tierColors[t]}${Math.round(intensity * 60).toString(16).padStart(2, "0")}` : undefined,
                        }}
                      >
                        {v || ""}
                      </td>
                    );
                  })}
                  <td className="text-right p-2 font-semibold">{total}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </ChartCard>
  );
}

function VolumeByCountry({ rows }) {
  const data = useMemo(() => {
    const volumes = ["mały", "średni", "duży"];
    const countries = [...new Set(rows.map((r) => r.kraj).filter(Boolean))].sort();
    return countries.map((kraj) => {
      const out = { kraj };
      for (const v of volumes) out[v] = 0;
      for (const r of rows) {
        if (r.kraj !== kraj) continue;
        const v = (r.wolumen || "").trim().toLowerCase();
        if (volumes.includes(v)) out[v] += 1;
      }
      return out;
    });
  }, [rows]);
  if (!hasCol(rows, "kraj") || !hasCol(rows, "wolumen"))
    return <EmptyPanel title="Wolumen × kraj" hint="Brak kolumn 'kraj' lub 'wolumen'." />;
  const palette = { mały: "#a3a3a3", średni: "#eab308", duży: "#16a34a" };
  return (
    <ChartCard title="Wolumen × kraj" subtitle="Stacked bar: mały / średni / duży">
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 4 }}>
          <XAxis dataKey="kraj" stroke="#888" fontSize={11} />
          <YAxis stroke="#888" fontSize={11} />
          <Tooltip
            contentStyle={T}
          />
          <Legend wrapperStyle={{ fontSize: 11 }} />
          {["mały", "średni", "duży"].map((v) => (
            <Bar key={v} dataKey={v} stackId="a" fill={palette[v]} />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Dynamic distributions
// ──────────────────────────────────────────────────────────────────────────

function DynamicDistributions({ rows, columns }) {
  // Heuristic: treat columns with ≤30 unique non-empty values as categorical.
  const categorical = useMemo(() => {
    const out = [];
    for (const col of columns) {
      if (["related_to", "rok_zalozenia", "id_unikalne", "nazwa_firmy", "adres", "nip_vat", "rejestr_id", "www", "email", "telefon", "notatki", "marki_nabijarki", "marka_wlasna_oem", "sourcing", "kanal_sprzedaży", "zrodlo_danych", "data_weryfikacji", "flagi", "decydent", "stanowisko", "email_decydent"].includes(col)) continue;
      const unique = new Set();
      for (const r of rows) {
        const v = (r[col] || "").trim();
        if (v) unique.add(v);
        if (unique.size > 30) break;
      }
      if (unique.size >= 2 && unique.size <= 30) {
        out.push({ col, cardinality: unique.size });
      }
    }
    // Sort by interesting columns first
    const priority = ["kraj", "tier", "wolumen", "rynek_skala", "kategoria", "confidence_wolumen", "cross_sell_potential"];
    out.sort((a, b) => {
      const ai = priority.indexOf(a.col);
      const bi = priority.indexOf(b.col);
      if (ai !== -1 && bi !== -1) return ai - bi;
      if (ai !== -1) return -1;
      if (bi !== -1) return 1;
      return a.col.localeCompare(b.col);
    });
    return out;
  }, [rows, columns]);

  const numeric = useMemo(() => {
    // rok_zalozenia is the main numeric
    const candidates = ["rok_zalozenia", "powinowactwo_nabijarki"];
    return candidates.filter((c) => columns.includes(c));
  }, [columns]);

  if (categorical.length === 0 && numeric.length === 0) {
    return null; // nothing dynamic to show — clean silent skip
  }

  return (
    <>
      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
        Rozkłady
      </p>
      <div className="grid gap-4 grid-cols-2">
        {categorical.map(({ col }) => (
          <CategoricalDistribution key={col} rows={rows} col={col} />
        ))}
        {numeric.map((col) => (
          <NumericHistogram key={col} rows={rows} col={col} />
        ))}
      </div>
    </>
  );
}

function CategoricalDistribution({ rows, col }) {
  const data = useMemo(() => groupBy(rows, col), [rows, col]);
  if (data.length === 0) return null;
  return (
    <ChartCard title={col} subtitle={`Rozkład wartości (${data.length})`}>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 12, left: 60, bottom: 4 }}>
          <XAxis type="number" stroke="#888" fontSize={11} />
          <YAxis dataKey="key" type="category" stroke="#888" fontSize={10} width={56} />
          <Tooltip
            contentStyle={T}
            formatter={(v) => [`${v}`, "Firmy"]}
          />
          <Bar dataKey="count" radius={[0, 3, 3, 0]}>
            {data.map((d, i) => (
              <Cell key={d.key} fill={COUNTRY_COLORS[d.key] || colorFor(d.key, ["#2563eb", "#dc2626", "#16a34a", "#eab308", "#9333ea", "#0891b2"])} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

function NumericHistogram({ rows, col }) {
  const data = useMemo(() => histogram(rows, col, 12), [rows, col]);
  if (data.length === 0) return null;
  return (
    <ChartCard title={col} subtitle="Histogram (12 binów)">
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 24 }}>
          <XAxis dataKey="label" stroke="#888" fontSize={9} angle={-30} dy={8} />
          <YAxis stroke="#888" fontSize={11} />
          <Tooltip
            contentStyle={T}
            formatter={(v) => [`${v}`, "Firmy"]}
          />
          <Bar dataKey="count" fill="#2563eb" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}

// ──────────────────────────────────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────────────────────────────────

function hasCol(rows, col) {
  // Cheap check: if any row has the column key defined in objects, treat it as present.
  // Our row objects always have all keys (from columns array) so this is mostly a no-op
  // — kept for future-proofing if rows get sparse.
  return rows.length === 0 || col in rows[0];
}

function ChartCard({ title, subtitle, children }) {
  return (
    <Card>
      <CardHeader className="pb-1">
        <CardTitle className="text-sm font-medium text-foreground">{title}</CardTitle>
        {subtitle && <p className="text-[11px] text-muted-foreground leading-tight mt-0.5">{subtitle}</p>}
      </CardHeader>
      <CardContent className="pt-2">{children}</CardContent>
    </Card>
  );
}

function EmptyPanel({ title, hint }) {
  return (
    <ChartCard title={title} subtitle={hint}>
      <div className="h-32 flex items-center justify-center text-xs text-muted-foreground">
        Brak danych.
      </div>
    </ChartCard>
  );
}