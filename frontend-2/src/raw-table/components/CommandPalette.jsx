import { useState, useMemo } from "react";
import { CommandDialog, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList, CommandShortcut } from "@/components/ui/command";
import {
  ArrowUpDown,
  EyeOff,
  Eye,
  XCircle,
  Trash2,
  Upload,
  Moon,
  Sun,
  Monitor,
  Rows3,
  Rows4,
} from "lucide-react";
import { getColumnLabel } from "@/lib/schema";

export function CommandPalette({ open, onOpenChange, context, onAction }) {
  const [query, setQuery] = useState("");

  // Reset query when the dialog opens — done in the change handler so
  // we don't need a setState-in-effect (the lint-compiler complains
  // about that pattern).
  const handleOpenChange = (next) => {
    if (next) setQuery("");
    onOpenChange(next);
  };

  const items = useMemo(() => {
    const list = [
      {
        group: "Akcje",
        items: [
          { id: "upload", label: "Upload CSV", icon: Upload, shortcut: "⌘O" },
          { id: "clear-filters", label: "Wyczyść filtry", icon: XCircle, shortcut: "R" },
          { id: "clear-sort", label: "Wyczyść sortowanie", icon: ArrowUpDown },
          { id: "reset", label: "Reset widoku", icon: Trash2, destructive: true },
        ],
      },
      {
        group: "Wygląd",
        items: [
          {
            id: "density-compact",
            label: "Gęstość: kompaktowa",
            icon: Rows3,
            shortcut: "D",
            active: context.density === "compact",
          },
          {
            id: "density-comfortable",
            label: "Gęstość: wygodna",
            icon: Rows4,
            shortcut: "D",
            active: context.density === "comfortable",
          },
          {
            id: "theme-light",
            label: "Motyw: jasny",
            icon: Sun,
            active: context.theme === "light",
          },
          {
            id: "theme-dark",
            label: "Motyw: ciemny",
            icon: Moon,
            active: context.theme === "dark",
          },
          {
            id: "theme-system",
            label: "Motyw: systemowy",
            icon: Monitor,
            active: context.theme === "system",
          },
        ],
      },
    ];

    if (context.columns?.length) {
      list.push({
        group: `Kolumny (${context.columns.length})`,
        items: context.columns
          .filter((c) => {
            const label = getColumnLabel(c).toLowerCase();
            return !query || c.toLowerCase().includes(query.toLowerCase()) || label.includes(query.toLowerCase());
          })
          .slice(0, 20)
          .map((c) => {
            const visible = context.visibility?.[c] !== false;
            return {
              id: `col-${c}`,
              label: `${getColumnLabel(c)} (${c})`,
              icon: visible ? Eye : EyeOff,
              type: context.schema?.find((s) => s.id === c)?.type,
              groupType: true,
            };
          }),
      });

      list.push({
        group: "Sortuj po",
        items: context.columns
          .filter((c) => {
            const label = getColumnLabel(c).toLowerCase();
            return !query || c.toLowerCase().includes(query.toLowerCase()) || label.includes(query.toLowerCase());
          })
          .slice(0, 15)
          .map((c) => ({
            id: `sort-${c}`,
            label: `${getColumnLabel(c)} (${c})`,
            icon: ArrowUpDown,
            sortCol: c,
          })),
      });
    }

    return list;
  }, [context, query]);

  return (
    <CommandDialog open={open} onOpenChange={handleOpenChange}>
      <CommandInput
        placeholder="Szukaj akcji, kolumny, sortu…"
        value={query}
        onValueChange={setQuery}
      />
      <CommandList className="max-h-[60vh]">
        <CommandEmpty>Brak wyników</CommandEmpty>
        {items.map((group) => (
          <CommandGroup key={group.group} heading={group.group}>
            {group.items.map((item) => {
              const Icon = item.icon;
              return (
                <CommandItem
                  key={item.id}
                  value={item.label}
                  onSelect={() => {
                    onAction(item);
                    onOpenChange(false);
                  }}
                  className={item.destructive ? "text-destructive" : item.active ? "bg-accent" : ""}
                >
                  <Icon className="h-4 w-4 opacity-70" />
                  <span className="flex-1 font-mono text-xs">{item.label}</span>
                  {item.type && (
                    <span className="text-[10px] text-muted-foreground uppercase tracking-wider">
                      {item.type}
                    </span>
                  )}
                  {item.shortcut && (
                    <CommandShortcut>{item.shortcut}</CommandShortcut>
                  )}
                </CommandItem>
              );
            })}
          </CommandGroup>
        ))}
      </CommandList>
    </CommandDialog>
  );
}
