// CountryPills.jsx — small pill buttons for selecting the active country.
//
// This is a TOP-LEVEL control (above the table) that filters the data by
// the `kraj` column. The `kraj` column itself is intentionally NOT exposed
// in CollapsibleFilters / FilterInput / ActiveFilterChips — country is a
// primary axis (it determines which per-country URL/keyword data lookups
// the hooks fire), so the pill bar here is the canonical way to switch
// countries. The "leave the column header as-is" rule still applies — the
// column header in the data table does not get a per-column filter input
// for `kraj`; this pill bar is the only country selection UI.

import { useMemo } from "react";
import { cn } from "@/lib/utils";

// Order mirrors tools/config.py:COUNTRY_ORDER (PL first, then alphabetical).
// RS kept for "competitive intel" context but styled as out-of-scope.
const COUNTRIES = [
  { iso: "PL", name: "Polska" },
  { iso: "CZ", name: "Czechy" },
  { iso: "SK", name: "Słowacja" },
  { iso: "RO", name: "Rumunia" },
  { iso: "LT", name: "Litwa" },
  { iso: "LV", name: "Łotwa" },
  { iso: "EE", name: "Estonia" },
  { iso: "FR", name: "Francja" },
  { iso: "MD", name: "Mołdawia" },
  { iso: "BG", name: "Bułgaria" },
  { iso: "SI", name: "Słowenia" },
  { iso: "HR", name: "Chorwacja" },
  { iso: "RS", name: "Serbia (out-of-scope)" },
];

const ISO_TO_NAME = COUNTRIES.reduce((acc, c) => {
  acc[c.iso] = c.name;
  return acc;
}, {});

export function CountryPills({
  rows = [],
  activeIso = null,
  onSelect,
  className = "",
}) {
  // Count rows per country from the data actually loaded. Only countries
  // with rows >= 1 are shown as "available" pills (others stay in the list
  // but get a faint style + zero count, so the layout is stable).
  const counts = useMemo(() => {
    const map = new Map();
    for (const r of rows) {
      const k = (r?.kraj || "").toString().trim().toUpperCase();
      if (!k) continue;
      map.set(k, (map.get(k) || 0) + 1);
    }
    return map;
  }, [rows]);

  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-1.5 px-3 py-2 border-b border-border/60 bg-muted/20 touch-scroll-x",
        className
      )}
      role="toolbar"
      aria-label="Wybór kraju"
    >
      <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mr-1.5 select-none shrink-0">
        Kraj:
      </span>

      {/* "Wszystkie" — clears the country filter */}
      <button
        type="button"
        onClick={() => onSelect?.(null)}
        aria-pressed={!activeIso}
        title="Pokaż wszystkie kraje (wyczyść filtr kraju)"
        className={cn(
          "inline-flex items-center justify-center gap-1 min-h-[36px] sm:min-h-[28px] px-3 sm:px-2.5 py-1 rounded-full text-[11px] font-medium border transition-colors cursor-pointer",
          !activeIso
            ? "bg-primary text-primary-foreground border-primary shadow-sm"
            : "bg-card text-card-foreground border-border hover:bg-muted/70"
        )}
      >
        <span>Wszystkie</span>
        <span
          className={cn(
            "font-mono text-[10px] tabular-nums px-1.5 py-px rounded-full",
            !activeIso ? "bg-primary-foreground/20 text-primary-foreground" : "text-muted-foreground opacity-70"
          )}
        >
          {rows.length}
        </span>
      </button>

      {COUNTRIES.map(({ iso, name }) => {
        const count = counts.get(iso) || 0;
        const on = activeIso === iso;
        const hasRows = count > 0;
        return (
          <button
            key={iso}
            type="button"
            onClick={() => onSelect?.(iso)}
            disabled={!hasRows}
            aria-pressed={on}
            title={name}
            data-iso={iso}
            className={cn(
              "inline-flex items-center justify-center gap-1 min-h-[36px] sm:min-h-[28px] px-3 sm:px-2.5 py-1 rounded-full text-[11px] font-medium border transition-colors",
              on
                ? "bg-primary text-primary-foreground border-primary shadow-sm cursor-pointer"
                : hasRows
                  ? "bg-card text-card-foreground border-border hover:bg-muted/70 cursor-pointer"
                  : "bg-card/40 text-muted-foreground/50 border-border/40 cursor-not-allowed"
            )}
          >
            <span className="font-mono font-semibold tracking-tight">{iso}</span>
            {count > 0 && (
              <span
                className={cn(
                  "font-mono text-[10px] tabular-nums px-1.5 py-px rounded-full",
                  on ? "bg-primary-foreground/20 text-primary-foreground" : "text-muted-foreground opacity-70"
                )}
              >
                {count}
              </span>
            )}
          </button>
        );
      })}

      {/* Hidden helper for tests / screen-reader fallback */}
      {activeIso && (
        <span data-country-label className="sr-only">
          Wybrano: {ISO_TO_NAME[activeIso] || activeIso}
        </span>
      )}
    </div>
  );
}

export default CountryPills;
