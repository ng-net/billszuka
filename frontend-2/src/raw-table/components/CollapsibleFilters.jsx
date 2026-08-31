import React, { useState, useMemo } from "react";
import { Filter, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { cn } from "@/lib/utils";

function valueMatches(value, filterVal) {
  if (!filterVal) return false;
  if (Array.isArray(filterVal)) return filterVal.includes(value);
  return filterVal === value;
}

const DEFAULT_LABELS = {
  // kraj removed — country column has no filtering option
  marki_nabijarki: "Marka",
  tier: "Rola",
  wolumen: "Wolumen",
  confidence_wolumen: "Pewność",
  cross_sell_potential: "Cross-sell",
  powinowactwo_nabijarki: "Powinowactwo",
  kategoria: "Kategoria",
  kanal_sprzedaży: "Kanał",
  rok_zalozenia: "Rok",
  __brand: "Marka (AI)",
};

export function CollapsibleFilters({
  groups: groupsProp,
  rows = [],
  filters = {},
  onToggle,
  onToggleCollapse,
  collapsed: collapsedProp,
  defaultCollapsed = false,
  labels = {},
  className = "",
}) {
  const [internalCollapsed, setInternalCollapsed] = useState(defaultCollapsed);
  const collapsed = collapsedProp !== undefined ? collapsedProp : internalCollapsed;
  const setCollapsed = (v) => {
    if (collapsedProp === undefined) setInternalCollapsed(v);
    onToggleCollapse?.(v);
  };

  // If groups are provided directly (e.g. in tests or static setup), compute counts if possible.
  // Note: "kraj" is excluded from filter rendering — country column has no
  // filtering option. This applies even if a caller passes `kraj` in groupsProp.
  const dynamicGroups = useMemo(() => {
    if (groupsProp) {
      // If groups are given as { [key]: ["val1", "val2"] } or { [key]: [{value, count}] }
      const res = {};
      for (const [key, vals] of Object.entries(groupsProp)) {
        if (key === "kraj") continue; // country filter intentionally not exposed
        if (!Array.isArray(vals)) continue;
        res[key] = vals.map((v) => {
          if (typeof v === "object" && v !== null) return v;
          // compute count from rows if rows passed
          const count = rows && rows.length > 0
            ? rows.filter((r) => String(r[key] || "") === String(v)).length
            : null;
          return { value: v, count };
        });
      }
      return res;
    }

    if (!rows || rows.length === 0) return {};

    // Note: "kraj" is intentionally NOT in the filter list — country column has
    // no filtering option. Use per-country file/view as the country selector.
    const keys = ["tier", "wolumen", "powinowactwo_nabijarki", "cross_sell_potential"];
    const out = {};
    for (const k of keys) {
      const counts = new Map();
      for (const r of rows) {
        const val = (r[k] || "").toString().trim();
        if (!val || val === "brak" || val === "—") continue;
        counts.set(val, (counts.get(val) || 0) + 1);
      }
      out[k] = [...counts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10)
        .map(([value, count]) => ({ value, count }));
    }
    return out;
  }, [groupsProp, rows]);

  const groupKeys = Object.keys(dynamicGroups);

  return (
    <div
      data-collapsed={collapsed ? "true" : "false"}
      className={cn(
        "bg-card border border-border rounded-xl shadow-sm overflow-hidden",
        className
      )}
    >
      <div className="flex items-center justify-between gap-2 px-3 py-2 border-b border-border bg-muted/20">
        <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          <Filter size={12} className="text-primary" />
          <span>Filtry</span>
          <span className="ml-1 text-[10px] text-muted-foreground/70 normal-case font-normal">
            {Object.keys(filters).filter((k) => filters[k] != null && filters[k] !== "").length} aktywne
          </span>
        </div>
        <button
          type="button"
          onClick={() => setCollapsed(!collapsed)}
          aria-expanded={!collapsed}
          aria-label={collapsed ? "Rozwiń filtry" : "Zwiń filtry"}
          title={collapsed ? "Rozwiń filtry" : "Zwiń filtry"}
          className="inline-flex items-center gap-1 text-[11px] font-medium text-muted-foreground hover:text-foreground px-2 py-1 rounded-md hover:bg-muted transition-colors cursor-pointer"
        >
          {collapsed ? (
            <>
              <PanelLeftOpen size={13} /> <span>Rozwiń</span>
            </>
          ) : (
            <>
              <PanelLeftClose size={13} /> <span>Zwiń</span>
            </>
          )}
        </button>
      </div>

      {!collapsed ? (
        <div className="p-3 space-y-3.5 max-h-[70vh] overflow-y-auto">
          {groupKeys.map((key) => {
            const label = labels[key] || DEFAULT_LABELS[key] || key;
            const items = dynamicGroups[key] || [];
            const active = filters[key];
            const activeCount = Array.isArray(active)
              ? active.length
              : active
              ? 1
              : 0;

            const maxCount = items.reduce((max, it) => Math.max(max, it.count || 0), 1);

            return (
              <div key={key} className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10.5px] font-bold uppercase tracking-wider text-muted-foreground">
                    {label}
                  </span>
                  {activeCount > 0 && (
                    <span className="text-[10px] font-semibold tabular-nums bg-primary/15 text-primary px-1.5 py-0.2 rounded-full">
                      {activeCount}
                    </span>
                  )}
                </div>

                <div className="flex flex-wrap gap-1.5">
                  {items.map((item) => {
                    const v = item.value;
                    const on = valueMatches(v, active);
                    const pct = item.count != null && maxCount > 0 ? Math.min(100, Math.round((item.count / maxCount) * 100)) : null;

                    return (
                      <button
                        key={v}
                        type="button"
                        onClick={() => onToggle?.(key, v)}
                        aria-pressed={on}
                        className={cn(
                          "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium border transition-all cursor-pointer",
                          on
                            ? "bg-primary text-primary-foreground border-primary shadow-sm font-semibold"
                            : "bg-card text-card-foreground border-border hover:bg-muted/70 hover:border-border/80"
                        )}
                      >
                        <span className="truncate max-w-[150px]" title={v}>
                          {v}
                        </span>

                        {/* Distribution bar indicator */}
                        {pct !== null && !on && (
                          <span className="inline-block w-8 h-1 bg-muted rounded-full overflow-hidden shrink-0">
                            <span
                              className="block h-full bg-primary/60"
                              style={{ width: `${pct}%` }}
                            />
                          </span>
                        )}

                        {item.count != null && (
                          <span
                            className={cn(
                              "font-mono text-[10px] tabular-nums px-1 py-0.2 rounded-full",
                              on ? "bg-primary-foreground/20 text-primary-foreground" : "text-muted-foreground opacity-70"
                            )}
                          >
                            {item.count}
                          </span>
                        )}

                        {on && (
                          <span aria-hidden="true" className="text-primary-foreground/80 font-bold ml-0.5">
                            ✕
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="px-3 py-2 flex flex-wrap items-center gap-3">
          {groupKeys.map((key) => {
            const label = labels[key] || DEFAULT_LABELS[key] || key;
            const active = filters[key];
            const count = Array.isArray(active)
              ? active.length
              : active
              ? 1
              : 0;
            return (
              <span
                key={key}
                className="inline-flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground"
              >
                <span className="text-[10px] uppercase tracking-wider text-muted-foreground/70">
                  {label}:
                </span>
                <span
                  className={cn(
                    "tabular-nums font-bold",
                    count > 0 ? "text-primary" : "text-muted-foreground/60"
                  )}
                >
                  {count}
                </span>
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default CollapsibleFilters;
