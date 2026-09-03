import { useState, memo } from "react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { formatDate, truncate, formatNumber, cn } from "@/lib/utils";
import { highlightKeywords } from "@/lib/brand";
import { Mail, Phone, ExternalLink, Copy, Maximize2 } from "lucide-react";
import { toast } from "sonner";
import { UrlBadge, WwwStatusPill } from "@/components/UrlBadge";

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
  "duży": "bg-green-500/15 text-green-700 dark:text-green-300 border-green-500/20",
  "średni": "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/20",
  "mały": "bg-zinc-500/15 text-zinc-700 dark:text-zinc-300 border-zinc-500/20",
};

// Confidence (confidence_wolumen) — categorical
const CONFIDENCE_COLORS = {
  "Jest NIP": "bg-green-500/15 text-green-700 dark:text-green-300 border-green-500/20",
  "www bez NIP": "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/20",
  "brak kontaktu": "bg-rose-500/15 text-rose-700 dark:text-rose-300 border-rose-500/20",
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
const LONG_TEXT_COLUMNS = /^(notatki|adres|marka_wlasna_oem|sourcing|kanal_sprzedaży|zrodlo_danych|decydent|stanowisko|email_decydent|kanal_zamiennik|flagi|cross_sell_potential|wolumen|confidence_wolumen|notatki)$/i;

// Separator dla wielu wartości w jednej komórce (marki_nabijarki, flagi,
// kanały, sourcing, related_to, zrodlo_danych). Akceptuje
// "PowerMatic | Hawk", "PowerMatic,Hawk", "PowerMatic; Hawk", itd.
// Trailing whitespace ucinamy; puste wpisy pomijamy.
const MULTI_VALUE_SPLIT_RE = /\s*[|,;\/]\s*/;

// Rozwija skróconą listę modeli jednej marki do pełnych nazw.
// "PowerMatic I, II+, III+, IV, V" → ["PowerMatic I", "PowerMatic II+",
// "PowerMatic III+", "PowerMatic IV", "PowerMatic V"]
// "Hawk HK-1, HK-2, HK-3" → ["Hawk HK-1", "Hawk HK-2", "Hawk HK-3"]
// Dopasowuje marki: PowerMatic / Powermatic (case-insensitive)
// oraz Hawk / Gerui / Shark / Mascotte / OCB / Gizeh / Korona / Cartel /
// Don Pealo. Każda marka ma własny wzorzec; nierozpoznane fragmenty
// zostają jak są (jeden chunk → jeden pill).
const BRAND_MODEL_EXPANDERS = [
  // PowerMatic — warianty modeli: 1+ | 2+ | 3+ | 4 | 5 | V | Mini
  {
    test: /^PowerMatic\b/i,
    tokens: ["Mini", "I", "II+", "II", "III+", "III", "IV", "V", "V+", "1+", "2", "3", "3+", "4"],
  },
  // Hawk — warianty: HK-1, HK-2, HK-3, Mini, Pro
  {
    test: /^Hawk\b/i,
    tokens: ["HK-1", "HK-2", "HK-3", "Mini", "Pro", "X"],
  },
];

/**
 * Dzieli wartość komórki marki_nabijarki na listę pełnych nazw modeli.
 * Obsługuje zarówno separator "|" (inne marki), jak i przecinki w liście
 * modeli jednej marki ("PowerMatic I, II+, III+").
 */
function expandMarkiNabijarki(value) {
  if (!value) return [];
  // 1. Najpierw rozbij po "|", ";" albo "/" — to rozdziela różne marki.
  //    Przecinek zostawiamy na później, bo listy modeli go używają.
  const brandChunks = String(value)
    .split(/\s*[|;\/]\s*/)
    .map((s) => s.trim())
    .filter(Boolean);

  const result = [];
  for (const chunk of brandChunks) {
    // 2. Jeśli chunk zaczyna się od rozpoznanej marki i dalej ma
    //    przecinki → rozbij po przecinkach i rozwiń do pełnych nazw.
    const expander = BRAND_MODEL_EXPANDERS.find((e) => e.test.test(chunk));
    if (expander && chunk.includes(",")) {
      // "PowerMatic I, II+, III+" → ["I", "II+", "III+"] → ["PowerMatic I", ...]
      const rest = chunk.replace(expander.test, "").trim();
      const tokens = rest
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      const brand = chunk.match(expander.test)[0]; // oryginalna nazwa marki
      for (const t of tokens) {
        // Jeśli token sam wygląda jak pełna nazwa (np. "PowerMatic Mini"),
        // nie doklejaj marki drugi raz.
        if (/^[A-Z]/.test(t) && !expander.tokens.includes(t)) {
          result.push(t);
        } else {
          result.push(`${brand} ${t}`);
        }
      }
    } else {
      result.push(chunk);
    }
  }
  return result;
}

/**
 * Sprawdza czy wartość wygląda na listę wielu pozycji (zawiera separator
 * z MULTI_VALUE_SPLIT_RE). Służy do decyzji czy renderować listę pilli
 * czy pojedynczy element.
 */
function looksLikeList(value) {
  if (!value) return false;
  return MULTI_VALUE_SPLIT_RE.test(String(value));
}

/**
 * Renderuje jeden lub więcej elementów jako pilli (Badge). Bez labelu
 * kolumny. Klik kopiuje dany element.
 *
 * - 0 elementów → null
 * - 1 element    → pojedynczy Badge
 * - N elementów  → flex-wrap listy Badge
 */
function PillsList({ items, titlePrefix = "" }) {
  if (!items || items.length === 0) return null;
  if (items.length === 1) {
    const single = items[0];
    return (
      <Badge
        variant="outline"
        title={titlePrefix ? `${titlePrefix}: ${single}` : `${single} — kliknij, żeby skopiować`}
        onClick={(e) => {
          e.stopPropagation();
          copyToClipboard(single);
          toast.success(`Skopiowano: ${single}`, { duration: 1200 });
        }}
        className="font-normal text-xs cursor-pointer hover:bg-accent"
      >
        {single}
      </Badge>
    );
  }
  return (
    <span
      className="inline-flex flex-wrap gap-1 max-w-full"
      onClick={(e) => e.stopPropagation()}
    >
      {items.map((m, i) => (
        <Badge
          key={`${m}-${i}`}
          variant="outline"
          title={titlePrefix ? `${titlePrefix}: ${m}` : `${m} — kliknij, żeby skopiować`}
          onClick={() => {
            copyToClipboard(m);
            toast.success(`Skopiowano: ${m}`, { duration: 1200 });
          }}
          className="font-normal text-xs cursor-pointer hover:bg-accent"
        >
          {m}
        </Badge>
      ))}
    </span>
  );
}

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
      <PopoverTrigger asChild>
        <span
          onClick={(e) => {
            e.stopPropagation();
            setOpen((prev) => !prev);
          }}
          className="cursor-pointer hover:text-primary inline-flex items-center gap-1"
          title={value}
        >
          <HighlightedText text={display} />
          {truncated && (
            <Maximize2 className="inline h-2.5 w-2.5 ml-1 opacity-0 group-hover:opacity-50 shrink-0" />
          )}
        </span>
      </PopoverTrigger>
      {open && (
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
      )}
    </Popover>
  );
}

