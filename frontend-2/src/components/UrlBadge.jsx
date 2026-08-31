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
 *   showUrl: bool — czy pokazywać URL tekst obok pill (default true)
 *   compact: bool — krótszy URL (32 znaki) + mniejsza pill
 */
export function UrlBadge({
  url,
  status = "unknown",
  state = "unknown",
  http_code,
  error,
  redirect_url,
  checked_at,
  showUrl = true,
  compact = false,
  keyword_score,        // 0-100, opcjonalny
  keyword_hits,         // [str, ...], opcjonalna lista trafionych słów
}) {
  if (!url) {
    return showUrl ? <span className="text-xs text-gray-400">—</span> : null;
  }

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

  // Tekst w pill: kod HTTP + state label (np. "4xx 404", "5xx 500")
  let pillText;
  if (http_code && state !== "unknown") {
    if (state === "redirect") {
      pillText = `${http_code}`;
    } else if (state === "ok") {
      pillText = compact ? "OK" : "200 OK";
    } else if (state === "4xx") {
      pillText = compact ? `4xx ${http_code}` : `4xx ${http_code}`;
    } else if (state === "5xx") {
      pillText = compact ? `5xx ${http_code}` : `5xx ${http_code}`;
    } else {
      pillText = `${http_code}`;
    }
  } else if (state === "timeout") pillText = "timeout";
  else if (state === "ssl")      pillText = "SSL";
  else if (state === "dns")      pillText = "DNS";
  else                            pillText = "—";

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
