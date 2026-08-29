import { useState, memo } from "react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { formatDate, truncate, formatNumber, cn } from "@/lib/utils";
import { highlightKeywords } from "@/lib/brand";
import { Mail, Phone, ExternalLink, Copy, Maximize2 } from "lucide-react";
import { toast } from "sonner";

const KEYWORD_CLASS = {
  tyton: "bg-amber-200/70 dark:bg-amber-900/60 text-foreground",
  gilza: "bg-emerald-200/70 dark:bg-emerald-900/60 text-foreground",
  bibulki: "bg-blue-200/70 dark:bg-blue-900/60 text-foreground",
};

/**
 * Renders text with keyword segments highlighted via colored spans.
 * Falls back to plain text if no keywords matched.
 */
function HighlightedText({ text, className }) {
  const segments = highlightKeywords(text);
  const hasHighlight = segments.some((s) => s.type);
  if (!hasHighlight) return <span className={className}>{text}</span>;
  return (
    <span className={className}>
      {segments.map((s, i) =>
        s.type ? (
          <mark
            key={i}
            data-keyword={s.type}
            className={cn("px-0.5 rounded", KEYWORD_CLASS[s.type])}
          >
            {s.text}
          </mark>
        ) : (
          <span key={i}>{s.text}</span>
        )
      )}
    </span>
  );
}

const TIER_COLORS = {
  "wyłączność": "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/20",
  "duży 🟢": "bg-green-500/15 text-green-700 dark:text-green-300 border-green-500/20",
  "duży": "bg-green-500/15 text-green-700 dark:text-green-300 border-green-500/20",
  "średni 🟡": "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/20",
  "średni": "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/20",
  "mały": "bg-zinc-500/15 text-zinc-700 dark:text-zinc-300 border-zinc-500/20",
};

// Affinity to rolling-machine (powinowactwo_nabijarki) — categorical
const AFFINITY_COLORS = {
  "wysoki": "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/20",
  "średni": "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/20",
  "niski": "bg-orange-500/15 text-orange-700 dark:text-orange-300 border-orange-500/20",
  "brak": "bg-zinc-500/15 text-zinc-700 dark:text-zinc-300 border-zinc-500/20",
};

// Tier (business role) — categorical
const ROLE_COLORS = {
  "wyłączność": "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border-emerald-500/20",
  "autoryzowany": "bg-blue-500/15 text-blue-700 dark:text-blue-300 border-blue-500/20",
  "hurtownik": "bg-sky-500/15 text-sky-700 dark:text-sky-300 border-sky-500/20",
  "reseller": "bg-cyan-500/15 text-cyan-700 dark:text-cyan-300 border-cyan-500/20",
  "marketplace": "bg-violet-500/15 text-violet-700 dark:text-violet-300 border-violet-500/20",
  "detalista": "bg-teal-500/15 text-teal-700 dark:text-teal-300 border-teal-500/20",
  "producent": "bg-rose-500/15 text-rose-700 dark:text-rose-300 border-rose-500/20",
};

// Free-text columns where truncation/wrapping is common (notatki, adres,
// etc.) — hoisted to module scope so the regex compiles once, not on every
// cell render (this runs thousands of times per table paint).
const LONG_TEXT_COLUMNS = /^(notatki|adres|marki_nabijarki|marka_wlasna_oem|sourcing|kanal_sprzedaży|zrodlo_danych|decydent|stanowisko|email_decydent|kanal_zamiennik|flagi|cross_sell_potential|wolumen|confidence_wolumen|notatki)$/i;

function copyToClipboard(text) {
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(text).catch(() => {});
  }
}

/**
 * Long-text cell with hover tooltip (full value) + click popover (full value + copy).
 * Used for text cells that may be truncated by column width.
 */
function LongTextCell({ value, display, columnId, truncated }) {
  const [open, setOpen] = useState(false);
  const handleCopy = (e) => {
    e?.stopPropagation();
    copyToClipboard(value);
    toast.success("Skopiowano do schowka", { duration: 1200 });
  };
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <Tooltip delayDuration={250}>
        <TooltipTrigger asChild>
          <PopoverTrigger asChild>
            <span
              onClick={(e) => {
                e.stopPropagation();
                setOpen(true);
              }}
              className="cursor-pointer hover:text-primary"
              title={value}
            >
              <HighlightedText text={display} />
              {truncated && (
                <Maximize2 className="inline h-2.5 w-2.5 ml-1 opacity-0 group-hover:opacity-50" />
              )}
            </span>
          </PopoverTrigger>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-md break-words">
          <p className="text-xs">{truncated ? `${value.substring(0, 200)}${value.length > 200 ? "…" : ""}` : value}</p>
        </TooltipContent>
      </Tooltip>
      <PopoverContent
        className="w-[min(560px,calc(100vw-2rem))] p-0"
        align="start"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-3 py-2 border-b flex items-center justify-between">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-mono">
            {columnId}
          </span>
          <span className="text-[10px] text-muted-foreground tabular-nums">
            {value.length} znaków
          </span>
        </div>
        <ScrollArea className="max-h-80 px-3 py-2">
          <div className="text-sm whitespace-pre-wrap break-words leading-relaxed">
            <HighlightedText text={value} />
          </div>
        </ScrollArea>
        <div className="px-3 py-2 border-t flex items-center justify-end gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={handleCopy}
            className="h-7 text-xs"
          >
            <Copy className="h-3 w-3 mr-1" /> Kopiuj
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}