/**
 * Short cell with native title tooltip (full value) + click copy.
 * Zero Radix Tooltip overhead — instant renders.
 */
function ShortTextCell({ value, display }) {
  const handleClick = (e) => {
    e.stopPropagation();
    copyToClipboard(value);
    toast.success("Skopiowano do schowka", { duration: 1200 });
  };
  return (
    <span
      onClick={handleClick}
      className="cursor-pointer hover:text-primary"
      title={value}
    >
      {display}
    </span>
  );
}

export const CellRenderer = memo(function CellRenderer({
  value,
  type,
  columnId,
  onCopy,
  maskDecydenci = true,
  urlStatus,
  keywordScan,
}) {
  if (value == null || value === "") {
    return <span className="text-muted-foreground/40">—</span>;
  }

  let display = String(value);

  // Transform rok_zalozenia and other incorporation dates: e.g. "1992" -> "1992 (34 lat)"
  if (
    columnId === "rok_zalozenia" ||
    columnId.includes("rejestracji") ||
    columnId.includes("rozpoczecia") ||
    columnId.includes("incorporation") ||
    columnId.includes("start_date")
  ) {
    const year = parseInt(display, 10);
    if (!isNaN(year) && year > 1000) {
      const currentYear = new Date().getFullYear();
      const age = currentYear - year;
      if (age >= 0) {
        display = `${display} (${age} lat)`;
      }
    }
  }

  // Transform decydent: e.g. "Jan Kowalski" -> "Jan Ko***i" when maskDecydenci is active (default true)
  if (columnId === "decydent" && maskDecydenci && display.trim().length > 0) {
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
  // Special handling for www_status column: render mini pill with label with error inside
  if (columnId === "www_status" && display.trim()) {
    return <WwwStatusPill rawStatus={display.trim()} />;
  }

  // Special handling for www column: render live status badge from SQLite or fallback to raw_status
  if (columnId === "www" && display.trim()) {
    const rawUrl = display.trim();
    const href = /^https?:\/\//i.test(rawUrl) ? rawUrl : `https://${rawUrl}`;
    return (
      <UrlBadge
        url={href}
        status={urlStatus?.status || "unknown"}
        state={urlStatus?.state || "unknown"}
        http_code={urlStatus?.http_code}
        error={urlStatus?.error}
        redirect_url={urlStatus?.redirect_url}
        checked_at={urlStatus?.checked_at}
        keyword_score={keywordScan?.score_pct}
        keyword_hits={keywordScan?.keywords_found}
        showUrl={true}
        compact={true}
      />
    );
  }

  // URL — click opens in new tab. No popover needed; full URL is in title.
  const isUrlLike =
    type === "url" ||
    /^https?:\/\//i.test(display) ||
    /^(www\.|linkedin\.com|facebook\.com|instagram\.com|tiktok\.com|[a-z0-9-]+\.(pl|cz|sk|com|de|eu|co\.uk|org|net|io|app))/i.test(display.trim()) ||
    ["www", "linkedin", "facebook", "instagram", "tiktok"].includes(columnId);

  if (isUrlLike && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(display)) {
    const rawUrl = display.trim();
    const href = /^https?:\/\//i.test(rawUrl) ? rawUrl : `https://${rawUrl}`;
    const cleanDisplay = rawUrl.replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, "");
    return (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        onClick={(e) => e.stopPropagation()}
        title={href}
        className="inline-flex items-center gap-1 text-primary hover:underline font-mono text-xs"
      >
        <span className="truncate max-w-[200px]">{cleanDisplay}</span>
        <ExternalLink className="h-3 w-3 shrink-0 opacity-60" />
      </a>
    );
  }

  // Email
  if (type === "email" || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(display)) {
    return (
      <a
        href={`mailto:${display}`}
        onClick={(e) => e.stopPropagation()}
        title={display}
        className="inline-flex items-center gap-1 text-primary hover:underline"
      >
        <Mail className="h-3 w-3 opacity-60" />
        <span className="truncate max-w-[200px]">{display}</span>
      </a>
    );
  }

  // Phone
  if (type === "phone") {
    const digits = display.replace(/[^\d+]/g, "");
    return (
      <a
        href={`tel:${digits}`}
        onClick={(e) => e.stopPropagation()}
        title="Kliknij, żeby zadzwonić"
        className="inline-flex items-center gap-1 tabular-nums hover:text-primary"
      >
        <Phone className="h-3 w-3 opacity-60" />
        {display}
      </a>
    );
  }

  // Date — tooltip with full ISO + relative hint
  if (type === "date" || value instanceof Date) {
    const d = value instanceof Date ? value : new Date(display);
    if (!isNaN(d.getTime())) {
      return (
        <span
          title={d.toISOString().slice(0, 10)}
          className="tabular-nums text-muted-foreground text-xs cursor-default"
        >
          {formatDate(d)}
        </span>
      );
    }
  }

  // Number
  if (type === "number" && typeof value === "number") {
    return (
      <span
        onClick={handleClick}
        title={`Kliknij, żeby skopiować: ${value}`}
        className="cursor-pointer tabular-nums"
      >
        {formatNumber(value)}
      </span>
    );
  }

  // Enum / tier
  if (type === "enum" && TIER_COLORS[display]) {
    return (
      <Badge
        variant="outline"
        title="Kliknij, żeby skopiować"
        onClick={handleClick}
        className={`${TIER_COLORS[display]} font-normal text-xs cursor-pointer`}
      >
        {display}
      </Badge>
    );
  }

  // Confidence (confidence_wolumen) — categorical badge
  if (columnId === "confidence_wolumen" && CONFIDENCE_COLORS[display]) {
    return (
      <Badge
        variant="outline"
        title="Pewność wolumenu — kliknij, żeby skopiować"
        onClick={handleClick}
        className={`${CONFIDENCE_COLORS[display]} font-normal text-xs cursor-pointer`}
      >
        {display}
      </Badge>
    );
  }

  // Affinity (powinowactwo_nabijarki) — categorical badge
  if (AFFINITY_COLORS[display]) {
    return (
      <Badge
        variant="outline"
        title="Powinowactwo do nabijarek — kliknij, żeby skopiować"
        onClick={handleClick}
        className={`${AFFINITY_COLORS[display]} font-normal text-xs cursor-pointer`}
      >
        {display}
      </Badge>
    );
  }

  // Role (tier) — categorical badge
  if (ROLE_COLORS[display]) {
    return (
      <Badge
        variant="outline"
        title="Rola w kanale — kliknij, żeby skopiować"
        onClick={handleClick}
        className={`${ROLE_COLORS[display]} font-normal text-xs cursor-pointer`}
      >
        {display}
      </Badge>
    );
  }

  // Cross-sell potential, rynek_skala, kategoria, kraj, marka_wlasna_oem, flagi, wolumen
  // — all enum with potentially 1-15 unique values. Render as muted outline badge.
  if (type === "enum") {
    return (
      <Badge
        variant="outline"
        title="Kliknij, żeby skopiować"
        className="font-normal text-xs cursor-pointer hover:bg-accent"
        onClick={handleClick}
      >
        {display}
      </Badge>
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

  // Kolumny-asortyment: wiele wartości w jednej komórce rozdzielonych
  // "|", ",", ";", "/" — każda renderowana jako osobny pill (Badge).
  // Pojedyncza wartość → też pill (spójność wizualna). notatki celowo
  // pominięte — to akapity, nie assety.
  const PILLIFY_COLUMNS = new Set([
    "marki_nabijarki",
    "flagi",
    "kanal_sprzedaży",
    "kanal_zamiennik",
    "marka_wlasna_oem",
    "sourcing",
    "related_to",
    "zrodlo_danych",
  ]);
  if (PILLIFY_COLUMNS.has(columnId) && looksLikeList(display)) {
    // marki_nabijarki ma własny splitter — rozwija "PowerMatic I, II+, III+"
    // na osobne pilli per model.
    const items =
      columnId === "marki_nabijarki"
        ? expandMarkiNabijarki(display)
        : display.split(MULTI_VALUE_SPLIT_RE).map((s) => s.trim()).filter(Boolean);
    return <PillsList items={items} />;
  }

  // Long text → popover with full content. Threshold: 30 chars OR a free-text
  // type column (where truncation is common: notatki, adres, marka_wlasna_oem, etc.)
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
