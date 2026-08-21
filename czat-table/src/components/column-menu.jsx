import * as React from "react"
import { ArrowUp, ArrowDown, X, EyeOff, MoreHorizontal, RotateCcw } from "lucide-react"
import { cn } from "@/lib/utils"

/**
 * Right-click / long-press menu shown above a column header.
 * Pure presentational: the parent owns the actions.
 */
export function ColumnMenu({
  col,
  x,
  y,
  onClose,
  onSortAsc,
  onSortDesc,
  onAddSortAsc,
  onAddSortDesc,
  onClearSort,
  onHide,
  onResetWidth,
  onReset,
}) {
  // Clamp to viewport
  const [pos, setPos] = React.useState({ x, y })
  React.useEffect(() => {
    const w = 220
    const h = 280
    const px = Math.min(x, window.innerWidth - w - 8)
    const py = Math.min(y, window.innerHeight - h - 8)
    setPos({ x: px, y: py })
  }, [x, y])

  React.useEffect(() => {
    function onKey(e) {
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [onClose])

  return (
    <div className="fixed inset-0 z-50" onClick={onClose}>
      <div
        role="menu"
        style={{ left: pos.x, top: pos.y }}
        className="absolute min-w-[220px] rounded-md border bg-popover p-1 text-sm text-popover-foreground shadow-md"
        onClick={(e) => e.stopPropagation()}
      >
        <Item icon={ArrowUp} onClick={onSortAsc}>Sort ascending</Item>
        <Item icon={ArrowDown} onClick={onSortDesc}>Sort descending</Item>
        <Item icon={ArrowUp} onClick={onAddSortAsc}>Add to sort (asc)</Item>
        <Item icon={ArrowDown} onClick={onAddSortDesc}>Add to sort (desc)</Item>
        <Item icon={X} onClick={onClearSort}>Clear sort on this column</Item>
        <div className="my-1 h-px bg-border" />
        <Item icon={EyeOff} onClick={onHide}>Hide column</Item>
        {onResetWidth && <Item icon={RotateCcw} onClick={onResetWidth}>Reset width to default</Item>}
        <Item icon={MoreHorizontal} onClick={onReset}>Reset column (all settings)</Item>
      </div>
    </div>
  )
}

function Item({ icon: Icon, children, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "flex w-full cursor-default items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground",
      )}
    >
      <Icon className="size-4 text-muted-foreground" />
      <span>{children}</span>
    </button>
  )
}
