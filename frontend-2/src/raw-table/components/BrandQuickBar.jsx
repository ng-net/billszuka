import { useMemo } from "react";
import { Sparkles } from "lucide-react";
import { classifyBrand } from "@/lib/brand";
import { cn } from "@/lib/utils";

const BRAND_SEGMENTS = [
  { id: null, label: "Wszystko", color: "slate" },
  { id: "PowerMatic", label: "PowerMatic", color: "indigo" },
  { id: "PowerMatic + Hawk", label: "PowerMatic + Hawk", color: "gradient" },
  { id: "Hawk", label: "Hawk", color: "rose" },
  { id: "Inna", label: "Inna", color: "slate" },
];

export function BrandQuickBar({ rows = [], activeBrand, onSelectBrand, className }) {
  // Compute counts once per rows change
  const brandCounts = useMemo(() => {
    const counts = {
      total: rows.length,
      PowerMatic: 0,
      "PowerMatic + Hawk": 0,
      Hawk: 0,
      Inna: 0,
    };
    if (!rows || rows.length === 0) return counts;

    for (const r of rows) {
      const b = r.__brand || classifyBrand(r);
      if (b === "PowerMatic") counts.PowerMatic += 1;
      else if (b === "PowerMatic + Hawk") counts["PowerMatic + Hawk"] += 1;
      else if (b === "Hawk") counts.Hawk += 1;
      else if (b === "Inna") counts.Inna += 1;
    }
    return counts;
  }, [rows]);

  if (rows.length === 0) return null;

  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-1 bg-card/60 border border-border/70 rounded-lg p-1 text-xs",
        className
      )}
    >
      <div className="flex items-center gap-1.5 px-2 text-muted-foreground font-semibold uppercase tracking-wider text-[10.5px] shrink-0">
        <Sparkles size={12} className="text-indigo-500 shrink-0" />
        <span>Marka</span>
      </div>

      <div className="flex items-center gap-1 flex-wrap">
        {BRAND_SEGMENTS.map((seg) => {
          const isAll = seg.id === null;
          const isActive = isAll ? !activeBrand : activeBrand === seg.id;
          const count = isAll ? brandCounts.total : brandCounts[seg.id] || 0;

          return (
            <button
              key={seg.label}
              type="button"
              onClick={() => {
                if (isAll) {
                  onSelectBrand?.(null);
                } else {
                  // toggle off if already active
                  onSelectBrand?.(activeBrand === seg.id ? null : seg.id);
                }
              }}
              className={cn(
                "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all cursor-pointer",
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm font-semibold"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/60"
              )}
            >
              {seg.color === "indigo" && !isActive && (
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 shrink-0" />
              )}
              {seg.color === "rose" && !isActive && (
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500 shrink-0" />
              )}
              {seg.color === "gradient" && !isActive && (
                <span className="w-1.5 h-1.5 rounded-full bg-gradient-to-r from-indigo-500 to-rose-500 shrink-0" />
              )}
              <span>{seg.label}</span>
              <span
                className={cn(
                  "font-mono text-[10px] tabular-nums px-1.5 py-0.2 rounded-full",
                  isActive
                    ? "bg-primary-foreground/20 text-primary-foreground font-bold"
                    : "bg-muted text-muted-foreground"
                )}
              >
                {count.toLocaleString("pl-PL")}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default BrandQuickBar;
