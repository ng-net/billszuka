import { motion } from "framer-motion";
import { formatNumber } from "@/lib/utils";

export function StatusBar({
  totalRows,
  filteredRows,
  visibleColumns,
  totalColumns,
  activeFilters,
  sortStack,
  parseTimeMs,
  density,
  fileMeta,
}) {
  return (
    <div className="border-t bg-card/50 backdrop-blur-sm">
      <div className="px-3 sm:px-4 h-8 flex items-center justify-between text-xs text-muted-foreground gap-4 overflow-x-auto no-scrollbar">
        <div className="flex items-center gap-3 shrink-0">
          <span className="tabular-nums">
            <motion.span
              key={filteredRows}
              initial={{ opacity: 0, y: -2 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.15 }}
              className="text-foreground font-medium"
            >
              {formatNumber(filteredRows)}
            </motion.span>
            {" "}z {formatNumber(totalRows)} wierszy
          </span>
          <span className="text-muted-foreground/40">·</span>
          <span className="tabular-nums">
            <span className="text-foreground">{visibleColumns}</span>/{totalColumns} kolumn
          </span>
          {activeFilters > 0 && (
            <>
              <span className="text-muted-foreground/40">·</span>
              <span className="tabular-nums">
                <span className="text-foreground">{activeFilters}</span>{" "}
                {activeFilters === 1 ? "filtr" : "filtrów"}
              </span>
            </>
          )}
          {sortStack.length > 0 && (
            <>
              <span className="text-muted-foreground/40">·</span>
              <span className="hidden md:inline">
                Sort: {sortStack.map((s) => `${s.id} ${s.desc ? "↓" : "↑"}`).join(" · ")}
              </span>
            </>
          )}
        </div>
        <div className="flex items-center gap-3 shrink-0 tabular-nums">
          <span className="hidden sm:inline">
            {parseTimeMs > 0 && `Parsed in ${(parseTimeMs / 1000).toFixed(2)}s`}
          </span>
          <span className="text-muted-foreground/40 hidden sm:inline">·</span>
          <span className="capitalize">{density}</span>
          {fileMeta?.name && (
            <>
              <span className="text-muted-foreground/40">·</span>
              <span className="truncate max-w-[200px]" title={fileMeta.name}>
                {fileMeta.name}
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
