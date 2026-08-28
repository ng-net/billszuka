import { useState } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { ArrowUp, ArrowDown, ArrowUpDown, GripVertical, X, Filter as FilterIcon } from "lucide-react";
import { flexRender } from "@tanstack/react-table";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { FilterInput } from "./FilterInput";
import { cn } from "@/lib/utils";

/**
 * `column` is a TanStack v8 Column object (from getVisibleLeafColumns()),
 * not a Header. Columns have .id, .columnDef, .getCanSort(), .getIsSorted() directly.
 */
export function SortableHeader({ column, sortIndex, stickyLeft, onContextMenu, onClick, focused, onHide, filterProps, isDivider }) {
  // Hooks must be called unconditionally on every render. The previous
  // version had `if (!column) return null` before `useSortable` — a rules
  // of-hooks violation that could crash if column was ever falsy.
  const colId = column?.id ?? "__none__";
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: colId });

  if (!column) return null;

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const canSort = column.getCanSort();
  const sortDir = column.getIsSorted(); // "asc" | "desc" | false
  const type = column.columnDef.meta?.type;
  const width = column.columnDef.meta?.width;
  const minWidth = column.columnDef.meta?.minWidth;
  const align = column.columnDef.meta?.align;

  const handleClick = (e) => {
    if (!canSort) return;
    const handler = column.getToggleSortingHandler();
    if (handler) handler(e);
  };

  return (
    <th
      ref={setNodeRef}
      style={{
        ...style,
        width: `${width}px`,
        minWidth: `${minWidth}px`,
        ...(stickyLeft != null ? { left: stickyLeft } : {}),
      }}
      className={cn(
        "group relative overflow-hidden text-left align-middle font-medium text-muted-foreground select-none",
        isDivider ? "border-r-[6px] border-border" : "border-r border-border",
        focused && "ring-2 ring-primary/50 ring-inset",
        stickyLeft != null && "sticky z-20 bg-card lg:static"
      )}
      onContextMenu={(e) => onContextMenu?.(e, column)}
    >
      <div
        className={cn(
          "flex items-center gap-1 px-3 py-2",
          align === "right" && "justify-end",
          align === "center" && "justify-center"
        )}
      >
        <button
          {...attributes}
          {...listeners}
          className="opacity-60 md:opacity-0 md:group-hover:opacity-100 transition-opacity cursor-grab active:cursor-grabbing -ml-1 mr-0.5 touch-none"
          title="Przeciągnij, żeby zmienić kolejność"
        >
          <GripVertical className="h-3 w-3 text-muted-foreground/40" />
        </button>

        <button
          onClick={(e) => {
            handleClick(e);
            onClick?.(colId);
          }}
          className={cn(
            "flex items-center gap-1 text-xs font-medium uppercase tracking-wide flex-1 min-w-0",
            canSort && "cursor-pointer hover:text-foreground",
            sortDir && "text-foreground"
          )}
        >
          <span className="truncate">
            {flexRender(column.columnDef.header, column)}
          </span>
          {canSort && (
            <span className="shrink-0">
              {sortDir === "asc" && <ArrowUp className="h-3 w-3 text-primary" />}
              {sortDir === "desc" && <ArrowDown className="h-3 w-3 text-primary" />}
              {!sortDir && (
                <ArrowUpDown className="h-3 w-3 opacity-0 group-hover:opacity-30" />
              )}
            </span>
          )}
        </button>

        {sortIndex != null && sortIndex > 0 && (
          <span className="shrink-0 inline-flex items-center justify-center h-4 w-4 rounded-full bg-primary text-primary-foreground text-[10px] font-bold tabular-nums">
            {sortIndex + 1}
          </span>
        )}

        {type && type !== "text" && (
          <span className="shrink-0 text-[9px] text-muted-foreground/50 uppercase tracking-wider">
            {type}
          </span>
        )}

        {filterProps && (
          <ColumnFilterTrigger
            columnId={column.id}
            type={filterProps.type}
            value={filterProps.value}
            enumValues={filterProps.enumValues}
            onChange={filterProps.onChange}
          />
        )}

        {onHide && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onHide(colId);
            }}
            className="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity h-5 w-5 -mr-1 inline-flex items-center justify-center rounded hover:bg-destructive/10 hover:text-destructive"
            title={`Ukryj kolumnę ${colId}`}
            aria-label={`Ukryj kolumnę ${colId}`}
          >
            <X className="h-3 w-3" />
          </button>
        )}
      </div>
    </th>
  );
}

/**
 * Per-column filter trigger. Renders a small filter icon in the header that
 * opens a type-aware dropdown (text/range/date/multi-select).
 * Highlighted when the column has an active filter value.
 */
function ColumnFilterTrigger({ columnId, type, value, enumValues, onChange }) {
  const [open, setOpen] = useState(false);
  const hasFilter = isFilterActive(value);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          onClick={(e) => e.stopPropagation()}
          onPointerDown={(e) => e.stopPropagation()}
          title={`Filtruj ${columnId}`}
          aria-label={`Filtruj ${columnId}`}
          className={cn(
            "shrink-0 h-5 w-5 -mr-1 inline-flex items-center justify-center rounded transition-opacity",
            "opacity-0 group-hover:opacity-100",
            hasFilter && "opacity-100",
            hasFilter
              ? "text-primary bg-primary/10"
              : "text-muted-foreground/50 hover:text-foreground hover:bg-muted"
          )}
        >
          <FilterIcon className="h-3 w-3" />
        </button>
      </PopoverTrigger>
      <PopoverContent
        align="end"
        sideOffset={4}
        className="p-2 w-auto min-w-[220px]"
        onClick={(e) => e.stopPropagation()}
        onPointerDown={(e) => e.stopPropagation()}
      >
        <div className="text-[10px] text-muted-foreground uppercase tracking-wider font-mono mb-1.5 px-1">
          Filtruj: {columnId}
        </div>
        <FilterInput
          type={type}
          value={value}
          onChange={onChange}
          enumValues={enumValues}
          placeholder={`Filtruj ${columnId}…`}
        />
      </PopoverContent>
    </Popover>
  );
}

function isFilterActive(value) {
  if (value == null || value === "") return false;
  if (Array.isArray(value)) return value.length > 0;
  if (typeof value === "object") return Object.keys(value).length > 0;
  return true;
}
