import { useMemo } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { topValues } from "@/lib/views";
import { classifyBrand } from "@/lib/brand";

/**
 * QuickChips — one-click toggle chips for a single column's top values.
 *
 * Props:
 *   columnId — column to derive values from. Use "__brand" for the
 *              brand classifier (computed from row text fields).
 *   rows     — full dataset (used to compute top values)
 *   filter   — current filter value for this column
 *   onToggle — (value) => void  (adds/removes the value from filter)
 *   limit    — max chips to show (default 6)
 *   label    — display label override
 */
export function QuickChips({ columnId, rows, filter, onToggle, limit = 6, label }) {
  const values = useMemo(() => {
    if (columnId === "__brand") {
      // Brand is a synthetic column — count via classifyBrand().
      const counts = new Map();
      for (const row of rows) {
        const b = classifyBrand(row);
        if (b === "—") continue;
        counts.set(b, (counts.get(b) || 0) + 1);
      }
      return [...counts.entries()]
        .sort((a, b) => b[1] - a[1])
        .slice(0, limit)
        .map(([value, count]) => ({ value, count }));
    }
    return topValues(rows, columnId, limit);
  }, [rows, columnId, limit]);

  if (values.length === 0) return null;

  const active = Array.isArray(filter) ? new Set(filter) : filter ? new Set([filter]) : new Set();

  return (
    <div className="flex items-center gap-1.5 min-w-0">
      {label && (
        <span className="text-[10px] uppercase tracking-wider text-muted-foreground shrink-0">
          {label}
        </span>
      )}
      <div className="flex items-center gap-1 flex-wrap">
        {values.map(({ value, count }) => {
          const isActive = active.has(value);
          return (
            <motion.button
              key={value}
              whileTap={{ scale: 0.96 }}
              onClick={() => onToggle?.(value)}
              className={cn(
                "inline-flex items-center gap-1 rounded-full border px-3 sm:px-2.5 py-1 text-xs font-medium transition-colors min-h-[32px]",
                isActive
                  ? "bg-primary text-primary-foreground border-primary shadow-sm"
                  : "bg-background text-muted-foreground hover:bg-accent hover:text-foreground"
              )}
              title={isActive ? `Wyłącz filtr: ${value}` : `Filtruj: ${value} (${count})`}
              aria-pressed={isActive}
            >
              <span className="truncate max-w-[7rem]">{value}</span>
              <span className="text-[10px] tabular-nums opacity-60">{count}</span>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}