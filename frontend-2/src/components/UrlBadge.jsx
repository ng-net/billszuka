import {
  ExternalLink,
  Check,
  ArrowRight,
  AlertCircle,
  XCircle,
  Timer,
  Lock,
  HelpCircle,
} from "lucide-react";

/**
 * parseWwwStatus — interpretuje string z kolumny www_status w CSV (np. "green|200|12ms", "red|404", "red|timeout").
 */
export function parseWwwStatus(rawStatus) {
  if (!rawStatus || typeof rawStatus !== "string") return null;
  const parts = rawStatus.trim().split("|");
  const color = parts[0]?.toLowerCase();
  if (color === "green") {
    const http_code = parts[1] ? Number(parts[1]) : 200;
    const response_time = parts[2] || null;
    return {
      status: "green",
      state: http_code >= 300 && http_code < 400 ? "redirect" : "ok",
      http_code,
      response_time,
      label: "200 OK",
    };
  }
  if (color === "red") {
    const detail = parts[1] || "";
    if (detail === "timeout") return { status: "red", state: "timeout", error: "Timeout", label: "Timeout" };
    if (detail === "dns") return { status: "red", state: "dns", error: "DNS Error", label: "DNS Error" };
    if (detail === "ssl") return { status: "red", state: "ssl", error: "SSL Error", label: "SSL Error" };
    const code = Number(detail);
    if (!isNaN(code) && code > 0) {
      const errName =
        code === 404 ? "404 Not Found" :
        code === 403 ? "403 Forbidden" :
        code === 402 ? "402 Payment" :
        code === 405 ? "405 Method" :
        code === 429 ? "429 Rate Limit" :
        code === 500 ? "500 Server Error" :
        code === 503 ? "503 Unavailable" :
        code >= 500 ? `${code} Server Error` :
        `${code} Error`;
      return {
        status: "red",
        state: code >= 500 ? "5xx" : code >= 400 ? "4xx" : "error",
        http_code: code,
        error: errName,
        label: errName,
      };
    }
    return { status: "red", state: "error", error: detail || "Błąd połączenia", label: detail || "Błąd" };
  }
  if (color === "unknown" || color === "nieznane") {
    return { status: "unknown", state: "unknown", label: "Nieznany" };
  }
  return null;
}

/**
 * UrlBadge — URL z pigułką statusu (4 stany + unknown).
 *
 * Stany i kolory:
 *   ok       → green  ("200 OK" / "200" / samo "OK" w kompaktowym)
 *   redirect → blue   ("→301" / "→ 301 Moved")
 *   4xx      → orange ("404" / "403" / "404 Not Found")
 *   5xx      → red    ("500" / "503" / "500 Server Error")
 *   timeout  → red    ("timeout")
 *   ssl      → red    ("SSL")
 *   dns      → red    ("DNS")
 *   unknown  → gray   ("—" / "nieznane")
 *
 * Props:
 *   url, status (high-level), state (szczegółowy), http_code, error, redirect_url, checked_at
 *   raw_status: string — opcjonalny string z kolumny www_status w CSV (np. "green|200|12ms")
 *   showUrl: bool — czy pokazywać URL tekst obok pill (default true)
 *   compact: bool — krótszy URL (32 znaki) + mniejsza pill
 */
