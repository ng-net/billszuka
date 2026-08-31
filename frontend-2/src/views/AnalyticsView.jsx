import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { Bird, BarChart3, AlertCircle, Loader2, Layers, MapPin, Building2, Tag, AlertTriangle, Sparkles, Zap, ChevronDown, CheckCircle2, Info } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { parseCsvUrl } from "@/lib/csv";
import {
  groupBy, deriveStatus, COUNTRY_COLORS, colorFor,
  topByCountry, claimDistributors, powerMaticListings,
  powerMaticMatrix, regionRollup, coverageByCountry,
  researchAnomalies, topResearchAnomaly, verificationTimeline,
  powerMaticGroups,
} from "@/lib/analytics";
import { classifyBrand } from "@/lib/brand";
import { cn } from "@/lib/utils";

/**
 * AnalyticsView v1.2 — redesigned per docs/ANALYTICS-REDESIGN.md
 *
 * Sections (top → bottom):
 *   1. Header
 *   2. Headline insight banner (dismissable, only if anomaly exists)
 *   3. KPI strip — 6 tiles (incl. 2 new PM tiles)
 *   4. Hero card: Kraje × PowerMatic (heatmap / stacked toggle)
 *   5. Region rollup — 3 cards (V4, Balkans, Baltics)
 *   6. Research ROI callout
 *   7. Coverage chart (stacked) + Status mix (donut)
 *   8. Brand classifier donut + Tier bars
 *   9. Verification velocity timeline (sparkline grid)
 *  10. PowerMatic listings (grouped) + Claims
 *  11. Top firms (collapsible <details> per country)
 */

const MASTER_URL = "/api/master.csv";
const STATUS_COLORS = {
  FROZEN: "#16a34a",
  "DO-WERYFIKACJI": "#eab308",
  PENDING_API: "#0ea5e9",
  OTHER: "#94a3b8",
};
const BRAND_COLORS = {
  "PowerMatic + Hawk": "#7c3aed",
  "PowerMatic": "#dc2626",
  "Hawk": "#0891b2",
  "Inna": "#64748b",
};
const REGION_ORDER = ["Balkans", "V4", "Baltics"]; // by PM% desc in current data

// ---------------------------------------------------------------------------
// Small visual primitives
// ---------------------------------------------------------------------------

function Bar({ value, max, color, label, count, sub }) {
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
      <div className="w-16 shrink-0 text-right tabular-nums">
        <span className="font-medium">{count.toLocaleString("pl-PL")}</span>
        {sub != null && <span className="text-muted-foreground ml-1 text-xs">{sub}</span>}
      </div>
    </div>
  );
}

