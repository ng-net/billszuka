import { useState } from "react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Eye, BookmarkPlus, Check, LayoutGrid } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * ViewSwitcher — saved views for the table.
 *
 * Props:
 *   views       — array of saved views { id, name, filters, columns? }
 *   activeView  — id of currently active view (null = "Wszystko")
 *   onActivate  — (view | null) => void  (null = reset to no view)
 *   onSave      — (name) => void  (saves current filters+columns as new view)
 *   onDelete    — (viewId) => void
 */
export function ViewSwitcher({ views = [], activeView, onActivate, onSave, onDelete }) {
  const [open, setOpen] = useState(false);
  const [saveName, setSaveName] = useState("");

  const active = views.find((v) => v.id === activeView);
  const label = active?.name || "Wszystko";

  const handleSave = () => {
    const name = saveName.trim();
    if (!name) return;
    onSave?.(name);
    setSaveName("");
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className="gap-1.5">
          <LayoutGrid className="h-4 w-4" />
          <span className="hidden sm:inline">{label}</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[min(18rem,calc(100vw-2rem))] p-0" align="end">
        <div className="p-3 border-b space-y-2">
          <p className="text-sm font-medium">Widoki</p>
          <button
            onClick={() => {
              onActivate?.(null);
              setOpen(false);
            }}
            className={cn(
              "flex items-center gap-2 w-full px-2 py-1.5 rounded text-sm hover:bg-muted/60",
              !activeView && "bg-muted"
            )}
          >
            <Eye className="h-3.5 w-3.5 opacity-60" />
            <span className="flex-1 text-left">Wszystko</span>
            {!activeView && <Check className="h-3.5 w-3.5 text-primary" />}
          </button>
        </div>

        <div className="max-h-72 overflow-auto py-1">
          {views.length === 0 ? (
            <p className="text-xs text-muted-foreground text-center py-6">
              Brak zapisanych widoków
            </p>
          ) : (
            views.map((v) => (
              <div
                key={v.id}
                className={cn(
                  "flex items-center gap-2 px-3 py-1.5 text-sm hover:bg-muted/40",
                  v.id === activeView && "bg-muted"
                )}
              >
                <button
                  onClick={() => {
                    onActivate?.(v);
                    setOpen(false);
                  }}
                  className="flex-1 flex items-center gap-2 text-left"
                >
                  <Eye className="h-3.5 w-3.5 opacity-60" />
                  <span className="truncate">{v.name}</span>
                </button>
                {v.id === activeView && <Check className="h-3.5 w-3.5 text-primary" />}
                {v.userDefined && onDelete && (
                  <button
                    onClick={() => onDelete?.(v.id)}
                    className="text-xs text-muted-foreground hover:text-destructive"
                    title="Usuń widok"
                  >
                    ×
                  </button>
                )}
              </div>
            ))
          )}
        </div>

        {onSave && (
          <div className="p-3 border-t space-y-2">
            <p className="text-xs text-muted-foreground">Zapisz bieżący widok</p>
            <div className="flex gap-1.5">
              <Input
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSave()}
                placeholder="np. PL Big players"
                className="h-7 text-xs"
              />
              <Button
                size="xs"
                variant="outline"
                onClick={handleSave}
                disabled={!saveName.trim()}
              >
                <BookmarkPlus className="h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}