/**
 * Short cell with hover tooltip (full value) + click copy.
 * No popover — full value is already visible.
 */
function ShortTextCell({ value, display }) {
  const handleClick = (e) => {
    e.stopPropagation();
    copyToClipboard(value);
    toast.success("Skopiowano do schowka", { duration: 1200 });
  };
  return (
    <Tooltip delayDuration={300}>
      <TooltipTrigger asChild>
        <span
          onClick={handleClick}
          className="cursor-pointer hover:text-primary"
          title={value}
        >
          {display}
        </span>
      </TooltipTrigger>
      <TooltipContent side="top">
        <p className="text-xs max-w-xs break-words">{value}</p>
      </TooltipContent>
    </Tooltip>
  );
}

export const CellRenderer = memo(function CellRenderer({ value, type, columnId, onCopy }) {
  if (value == null || value === "") {
    return <span className="text-muted-foreground/40">—</span>;
  }

  let display = String(value);

  // Transform rok_zalozenia: e.g. "1992" -> "1992 (34 lat)"
  if (columnId === "rok_zalozenia") {
    const year = parseInt(display, 10);
    if (!isNaN(year) && year > 1000) {
      const currentYear = new Date().getFullYear();
      const age = currentYear - year;
      if (age >= 0) {
        display = `${year} (${age} lat)`;
      }
    }
  }

  // Transform decydent: e.g. "Jan Kowalski" -> "Jan Ko***i"
  if (columnId === "decydent" && display.trim().length > 0) {
    const parts = display.trim().split(/\s+/);
    if (parts.length >= 2) {
      const surname = parts[parts.length - 1];
      if (surname.length > 3) {
        const maskedSurname = surname.substring(0, 2) + "***" + surname.substring(surname.length - 1);
        parts[parts.length - 1] = maskedSurname;
      } else if (surname.length === 3) {
        const maskedSurname = surname.substring(0, 1) + "***" + surname.substring(surname.length - 1);
        parts[parts.length - 1] = maskedSurname;
      }
      display = parts.join(" ");
    }
  }
  const handleClick = (e) => {
    e.stopPropagation();
    copyToClipboard(display);
    toast.success("Skopiowano do schowka", { duration: 1200 });
    onCopy?.(display);
  };

  // URL — click opens in new tab. No popover needed; full URL is in title.
  if (type === "url" || /^https?:\/\//i.test(display)) {
    return (
      <Tooltip delayDuration={250}>
        <TooltipTrigger asChild>
          <a
            href={display}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="inline-flex items-center gap-1 text-primary hover:underline font-mono text-xs"
          >
            <span className="truncate max-w-[200px]">{display.replace(/^https?:\/\//, "").replace(/\/$/, "")}</span>
            <ExternalLink className="h-3 w-3 shrink-0 opacity-60" />
          </a>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-md">
          <p className="text-xs break-all">{display}</p>
        </TooltipContent>
      </Tooltip>
    );
  }

  // Email
  if (type === "email" || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(display)) {
    return (
      <Tooltip delayDuration={250}>
        <TooltipTrigger asChild>
          <a
            href={`mailto:${display}`}
            onClick={(e) => e.stopPropagation()}
            className="inline-flex items-center gap-1 text-primary hover:underline"
          >
            <Mail className="h-3 w-3 opacity-60" />
            <span className="truncate max-w-[200px]">{display}</span>
          </a>
        </TooltipTrigger>
        <TooltipContent side="top">
          <p className="text-xs">{display}</p>
        </TooltipContent>
      </Tooltip>
    );
  }

  // Phone
  if (type === "phone") {
    const digits = display.replace(/[^\d+]/g, "");
    return (
      <Tooltip delayDuration={250}>
        <TooltipTrigger asChild>
          <a
            href={`tel:${digits}`}
            onClick={(e) => e.stopPropagation()}
            className="inline-flex items-center gap-1 tabular-nums hover:text-primary"
          >
            <Phone className="h-3 w-3 opacity-60" />
            {display}
          </a>
        </TooltipTrigger>
        <TooltipContent side="top">
          <p className="text-xs tabular-nums">Kliknij, żeby zadzwonić</p>
        </TooltipContent>
      </Tooltip>
    );
  }

  // Date — tooltip with full ISO + relative hint
  if (type === "date" || value instanceof Date) {
    const d = value instanceof Date ? value : new Date(display);
    if (!isNaN(d.getTime())) {
      return (
        <Tooltip delayDuration={250}>
          <TooltipTrigger asChild>
            <span className="tabular-nums text-muted-foreground text-xs cursor-default">
              {formatDate(d)}
            </span>
          </TooltipTrigger>
          <TooltipContent side="top">
            <p className="text-xs tabular-nums">{d.toISOString().slice(0, 10)}</p>
          </TooltipContent>
        </Tooltip>
      );
    }
  }

  // Number
  if (type === "number" && typeof value === "number") {
    return (
      <Tooltip delayDuration={250}>
        <TooltipTrigger asChild>
          <span onClick={handleClick} className="cursor-pointer tabular-nums">
            {formatNumber(value)}
          </span>
        </TooltipTrigger>
        <TooltipContent side="top">
          <p className="text-xs">Kliknij, żeby skopiować: <span className="font-mono">{value}</span></p>
        </TooltipContent>
      </Tooltip>
    );
  }

  // Enum / tier
  if (type === "enum" && TIER_COLORS[display]) {
    return (
      <Tooltip delayDuration={250}>
        <TooltipTrigger asChild>
          <Badge variant="outline" className={`${TIER_COLORS[display]} font-normal text-xs cursor-default`}>
            {display}
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="top">
          <p className="text-xs">Kliknij, żeby skopiować</p>
        </TooltipContent>
      </Tooltip>
    );
  }

  // Affinity (powinowactwo_nabijarki) — categorical badge
  if (AFFINITY_COLORS[display]) {
    return (
      <Tooltip delayDuration={250}>
        <TooltipTrigger asChild>
          <Badge variant="outline" className={`${AFFINITY_COLORS[display]} font-normal text-xs cursor-default`}>
            {display}
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="top">
          <p className="text-xs">Powinowactwo do nabijarek — kliknij, żeby skopiować</p>
        </TooltipContent>
      </Tooltip>
    );
  }

  // Role (tier) — categorical badge
  if (ROLE_COLORS[display]) {
    return (
      <Tooltip delayDuration={250}>
        <TooltipTrigger asChild>
          <Badge variant="outline" className={`${ROLE_COLORS[display]} font-normal text-xs cursor-default`}>
            {display}
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="top">
          <p className="text-xs">Rola w kanale — kliknij, żeby skopiować</p>
        </TooltipContent>
      </Tooltip>
    );
  }

  // Cross-sell potential, rynek_skala, kategoria, kraj, marka_wlasna_oem, flagi, wolumen
  // — all enum with potentially 1-15 unique values. Render as muted outline badge.
  if (type === "enum") {
    return (
      <Tooltip delayDuration={250}>
        <TooltipTrigger asChild>
          <Badge
            variant="outline"
            className="font-normal text-xs cursor-pointer hover:bg-accent"
            onClick={(e) => { e.stopPropagation(); copyToClipboard(display); toast.success("Skopiowano do schowka", { duration: 1200 }); }}
          >
            {display}
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="top">
          <p className="text-xs">Kliknij, żeby skopiować</p>
        </TooltipContent>
      </Tooltip>
    );
  }

  // ID-ish (NIP, KRS, REGON, IDs like PL-A-001)
  if (/^(nip|rejestr|krs|regon)/i.test(columnId) || /^[A-Z]{2,}-\d+/.test(display)) {
    return (
      <ShortTextCell
        value={display}
        display={truncate(display, 32)}
      />
    );
  }

  // Long text → popover with full content. Threshold: 30 chars OR a free-text
  // type column (where truncation is common: notatki, adres, marki_nabijarki, etc.)
  const isLong = display.length > 30 || LONG_TEXT_COLUMNS.test(columnId);
  if (isLong) {
    return (
      <LongTextCell
        value={display}
        display={truncate(display, 60)}
        columnId={columnId}
        truncated={display.length > 60 || LONG_TEXT_COLUMNS.test(columnId)}
      />
    );
  }

  // Default short text
  return (
    <ShortTextCell value={display} display={display} />
  );
});