export function UrlBadge({
  url,
  status: statusProp,
  state: stateProp,
  http_code: httpCodeProp,
  error: errorProp,
  redirect_url,
  checked_at,
  raw_status,
  showUrl = true,
  compact = false,
  keyword_score,        // 0-100, opcjonalny
  keyword_hits,         // [str, ...], opcjonalna lista trafionych słów
}) {
  if (!url) {
    return showUrl ? <span className="text-xs text-gray-400">—</span> : null;
  }

  // Fallback to parsed raw_status if props are missing/unknown
  const parsed = (!stateProp || stateProp === "unknown") && raw_status ? parseWwwStatus(raw_status) : null;
  const state = stateProp && stateProp !== "unknown" ? stateProp : (parsed?.state || "unknown");
  const http_code = httpCodeProp !== undefined ? httpCodeProp : parsed?.http_code;
  const error = errorProp !== undefined ? errorProp : parsed?.error;

  const palette = {
    ok:       { bg: "#dcfce7", text: "#166534", Icon: Check },
    redirect: { bg: "#dbeafe", text: "#1e40af", Icon: ArrowRight },
    "4xx":    { bg: "#fed7aa", text: "#9a3412", Icon: AlertCircle },
    "5xx":    { bg: "#fecaca", text: "#991b1b", Icon: XCircle },
    timeout:  { bg: "#fee2e2", text: "#991b1b", Icon: Timer },
    ssl:      { bg: "#fee2e2", text: "#991b1b", Icon: Lock },
    dns:      { bg: "#fee2e2", text: "#991b1b", Icon: HelpCircle },
    unknown:  { bg: "#f3f4f6", text: "#6b7280", Icon: HelpCircle },
  };
  const c = palette[state] || palette.unknown;
  const Icon = c.Icon;

  // Tekst w pill: kod HTTP + state label (np. "404", "SSL", "Timeout")
  let pillText;
  if (http_code && state !== "unknown") {
    if (state === "redirect") {
      pillText = `${http_code}`;
    } else if (state === "ok") {
      pillText = compact ? "OK" : "200 OK";
    } else if (state === "4xx") {
      pillText = compact ? `${http_code}` : (error || `${http_code} Error`);
    } else if (state === "5xx") {
      pillText = compact ? `${http_code}` : (error || `${http_code} Server Error`);
    } else {
      pillText = `${http_code}`;
    }
  } else if (state === "timeout") pillText = "Timeout";
  else if (state === "ssl")      pillText = compact ? "SSL" : "SSL Error";
  else if (state === "dns")      pillText = compact ? "DNS" : "DNS Error";
  else                            pillText = error || "—";

  const displayUrl = (() => {
    let s = url.replace(/^https?:\/\//, "").replace(/^www\./, "");
    if (compact && s.length > 32) return s.slice(0, 32) + "…";
    return s;
  })();

  // Tooltip z pełnym info
  const tipLines = [
    `URL: ${url}`,
    http_code ? `HTTP: ${http_code}` : null,
    state !== "ok" && state !== "unknown" ? `Stan: ${state}` : null,
    error ? `Błąd: ${error}` : null,
    redirect_url ? `Przekierowanie: ${redirect_url}` : null,
    checked_at ? `Sprawdzono: ${checked_at}` : "Nie sprawdzano",
    keyword_score !== undefined && keyword_score !== null
      ? `\nKeyword score: ${keyword_score}% (${keyword_hits?.length || 0} trafień)`
      : null,
    keyword_hits && keyword_hits.length
      ? `Trafione: ${keyword_hits.slice(0, 8).join(", ")}${keyword_hits.length > 8 ? "…" : ""}`
      : null,
  ].filter(Boolean);
  const tooltip = tipLines.join("\n");

  // Keyword score pill (opcjonalna, druga obok statusowej)
  const showKw = keyword_score !== undefined && keyword_score !== null;
  const kwBg = !showKw ? null
    : keyword_score >= 30 ? "#dbeafe"  // blue-100
    : keyword_score >= 10 ? "#e0e7ff"  // indigo-100
    : "#f1f5f9";                       // slate-100
  const kwText = !showKw ? null
    : keyword_score >= 30 ? "#1e40af"
    : keyword_score >= 10 ? "#3730a3"
    : "#64748b";
  const kwPillStyle = {
    display: "inline-flex",
    alignItems: "center",
    gap: 3,
    padding: compact ? "1px 5px" : "2px 7px",
    borderRadius: 9999,
    backgroundColor: kwBg,
    color: kwText,
    fontSize: compact ? 9 : 10,
    fontWeight: 600,
    lineHeight: 1.2,
    whiteSpace: "nowrap",
  };

  const pillStyle = {
    display: "inline-flex",
    alignItems: "center",
    gap: 3,
    padding: compact ? "1px 5px" : "2px 7px",
    borderRadius: 9999,
    backgroundColor: c.bg,
    color: c.text,
    fontSize: compact ? 9 : 10,
    fontWeight: 600,
    lineHeight: 1.2,
    whiteSpace: "nowrap",
  };
  const iconSize = compact ? 9 : 10;

  return (
    <span
      className="inline-flex items-center gap-1.5 align-middle"
      style={{ maxWidth: "100%" }}
      title={tooltip}
    >
      {/* Pill ze statusem (ikona + label) */}
      <span style={pillStyle}>
        <Icon size={iconSize} strokeWidth={2.5} />
        {pillText}
      </span>

      {/* Pill ze score keywords (opcjonalna) */}
      {showKw && (
        <span style={kwPillStyle} title={`Score keywords: ${keyword_score}% (${keyword_hits?.length || 0} trafień)${keyword_hits?.length ? "\n" + keyword_hits.slice(0, 8).join(", ") : ""}`}>
          🎯 {keyword_score}%
        </span>
      )}

      {/* URL tekst */}
      {showUrl && (
        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="text-xs text-blue-600 hover:underline truncate"
          style={{ maxWidth: compact ? 140 : 180 }}
        >
          {displayUrl}
        </a>
      )}

      {/* Open in new tab icon */}
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        onClick={(e) => e.stopPropagation()}
        className="text-gray-400 hover:text-gray-700 transition-colors"
        title={`Otwórz ${url} w nowej karcie`}
        aria-label="Otwórz w nowej karcie"
      >
        <ExternalLink size={compact ? 10 : 12} />
      </a>
    </span>
  );
}

/**
 * WwwStatusPill — mini pill for displaying www_status with clean label and error inside.
 *
 * Visual tokens:
 *   200 OK           → emerald pill: [✓ 200 OK (234ms)]
 *   404 / 403 / 4xx  → amber pill:   [⚠ 404 Not Found] / [⚠ 403 Forbidden]
 *   500 / 5xx        → rose pill:    [✕ 500 Server Error]
 *   timeout          → rose pill:    [⏱ Timeout]
 *   ssl              → rose pill:    [🔒 SSL Error]
 *   dns              → rose pill:    [? DNS Error]
 *   unknown          → slate pill:   [—]
 */
export function WwwStatusPill({ rawStatus, compact = false, className = "" }) {
  if (!rawStatus || typeof rawStatus !== "string" || !rawStatus.trim()) {
    return <span className="text-xs text-muted-foreground">—</span>;
  }
  const parsed = parseWwwStatus(rawStatus);
  if (!parsed) {
    return <span className="text-xs text-muted-foreground">{rawStatus}</span>;
  }

  const { status, state, http_code, error, response_time, label } = parsed;

  const isOk = status === "green";
  const is4xx = state === "4xx";
  const isTimeout = state === "timeout";
  const isSsl = state === "ssl";
  const isDns = state === "dns";

  let pillClasses = "bg-slate-50 text-slate-700 border-slate-200 dark:bg-zinc-800 dark:text-slate-300 dark:border-zinc-700";
  let Icon = HelpCircle;

  if (isOk) {
    pillClasses = "bg-emerald-50 text-emerald-700 border-emerald-200/80 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800/60";
    Icon = Check;
  } else if (is4xx) {
    pillClasses = "bg-amber-50 text-amber-700 border-amber-200/80 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800/60";
    Icon = AlertCircle;
  } else if (isTimeout) {
    pillClasses = "bg-rose-50 text-rose-700 border-rose-200/80 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800/60";
    Icon = Timer;
  } else if (isSsl) {
    pillClasses = "bg-rose-50 text-rose-700 border-rose-200/80 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800/60";
    Icon = Lock;
  } else if (isDns) {
    pillClasses = "bg-rose-50 text-rose-700 border-rose-200/80 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800/60";
    Icon = HelpCircle;
  } else {
    // 5xx or generic error
    pillClasses = "bg-rose-50 text-rose-700 border-rose-200/80 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800/60";
    Icon = XCircle;
  }

  let displayLabel = label || error || (http_code ? `HTTP ${http_code}` : isOk ? "200 OK" : "Błąd");
  if (compact) {
    if (displayLabel === "404 Not Found") displayLabel = "404";
    else if (displayLabel === "403 Forbidden") displayLabel = "403";
    else if (displayLabel === "500 Server Error") displayLabel = "500";
    else if (displayLabel === "SSL Error") displayLabel = "SSL";
    else if (displayLabel === "DNS Error") displayLabel = "DNS";
    else if (displayLabel === "200 OK") displayLabel = "OK";
  }

  const tooltip = isOk
    ? `Dostępny: 200 OK${response_time ? ` (czas: ${response_time})` : ""} | Raw: ${rawStatus}`
    : `Błąd strony: ${label || error} | Raw: ${rawStatus}`;

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold border shadow-xs transition-colors whitespace-nowrap select-none ${pillClasses} ${className}`}
      title={tooltip}
    >
      <Icon size={10} strokeWidth={2.5} className="shrink-0" />
      <span>{displayLabel}</span>
      {response_time && !compact && (
        <span className="opacity-60 text-[9px] font-normal font-mono border-l border-current/25 pl-1 ml-0.5">
          {response_time}
        </span>
      )}
    </span>
  );
}