function KpiTile({ label, value, hint, icon: Icon, accent }) {
  const accentCls = accent === "violet"
    ? "bg-violet-50/40 dark:bg-violet-950/20 border-violet-200/60 dark:border-violet-900/40"
    : "";
  return (
    <Card className={accentCls}>
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

function Donut({ segments, size = 120, strokeWidth = 18, centerLabel, centerValue }) {
  // Pure SVG donut. segments: [{ value, color, label }]. Skips 0-value segments.
  const r = (size - strokeWidth) / 2;
  const c = 2 * Math.PI * r;
  const visible = segments.filter(s => s.value > 0);
  const total = visible.reduce((s, x) => s + x.value, 0);
  let offset = 0;
  return (
    <div className="flex items-center gap-5">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
        {total === 0 ? (
          <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="currentColor" strokeOpacity="0.15" strokeWidth={strokeWidth} />
        ) : visible.map((s, i) => {
          const seg = (s.value / total) * c;
          const dasharray = `${seg} ${c - seg}`;
          const dashoffset = -offset;
          offset += seg;
          return (
            <circle
              key={i}
              cx={size/2}
              cy={size/2}
              r={r}
              fill="none"
              stroke={s.color}
              strokeWidth={strokeWidth}
              strokeDasharray={dasharray}
              strokeDashoffset={dashoffset}
            >
              <title>{`${s.label}: ${s.value} (${Math.round(100*s.value/total)}%)`}</title>
            </circle>
          );
        })}
        <text
          x={size/2}
          y={size/2}
          textAnchor="middle"
          dominantBaseline="middle"
          transform={`rotate(90 ${size/2} ${size/2})`}
          className="fill-foreground"
        >
          <tspan x={size/2} dy="-0.2em" className="text-lg font-bold tabular-nums">{centerValue}</tspan>
          <tspan x={size/2} dy="1.3em" className="text-[10px] uppercase tracking-wider fill-muted-foreground">{centerLabel}</tspan>
        </text>
      </svg>
      <ul className="space-y-1.5 text-sm">
        {segments.map((s) => {
          const pct = total > 0 ? Math.round(100 * s.value / total) : 0;
          return (
            <li key={s.label} className="flex items-center gap-2">
              <span className="inline-block h-2.5 w-2.5 rounded-sm shrink-0" style={{ background: s.color }} />
              <span className="text-muted-foreground">{s.label}</span>
              <span className="ml-auto tabular-nums font-medium">{s.value}</span>
              <span className="text-muted-foreground tabular-nums w-9 text-right text-xs">{pct}%</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function Sparkline({ data, width = 60, height = 16, color = "#16a34a" }) {
  if (!data || data.length === 0) {
    return <span className="text-muted-foreground text-xs">▁▁▁▁▁▁</span>;
  }
  const max = Math.max(1, ...data);
  const stepX = data.length > 1 ? width / (data.length - 1) : 0;
  const points = data.map((v, i) => {
    const x = i * stepX;
    const y = height - (v / max) * (height - 2) - 1;
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <title>{`Sparkline: ${data.join(" → ")}`}</title>
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Section: PowerMatic heatmap (with stacked alt view)
// ---------------------------------------------------------------------------

function PowerMaticHeatmap({ countries, max }) {
  const cols = [
    { key: "pm", label: "PowerMatic", color: "#7c3aed" },
    { key: "hawk", label: "Hawk", color: "#0891b2" },
    { key: "both", label: "PM+Hawk", color: "#a855f7" },
    { key: "brak", label: "Brak", color: "#64748b" },
  ];
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-[10px] uppercase tracking-wider text-muted-foreground">
            <th className="text-left font-medium pb-2 pr-3 w-32">Kraj</th>
            {cols.map(c => (
              <th key={c.key} className="text-right font-medium pb-2 px-2">
                <span className="inline-block h-2 w-2 rounded-sm mr-1 align-middle" style={{ background: c.color }} />
                {c.label}
              </th>
            ))}
            <th className="text-right font-medium pb-2 pl-2">Suma</th>
            <th className="text-right font-medium pb-2 pl-2 text-muted-foreground">Effort</th>
          </tr>
        </thead>
        <tbody>
          {countries.map(c => (
            <tr key={c.kraj} className="border-t border-border/40">
              <td className="py-1.5 pr-3">
                <span className="font-mono text-[11px] font-semibold bg-muted px-1.5 py-0.5 rounded">{c.kraj}</span>
              </td>
              {cols.map(col => {
                const v = c[col.key] || 0;
                const alpha = max > 0 ? Math.max(0.04, Math.min(0.85, v / max)) : 0;
                return (
                  <td key={col.key} className="py-1.5 px-2 text-right">
                    <span
                      className={cn(
                        "inline-block min-w-[2.25rem] px-1.5 py-0.5 rounded text-[11px] tabular-nums",
                        v > 0 ? "text-foreground" : "text-muted-foreground"
                      )}
                      style={{ background: v > 0 ? `${col.color}${Math.round(alpha*255).toString(16).padStart(2, "0")}` : "transparent" }}
                    >
                      {v}
                    </span>
                  </td>
                );
              })}
              <td className="py-1.5 pl-2 text-right tabular-nums font-semibold">{c.total}</td>
              <td className="py-1.5 pl-2 text-right tabular-nums text-muted-foreground text-xs">{c.total}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PowerMaticStacked({ countries, max }) {
  return (
    <div className="space-y-2.5">
      {countries.map(c => {
        const pmSegments = [
          { key: "pm", color: "#7c3aed" },
          { key: "hawk", color: "#0891b2" },
          { key: "both", color: "#a855f7" },
          { key: "brak", color: "#cbd5e1" },
        ];
        return (
          <div key={c.kraj} className="flex items-center gap-3 text-sm">
            <div className="w-12 shrink-0 font-mono text-[11px] font-semibold bg-muted px-1.5 py-0.5 rounded text-center">{c.kraj}</div>
            <div className="relative h-5 flex-1 overflow-hidden rounded bg-muted">
              <div className="absolute inset-y-0 left-0 flex w-full">
                {pmSegments.map(seg => {
                  const v = c[seg.key] || 0;
                  if (v === 0) return null;
                  const pct = (v / c.total) * 100;
                  return (
                    <motion.div
                      key={seg.key}
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ duration: 0.5, ease: "easeOut" }}
                      className="h-full"
                      style={{ background: seg.color }}
                      title={`${seg.key}: ${v}`}
                    />
                  );
                })}
              </div>
            </div>
            <div className="w-28 shrink-0 text-right tabular-nums text-xs text-muted-foreground">
              {(c.pm + c.both)}/{c.total} PM ({c.pmPct}%)
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section: Region rollup card
// ---------------------------------------------------------------------------

function RegionCard({ region }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-baseline justify-between">
          <span>{region.name}</span>
          <span className="text-2xl font-bold tabular-nums">{region.total}</span>
        </CardTitle>
        <div className="text-[10px] uppercase tracking-wider text-muted-foreground">firm w regionie</div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-muted-foreground">PowerMatic</span>
            <span className="tabular-nums font-medium">{region.pm}/{region.total} · {region.pmPct}%</span>
          </div>
          <div className="relative h-2 overflow-hidden rounded bg-muted">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${region.pmPct}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="absolute inset-y-0 left-0 rounded"
              style={{ background: "#7c3aed" }}
            />
          </div>
        </div>
        <div>
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-muted-foreground">FROZEN</span>
            <span className="tabular-nums font-medium">{region.fr}/{region.total} · {region.frPct}%</span>
          </div>
          <div className="relative h-2 overflow-hidden rounded bg-muted">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${region.frPct}%` }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="absolute inset-y-0 left-0 rounded"
              style={{ background: "#16a34a" }}
            />
          </div>
        </div>
        <div className="border-t border-border/40 pt-2 space-y-1">
          {region.krajeRows.map(k => (
            <div key={k.kraj} className="flex items-center gap-2 text-[11px]">
              <span className={cn(
                "font-mono font-semibold px-1.5 py-0.5 rounded text-[10px] w-9 text-center",
                k.anomaly ? "bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300"
                : "bg-muted text-muted-foreground"
              )}>
                {k.kraj}
              </span>
              <span className="text-muted-foreground tabular-nums">{k.total} firm</span>
              <span className="tabular-nums font-medium">{k.pm} PM</span>
              <span className="text-muted-foreground tabular-nums">· {k.fr} FROZEN</span>
              <span className="ml-auto">
                {k.anomaly && <span title="Anomalia: duży rynek, 0 PM" className="text-amber-600">⚠</span>}
                {k.importer && <span title="Importer / dovozce" className="text-violet-600 ml-1">📥</span>}
                {!k.anomaly && !k.importer && k.pmPct >= 10 && <span title="OK" className="text-emerald-600">✓</span>}
              </span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Section: Research ROI callout
// ---------------------------------------------------------------------------

function AnomalyLine({ item, icon: Icon, color }) {
  return (
    <div className="flex items-start gap-3 px-3 py-2">
      <Icon className={cn("h-4 w-4 mt-0.5 shrink-0", color)} />
      <div className="flex-1 min-w-0">
        <div className="text-sm">
          <span className="font-mono text-[11px] font-semibold bg-muted px-1.5 py-0.5 rounded mr-2">{item.kraj}</span>
          <span className="font-medium tabular-nums">{item.total} firm, {item.pm} PM, {item.fr} FROZEN</span>
        </div>
        <div className="text-xs text-muted-foreground mt-0.5">{item.text}</div>
      </div>
    </div>
  );
}

function ResearchROICard({ anomalies, unverified, ideal }) {
  if (anomalies.length === 0 && unverified.length === 0 && ideal.length === 0) return null;
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-amber-500" />
          Anomalie research → wynik
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {anomalies.length > 0 && (
          <div className="space-y-1">
            <div className="text-[10px] uppercase tracking-wider text-amber-600 dark:text-amber-400">Luka (duży rynek, 0 PM)</div>
            {anomalies.map(a => <AnomalyLine key={a.kraj} item={a} icon={AlertTriangle} color="text-amber-600" />)}
          </div>
        )}
        {unverified.length > 0 && (
          <div className="space-y-1">
            <div className="text-[10px] uppercase tracking-wider text-sky-600 dark:text-sky-400">Niezweryfikowane (0% FROZEN)</div>
            {unverified.map(u => <AnomalyLine key={u.kraj} item={u} icon={Info} color="text-sky-600" />)}
          </div>
        )}
        {ideal.length > 0 && (
          <div className="space-y-1">
            <div className="text-[10px] uppercase tracking-wider text-emerald-600 dark:text-emerald-400">Wzorcowe kraje (wysoki PM + FROZEN)</div>
            {ideal.map(i => <AnomalyLine key={i.kraj} item={i} icon={CheckCircle2} color="text-emerald-600" />)}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// ---------------------------------------------------------------------------
// Section: Coverage stacked bar
// ---------------------------------------------------------------------------

function CoverageStackedBar({ row }) {
  const segs = [
    { key: "FROZEN", color: STATUS_COLORS.FROZEN },
    { key: "DO_W", color: STATUS_COLORS["DO-WERYFIKACJI"], label: "DO-W" },
    { key: "PEND", color: STATUS_COLORS.PENDING_API, label: "PEND" },
    { key: "OTHER", color: STATUS_COLORS.OTHER },
  ];
  const total = row.total || 1;
  return (
    <div className="flex items-center gap-3 text-sm">
      <div className={cn(
        "w-12 shrink-0 font-mono text-[11px] font-semibold px-1.5 py-0.5 rounded text-center",
        row.frPct === 0 ? "bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300"
        : row.frPct < 70 ? "bg-orange-100 dark:bg-orange-950/60 text-orange-700 dark:text-orange-300"
        : "bg-muted text-muted-foreground"
      )}>
        {row.kraj}
      </div>
      <div className="relative h-5 flex-1 overflow-hidden rounded bg-muted">
        <div className="absolute inset-y-0 left-0 flex w-full">
          {segs.map(s => {
            const v = row[s.key] || 0;
            if (v === 0) return null;
            const pct = (v / total) * 100;
            return (
              <motion.div
                key={s.key}
                initial={{ width: 0 }}
                animate={{ width: `${pct}%` }}
                transition={{ duration: 0.4, ease: "easeOut" }}
                className="h-full"
                style={{ background: s.color }}
                title={`${s.label || s.key}: ${v}`}
              />
            );
          })}
        </div>
      </div>
      <div className="w-40 shrink-0 text-right text-[11px] tabular-nums text-muted-foreground">
        FROZEN {row.FROZEN}/{row.total} · DO-W {row.DO_W} · PEND {row.PEND} · OTH {row.OTHER}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section: Verification timeline
// ---------------------------------------------------------------------------

function TimelineRow({ row, max, monthLabels }) {
  return (
    <div className="flex items-center gap-3 text-sm">
      <div className="w-12 shrink-0 font-mono text-[11px] font-semibold bg-muted px-1.5 py-0.5 rounded text-center">{row.kraj}</div>
      <div className="w-16 shrink-0">
        <Sparkline data={row.spark} width={60} height={16} color={row.lastMonth > 0 ? "#16a34a" : "#94a3b8"} />
      </div>
      <div className="flex-1 flex items-center gap-1">
        {row.spark.map((v, i) => (
          <div
            key={i}
            className="flex-1 h-2 rounded-sm bg-muted overflow-hidden"
            title={`${monthLabels[i] || ""}: ${v} FROZEN (cumul.)`}
          >
            <div
              className="h-full bg-emerald-500"
              style={{ width: max > 0 ? `${Math.min(100, (v / max) * 100)}%` : "0%" }}
            />
          </div>
        ))}
      </div>
      <div className="w-20 shrink-0 text-right tabular-nums text-xs text-muted-foreground">
        {row.lastMonth > 0 ? `+${row.lastMonth} ostatni mc` : "0 / brak danych"}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function AnalyticsView() {
  const [state, setState] = useState({ status: "loading", rows: [], error: null });
  const [pmView, setPmView] = useState("heatmap");
  const [insightDismissed, setInsightDismissed] = useState(false);

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

    const byCountry = groupBy(rows, "kraj", { top: 20 });
    const byTier = groupBy(rows, "tier", { top: 10 });

    const brandCounts = new Map();
    for (const r of rows) {
      const b = classifyBrand(r);
      if (b === "—") continue;
      brandCounts.set(b, (brandCounts.get(b) || 0) + 1);
    }
    const byBrand = [...brandCounts.entries()]
      .map(([key, count]) => ({ key, count }))
      .sort((a, b) => b.count - a.count);

    const statusCounts = new Map();
    for (const r of rows) {
      const s = deriveStatus(r.flagi);
      statusCounts.set(s, (statusCounts.get(s) || 0) + 1);
    }
    const byStatus = [...statusCounts.entries()]
      .map(([key, count]) => ({ key, count }))
      .sort((a, b) => b.count - a.count);

    const countryCount = byCountry.filter((r) => r.key !== "—").length;
    const frozenCount = statusCounts.get("FROZEN") || 0;
    const frozenPct = rows.length ? Math.round((frozenCount / rows.length) * 100) : 0;

    // v1.2 — new aggregations
    const pmMatrix = powerMaticMatrix(rows);
    const regions = regionRollup(rows);
    const coverage = coverageByCountry(rows);
    const anomalies = researchAnomalies(rows);
    const insight = topResearchAnomaly(rows);
    const timeline = verificationTimeline(rows, 6);
    const grouped = powerMaticGroups(rows);
    const pmListings = powerMaticListings(rows);
    const pmKraj = new Set(pmListings.map(r => r.kraj));
    const claims = claimDistributors(rows);
    const topByCountryList = topByCountry(rows, 10, "confidence_wolumen");

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
      pmMatrix,
      regions,
      coverage,
      anomalies,
      insight,
      timeline,
      grouped,
      pmListings,
      pmKraj,
      pmKrajSize: pmKraj.size,
      pmCount: pmListings.length,
      claims,
      topByCountryList,
    };
  }, [state.rows]);

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

  const statusSegments = (["FROZEN", "DO-WERYFIKACJI", "PENDING_API", "OTHER"]).map(k => ({
    label: k, value: (tiles.byStatus.find(s => s.key === k) || { count: 0 }).count, color: STATUS_COLORS[k] || "#94a3b8",
  }));
  const brandSegments = tiles.byBrand.map(b => ({
    label: b.key, value: b.count, color: BRAND_COLORS[b.key] || "#64748b",
  }));

  const sortedRegions = [...tiles.regions].sort((a, b) => {
    const ai = REGION_ORDER.indexOf(a.name);
    const bi = REGION_ORDER.indexOf(b.name);
    return (ai === -1 ? 999 : ai) - (bi === -1 ? 999 : bi);
  });

  const timelineMax = Math.max(1, ...tiles.timeline.countries.flatMap(c => c.spark));

  return (
    <div className="h-full overflow-auto p-4 sm:p-6 space-y-4 sm:space-y-6">
      {/* 1. Header */}
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Analityka</h1>
          <p className="text-sm text-muted-foreground">
            Podsumowanie <strong>{tiles.total.toLocaleString("pl-PL")}</strong> wierszy z master.csv
          </p>
        </div>
        <Badge variant="outline" className="text-[10px]">
          <BarChart3 className="h-3 w-3 mr-1" /> Na żywo · v1.2
        </Badge>
      </div>

      {/* 2. Headline insight banner */}
      {tiles.insight && !insightDismissed && (
        <div className="flex items-start gap-3 rounded-md border border-amber-300 dark:border-amber-900/40 bg-amber-50/40 dark:bg-amber-950/20 px-4 py-2.5">
          <AlertTriangle className="h-4 w-4 text-amber-600 mt-0.5 shrink-0" />
          <div className="flex-1 text-sm">
            <strong className="text-amber-900 dark:text-amber-200 font-mono">{tiles.insight.country}:</strong>{" "}
            <span className="text-amber-800 dark:text-amber-300">{tiles.insight.text}</span>
          </div>
          <button
            onClick={() => setInsightDismissed(true)}
            className="text-amber-600 hover:text-amber-800 text-xs"
            aria-label="Dismiss"
          >
            ✕
          </button>
        </div>
      )}

      {/* 3. KPI strip */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6 sm:gap-4">
        <KpiTile label="Wiersze" value={tiles.total.toLocaleString("pl-PL")} icon={Layers} />
        <KpiTile label="Kraje" value={tiles.countryCount} icon={MapPin} />
        <KpiTile label="Marki (brand)" value={tiles.brandCount} icon={Tag} />
        <KpiTile label="FROZEN" value={`${tiles.frozenPct}%`} hint={`${tiles.frozenCount.toLocaleString("pl-PL")} zweryfikowanych`} icon={Building2} />
        <KpiTile
          label="Kraje z PowerMatic"
          value={`${tiles.pmKrajSize} / ${tiles.countryCount}`}
          hint={(() => {
            const noPM = [...new Set(tiles.coverage.map(c => c.kraj))].filter(k => !tiles.pmKraj.has(k));
            return noPM.length > 0 ? `${noPM.join(", ")} — brak` : null;
          })()}
          icon={Sparkles}
          accent="violet"
        />
        <KpiTile
          label="Firmy z PowerMatic"
          value={tiles.pmCount}
          hint={`${tiles.total ? Math.round(100 * tiles.pmCount / tiles.total) : 0}% bazy`}
          icon={Zap}
          accent="violet"
        />
      </div>

      {/* 4. Hero card: Kraje × PowerMatic */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between gap-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-violet-500" />
              Kraje × PowerMatic
              <span className="ml-auto text-xs font-mono tabular-nums text-muted-foreground font-normal">
                {tiles.pmCount} PM · {tiles.pmKrajSize}/{tiles.countryCount} kraje
              </span>
            </CardTitle>
            <div className="flex items-center gap-1 rounded-md border p-0.5">
              <button
                onClick={() => setPmView("heatmap")}
                className={cn("px-2 py-0.5 text-xs rounded", pmView === "heatmap" ? "bg-muted" : "text-muted-foreground hover:text-foreground")}
              >
                Heatmap
              </button>
              <button
                onClick={() => setPmView("stacked")}
                className={cn("px-2 py-0.5 text-xs rounded", pmView === "stacked" ? "bg-muted" : "text-muted-foreground hover:text-foreground")}
              >
                Stacked
              </button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {pmView === "heatmap"
            ? <PowerMaticHeatmap countries={tiles.pmMatrix.countries} max={tiles.pmMatrix.max} />
            : <PowerMaticStacked countries={tiles.pmMatrix.countries} max={tiles.pmMatrix.max} />
          }
        </CardContent>
      </Card>

      {/* 5. Region rollup */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {sortedRegions.map(r => <RegionCard key={r.name} region={r} />)}
      </div>

      {/* 6. Research ROI callout */}
      <ResearchROICard
        anomalies={tiles.anomalies.anomalies}
        unverified={tiles.anomalies.unverified}
        ideal={tiles.anomalies.ideal}
      />

      {/* 7. Coverage + Status */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Pokrycie FROZEN wg kraju</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {tiles.coverage.map(row => <CoverageStackedBar key={row.kraj} row={row} />)}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Status mix</CardTitle>
          </CardHeader>
          <CardContent>
            <Donut
              segments={statusSegments}
              centerLabel="statusów"
              centerValue={tiles.total.toLocaleString("pl-PL")}
            />
          </CardContent>
        </Card>
      </div>

      {/* 8. Brand + Tier */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Marki (brand classifier)</CardTitle>
          </CardHeader>
          <CardContent>
            {tiles.byBrand.length === 0 ? (
              <p className="text-sm text-muted-foreground">Brak wierszy z rozpoznawalną marką.</p>
            ) : (
              <Donut
                segments={brandSegments}
                centerLabel="brandów"
                centerValue={tiles.byBrand.reduce((s, b) => s + b.count, 0).toLocaleString("pl-PL")}
              />
            )}
          </CardContent>
        </Card>
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
      </div>

      {/* 9. Verification velocity timeline */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-emerald-500" />
            Verification velocity — ostatnie 6 miesięcy
            <span className="ml-auto text-[11px] text-muted-foreground font-normal">
              {tiles.timeline.hasAnyDate ? "skumulowany FROZEN per miesiąc" : "brak dat weryfikacji"}
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {tiles.timeline.countries.length === 0 ? (
            <p className="text-sm text-muted-foreground">Brak danych.</p>
          ) : tiles.timeline.countries.map(c => (
            <TimelineRow
              key={c.kraj}
              row={c}
              max={timelineMax}
              monthLabels={tiles.timeline.months.map(m => m.key)}
            />
          ))}
        </CardContent>
      </Card>

      {/* 10. PowerMatic listings (grouped) + Claims */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="border-violet-200/60 dark:border-violet-900/40 bg-violet-50/30 dark:bg-violet-950/20">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <span className="inline-flex items-center justify-center w-5 h-5 rounded bg-violet-500/20 text-violet-600 font-bold text-[10px]">PM</span>
              Firmy z PowerMatic w ofercie
              <span className="ml-auto text-xs font-mono tabular-nums text-muted-foreground font-normal">
                {tiles.pmListings.length} z {tiles.total}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {tiles.pmListings.length === 0 ? (
              <p className="text-sm text-muted-foreground">Brak firm z PowerMatic w bazie.</p>
            ) : (
              <div className="space-y-2">
                {tiles.grouped.groups.length > 0 && (
                  <details className="rounded-md border border-violet-200 dark:border-violet-900/40 bg-white/60 dark:bg-card/60 p-2" open>
                    <summary className="cursor-pointer text-xs font-semibold text-violet-700 dark:text-violet-300 flex items-center gap-2">
                      <ChevronDown className="h-3.5 w-3.5 transition-transform group-open:rotate-180" />
                      Multi-kraj ({tiles.grouped.groups.length} grup)
                    </summary>
                    <div className="mt-2 space-y-2">
                      {tiles.grouped.groups.map(g => (
                        <div key={g.parent} className="text-xs">
                          <div className="font-medium">{g.parent} <span className="text-muted-foreground">· {g.kraje.length} kraje · {g.rows.length} firm</span></div>
                          <ul className="ml-3 mt-0.5 space-y-0.5 text-muted-foreground">
                            {g.rows.map(r => (
                              <li key={r.id_unikalne} className="flex items-center gap-1.5">
                                <span className="font-mono text-[10px] bg-muted px-1 rounded">{r.kraj}</span>
                                <span className="truncate">{r.nazwa_firmy}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  </details>
                )}
                <div className="flex flex-wrap gap-2">
                  {tiles.grouped.singles.map((r) => (
                    <div
                      key={r.id_unikalne}
                      className={cn(
                        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border",
                        r.brand_variant === "PowerMatic + Hawk"
                          ? "bg-violet-100 dark:bg-violet-950/60 text-violet-700 dark:text-violet-300 border-violet-300 dark:border-violet-800"
                          : "bg-white dark:bg-card text-violet-700 dark:text-violet-300 border-violet-200 dark:border-violet-900/40"
                      )}
                      title={`${r.nazwa_firmy} · ${r.marki_nabijarki}`}
                    >
                      <span className="font-mono text-[10px] opacity-60">{r.kraj}</span>
                      <span className="truncate max-w-[180px]">{r.nazwa_firmy}</span>
                      <span className="text-[9px] uppercase tracking-wider opacity-70">·{r.brand_variant}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="border-amber-200/60 dark:border-amber-900/40 bg-amber-50/30 dark:bg-amber-950/20">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <span className="inline-flex items-center justify-center w-5 h-5 rounded-full bg-amber-500/20 text-amber-600">★</span>
              Twierdzą że są dystrybutorami
              <span className="ml-auto text-xs font-mono tabular-nums text-muted-foreground font-normal">
                {tiles.claims.length} z {tiles.total}
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {tiles.claims.length === 0 ? (
              <p className="text-sm text-muted-foreground">Brak firm deklarujących dystrybucję.</p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-80 overflow-auto">
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
      </div>

      {/* 11. Top firms per country (consolidated, <details> tree) */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Bird className="h-4 w-4 text-indigo-500" />
            Top firm wg kraju (wg confidence_wolumen)
            <span className="ml-auto text-[11px] text-muted-foreground font-normal">
              kliknij kraj aby rozwinąć
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {tiles.topByCountryList.length === 0 ? (
            <p className="text-sm text-muted-foreground">Brak danych.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {tiles.topByCountryList
                .slice()
                .sort((a, b) => {
                  // Sort by PM-share desc if data available
                  const pmA = tiles.pmMatrix.countries.find(c => c.kraj === a.country);
                  const pmB = tiles.pmMatrix.countries.find(c => c.kraj === b.country);
                  return (pmB?.pmPct || 0) - (pmA?.pmPct || 0) || a.country.localeCompare(b.country);
                })
                .map(g => (
                <details key={g.country} className="group border border-slate-200 dark:border-border rounded-md">
                  <summary className="cursor-pointer px-3 py-1.5 flex items-center gap-2 text-[12px] font-medium hover:bg-slate-50 dark:hover:bg-muted/40">
                    <span className="font-mono text-[10px] tabular-nums bg-indigo-100 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 px-1.5 py-0.5 rounded">
                      {g.country}
                    </span>
                    <span className="text-muted-foreground">{g.rows.length} firm</span>
                    <span className="ml-auto text-[10px] group-open:rotate-90 transition-transform">▶</span>
                  </summary>
                  <ol className="px-3 py-2 space-y-0.5 text-[11.5px]">
                    {g.rows.map((r, i) => (
                      <li key={r.id_unikalne} className="flex items-center gap-2 truncate">
                        <span className="text-[10px] font-mono tabular-nums text-muted-foreground w-4">{i + 1}.</span>
                        <span className="flex-1 truncate font-medium">{r.nazwa_firmy}</span>
                        <span className="text-[10px] text-muted-foreground tabular-nums">
                          {r.confidence_wolumen || r.wolumen}
                        </span>
                      </li>
                    ))}
                  </ol>
                </details>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
