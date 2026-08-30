import React, { useState } from "react";
import { Filter, PanelLeftClose, PanelLeftOpen } from "lucide-react";

function valueMatches(value, filterVal) {
  if (!filterVal) return false;
  if (Array.isArray(filterVal)) return filterVal.includes(value);
  return filterVal === value;
}

export function CollapsibleFilters({
  groups,
  filters = {},
  onToggle,
  onToggleCollapse,
  collapsed: collapsedProp,
  defaultCollapsed = false,
  labels = {},
  className = "",
}) {
  const DEFAULT_LABELS = {
    kraj: "Kraj",
    marki_nabijarki: "Marka",
    tier: "Rola",
    wolumen: "Wolumen",
    cross_sell_potential: "Cross-sell",
    powinowactwo_nabijarki: "Powinowactwo",
    kategoria: "Kategoria",
    kanal_sprzedaży: "Kanał",
    rok_zalozenia: "Rok",
  };
  const [internalCollapsed, setInternalCollapsed] = useState(defaultCollapsed);
  const collapsed = collapsedProp !== undefined ? collapsedProp : internalCollapsed;
  const setCollapsed = (v) => {
    if (collapsedProp === undefined) setInternalCollapsed(v);
    onToggleCollapse?.(v);
  };

  const groupKeys = Object.keys(groups);

  return (
    <div
      data-collapsed={collapsed ? "true" : "false"}
      className={
        "bg-white dark:bg-card border border-slate-200 dark:border-border rounded-xl shadow-sm " +
        className
      }
    >
      <div className="flex items-center justify-between gap-2 px-3 py-2 border-b border-slate-100 dark:border-border">
        <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          <Filter size={12} className="text-indigo-500" />
          Filtry
          <span className="ml-1 text-[10px] text-slate-400 normal-case font-normal">
            {Object.keys(filters).length} aktywne
          </span>
        </div>
        <button
          type="button"
          onClick={() => setCollapsed(!collapsed)}
          aria-expanded={!collapsed}
          aria-label={collapsed ? "Rozwiń filtry" : "Zwiń filtry"}
          title={collapsed ? "Rozwiń filtry" : "Zwiń filtry"}
          className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-600 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-400 px-2 py-1 rounded-md hover:bg-slate-100 dark:hover:bg-muted transition-colors"
        >
          {collapsed ? (
            <>
              <PanelLeftOpen size={13} /> Rozwiń
            </>
          ) : (
            <>
              <PanelLeftClose size={13} /> Zwiń
            </>
          )}
        </button>
      </div>

      {!collapsed ? (
        <div className="p-3 space-y-3">
          {groupKeys.map((key) => {
            const label = labels[key] || DEFAULT_LABELS[key] || key;
            const values = groups[key] || [];
            const active = filters[key];
            const activeCount = Array.isArray(active)
              ? active.length
              : active
              ? 1
              : 0;
            return (
              <div key={key}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10.5px] font-bold uppercase tracking-wider text-slate-500">
                    {label}
                  </span>
                  {activeCount > 0 && (
                    <span className="text-[10px] font-semibold tabular-nums bg-indigo-100 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 px-1.5 py-0.5 rounded-full">
                      {activeCount}
                    </span>
                  )}
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {values.map((v) => {
                    const on = valueMatches(v, active);
                    return (
                      <button
                        key={v}
                        type="button"
                        onClick={() => onToggle?.(key, v)}
                        aria-pressed={on}
                        className={
                          "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors " +
                          (on
                            ? "bg-indigo-600 text-white border-indigo-600 shadow-sm"
                            : "bg-white dark:bg-card text-slate-700 dark:text-slate-300 border-slate-200 dark:border-border hover:bg-slate-50 dark:hover:bg-muted")
                        }
                      >
                        <span className="truncate max-w-[160px]" title={v}>
                          {v}
                        </span>
                        {on && (
                          <span aria-hidden="true" className="text-white/80">
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
        <div className="px-3 py-2 flex flex-wrap items-center gap-2">
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
                className="inline-flex items-center gap-1 text-[11px] font-medium text-slate-600 dark:text-slate-400"
              >
                <span className="text-[10px] uppercase tracking-wider text-slate-400">
                  {label}
                </span>
                <span
                  className={
                    "tabular-nums font-bold " +
                    (count > 0 ? "text-indigo-600" : "text-slate-400")
                  }
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
