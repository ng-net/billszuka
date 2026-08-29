import { useState, useMemo } from "react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Input } from "@/components/ui/input";
import { Columns3, Search, RotateCcw } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { getColumnLabel } from "@/lib/schema";
import { cn } from "@/lib/utils";

export function ColumnToggle({ columns, visibility, onChange, schema }) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!search) return columns;
    const q = search.toLowerCase();
    return columns.filter((c) => {
      const label = getColumnLabel(c).toLowerCase();
      return c.toLowerCase().includes(q) || label.includes(q);
    });
  }, [columns, search]);

  const visibleCount = columns.filter((c) => visibility[c] !== false).length;

  const toggle = (col) => {
    onChange({ ...visibility, [col]: visibility[col] === false ? true : false });
  };

  const showAll = () => {
    const next = {};
    columns.forEach((c) => (next[c] = true));
    onChange(next);
  };

  const hideAll = () => {
    const next = {};
    columns.forEach((c) => (next[c] = false));
    onChange(next);
  };

  const getType = (col) => schema?.find((s) => s.id === col)?.type;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className="gap-1.5">
          <Columns3 className="h-4 w-4" />
          <span className="hidden md:inline">Kolumny</span>
          <span className="text-xs text-muted-foreground tabular-nums">
            {visibleCount}/{columns.length}
          </span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[min(18rem,calc(100vw-2rem))] p-0" align="end">
        <div className="p-3 border-b space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium">Widoczne kolumny</p>
            <button
              onClick={showAll}
              className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1"
              title="Reset do wszystkich"
            >
              <RotateCcw className="h-3 w-3" />
              Reset
            </button>
          </div>
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground/50" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Szukaj kolumny…"
              className="h-7 pl-7 text-xs"
            />
          </div>
          <div className="flex items-center gap-1.5 text-xs">
            <button onClick={showAll} className="text-primary hover:underline">
              Pokaż wszystkie
            </button>
            <span className="text-muted-foreground/50">·</span>
            <button
              onClick={hideAll}
              className="text-muted-foreground hover:text-foreground"
            >
              Ukryj wszystkie
            </button>
          </div>
        </div>
        <ScrollArea className="h-80">
          <div className="p-2 space-y-0.5">
            <AnimatePresence initial={false}>
              {filtered.map((col) => {
                const isVisible = visibility[col] !== false;
                const type = getType(col);
                return (
                  <motion.label
                    key={col}
                    layout
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.1 }}
                    className={cn(
                      "flex items-center gap-2 px-2 py-1.5 rounded cursor-pointer hover:bg-muted/50 text-sm",
                      !isVisible && "opacity-60"
                    )}
                  >
                    <Checkbox
                      checked={isVisible}
                      onCheckedChange={() => toggle(col)}
                    />
                    <div className="flex-1 min-w-0 flex flex-col">
                      <span className="truncate text-xs font-medium">{getColumnLabel(col)}</span>
                      <span className="truncate text-[10px] text-muted-foreground/60 font-mono">{col}</span>
                    </div>
                    {type && type !== "text" && (
                      <span className="text-[10px] text-muted-foreground uppercase tracking-wide">
                        {type}
                      </span>
                    )}
                  </motion.label>
                );
              })}
            </AnimatePresence>
            {filtered.length === 0 && (
              <p className="text-xs text-muted-foreground text-center py-8">
                Brak kolumn
              </p>
            )}
          </div>
        </ScrollArea>
      </PopoverContent>
    </Popover>
  );
}
