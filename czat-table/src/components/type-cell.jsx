import * as React from "react"
import { formatCell, cleanUrl } from "@/lib/format"
import { ExternalLink, Mail, Phone, Link2 } from "lucide-react"
import { cn } from "@/lib/utils"

/**
 * Render a single cell with type-aware behavior.
 * - plain click  → copy to clipboard
 * - cmd/ctrl+click on link cells → open the link
 * - hover on link cells → reveal the link icon
 */
export function TypeCell({ value, type, colId, onCopy, rowIndex, colIndex }) {
  const display = formatCell(value, type)
  const isLink = type === "url" || type === "email" || type === "phone"
  const [copied, setCopied] = React.useState(false)

  function handleClick(e) {
    if (e.metaKey || e.ctrlKey) return // let the link open
    if (!display) return
    e.preventDefault()
    e.stopPropagation()
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(display).catch(() => {})
    }
    setCopied(true)
    onCopy?.({ value: display, colId, rowIndex, colIndex })
    setTimeout(() => setCopied(false), 900)
  }

  if (!display) {
    return <span className="text-muted-foreground/50">—</span>
  }

  if (isLink) {
    const href =
      type === "email" ? `mailto:${display}` : type === "phone" ? `tel:${display}` : display
    return (
      <a
        href={href}
        target={type === "url" ? "_blank" : undefined}
        rel={type === "url" ? "noopener noreferrer" : undefined}
        onClick={handleClick}
        data-copy-target
        className={cn(
          "group/cell inline-flex max-w-full items-center gap-1.5 text-foreground underline decoration-muted-foreground/30 underline-offset-2 transition-colors hover:decoration-primary",
          copied && "text-primary",
        )}
        title={display}
      >
        {type === "email" ? <Mail className="size-3 shrink-0 text-muted-foreground" /> : type === "phone" ? <Phone className="size-3 shrink-0 text-muted-foreground" /> : <Link2 className="size-3 shrink-0 text-muted-foreground" />}
        <span className="truncate">{type === "url" ? cleanUrl(display) : display}</span>
        {type === "url" && <ExternalLink className="size-3 shrink-0 opacity-0 transition-opacity group-hover/cell:opacity-60" />}
      </a>
    )
  }

  return (
    <span
      onClick={handleClick}
      data-copy-target
      className={cn("block max-w-full truncate cursor-default", copied && "text-primary")}
      title={display}
    >
      {display}
    </span>
  )
}
