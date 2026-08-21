import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { ArrowUp, ArrowDown, ArrowUpDown, GripVertical, X } from "lucide-react";
import { flexRender } from "@tanstack/react-table";
import { cn } from "@/lib/utils";

/**
 * `column` is a TanStack v8 Column object (from getVisibleLeafColumns()),
 * not a Header. Columns have .id, .columnDef, .getCanSort(), .getIsSorted() directly.
 */
export function SortableHeader({ column, sortIndex, onContextMenu, onClick, focused, onHide }) {
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
  const align = column.columnDef.meta?.align;

  const handleClick = (e) => {
    if (!canSort) return;
    const handler = column.getToggleSortingHandler();
    if (handler) handler(e);
  };

  return (
    <th
      ref={setNodeRef}
      style={{ ...style, width: `${width}px`, minWidth: `${width}px` }}
      className={cn(
        "group relative text-left align-middle font-medium text-muted-foreground select-none",
        "border-r border-border",
        focused && "ring-2 ring-primary/50 ring-inset"
      )}
      onContextMenu={(e) => onContextMenu?.(e, column)}
    >
      <div
        className={cn(
          "flex items-center gap-1 px-3 py-2",
          align === "right" && "justify-end"
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
