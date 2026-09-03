import { useMemo } from "react";
import { X, RotateCcw, Filter } from "lucide-react";
import { cn } from "@/lib/utils";

const COLUMN_LABELS = {
  __brand: "Marka",
  // kraj removed — country column has no filtering option
  tier: "Rola",
  wolumen: "Wolumen",
  confidence_wolumen: "Pewność",
  marki_nabijarki: "Marki maszynek",
  marka_wlasna_oem: "Marka własna OEM",
  powinowactwo_nabijarki: "Powinowactwo",
  cross_sell_potential: "Cross-sell",
  kategoria: "Kategoria",
  kanal_sprzedaży: "Kanał",
  rok_zalozenia: "Rok założenia",
  miasto: "Miasto",
  sourcing: "Sourcing",
  zrodlo_danych: "Źródło",
};

export function ActiveFilterChips({
  filters = {},
  globalSearch = "",
  onRemoveFilter,
  onClearGlobalSearch,
  onResetAll,
  className,
}) {
  const chips = useMemo(() => {
    const list = [];

    // Global search chip
    if (globalSearch && String(globalSearch).trim()) {
      list.push({
        id: "__global",
        type: "global",
        label: "Szukaj",
        display: `"${globalSearch.trim()}"`,
        onRemove: () => onClearGlobalSearch?.(),
      });
    }

    // Column filter chips
    for (const [colId, val] of Object.entries(filters)) {
      if (colId === "kraj") continue; // country filter intentionally not shown
      if (val == null || val === "") continue;

      const colName = COLUMN_LABELS[colId] || colId.replace(/_/g, " ");

      if (Array.isArray(val)) {
        if (val.length === 0) continue;
        for (const item of val) {
          list.push({
            id: `${colId}-${item}`,
            type: "array-item",
            colId,
            valItem: item,
            label: colName,
            display: String(item),
            onRemove: () => onRemoveFilter?.(colId, item),
          });
        }
      } else if (typeof val === "object") {
        if (val.min != null || val.max != null) {
          const display = `${val.min ?? "min"} – ${val.max ?? "max"}`;
          list.push({
            id: `${colId}-numrange`,
            type: "object",
            colId,
            label: colName,
            display,
            onRemove: () => onRemoveFilter?.(colId),
          });
        } else if (val.from != null || val.to != null) {
          const display = `${val.from ?? "od"} – ${val.to ?? "do"}`;
          list.push({
            id: `${colId}-daterange`,
            type: "object",
            colId,
            label: colName,
            display,
            onRemove: () => onRemoveFilter?.(colId),
          });
        }
      } else {
        list.push({
          id: `${colId}-scalar`,
          type: "scalar",
          colId,
          label: colName,
          display: String(val),
          onRemove: () => onRemoveFilter?.(colId),
        });
      }
    }

    return list;
  }, [filters, globalSearch, onRemoveFilter, onClearGlobalSearch]);

  if (chips.length === 0) return null;

  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-1.5 px-3 py-1.5 bg-muted/40 border-b border-border/60 text-xs animate-in fade-in duration-150",
        className
      )}
    >
      <div className="flex items-center gap-1 text-[11px] font-semibold text-muted-foreground uppercase tracking-wider mr-1 shrink-0">
        <Filter size={11} className="text-brand" />
        <span>Aktywne ({chips.length}):</span>
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        {chips.map((chip) => (
          <span
            key={chip.id}
            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium bg-brand-muted text-brand-muted-foreground border border-brand-muted-foreground/20 hover:border-brand-muted-foreground/30 transition-colors"
          >
            <span className="opacity-70 text-[10.5px] uppercase font-semibold truncate max-w-[8rem]">
              {chip.label}:
            </span>
            <span className="font-semibold truncate max-w-[10rem]">{chip.display}</span>
            <button
              type="button"
              onClick={chip.onRemove}
              aria-label={`Usuń filtr ${chip.label}: ${chip.display}`}
              title={`Usuń filtr ${chip.label}: ${chip.display}`}
              className="ml-0.5 inline-flex h-7 w-7 sm:h-6 sm:w-6 items-center justify-center rounded hover:bg-brand-muted-foreground/20 text-brand transition-colors cursor-pointer"
            >
              <X size={12} />
            </button>
          </span>
        ))}

        <button
          type="button"
          onClick={onResetAll}
          className="inline-flex items-center justify-center gap-1 min-h-[32px] sm:min-h-[28px] text-[11px] text-error-muted-foreground hover:underline ml-1.5 px-2 sm:px-1.5 py-1 sm:py-0.5 rounded hover:bg-error-muted transition-colors cursor-pointer font-medium"
          title="Wyczyść wszystkie nałożone filtry"
        >
          <RotateCcw size={11} />
          <span>Resetuj</span>
        </button>
      </div>
    </div>
  );
}

export default ActiveFilterChips;
