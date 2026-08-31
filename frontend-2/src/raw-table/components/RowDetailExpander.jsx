import React, { useState } from "react";
import {
  MapPin,
  Building2,
  Copy,
  Check,
  Mail,
  Phone,
  ShieldCheck,
} from "lucide-react";
import { toast } from "sonner";
import { UrlBadge } from "@/components/UrlBadge";
import { cn } from "@/lib/utils";

function maskName(text) {
  if (!text) return "—";
  const parts = text.trim().split(/\s+/);
  if (parts.length >= 2) {
    const surname = parts[parts.length - 1];
    let maskedSurname = surname;
    if (surname.length > 3) {
      maskedSurname = surname.substring(0, 2) + "***" + surname.substring(surname.length - 1);
    } else if (surname.length === 3) {
      maskedSurname = surname.substring(0, 1) + "***" + surname.substring(surname.length - 1);
    }
    parts[parts.length - 1] = maskedSurname;
    return parts.join(" ");
  }
  const visible = text.substring(0, 3);
  const masked = "*".repeat(Math.max(0, text.length - 3));
  return `${visible}${masked}`;
}

function splitBrands(s) {
  if (!s) return [];
  return String(s).split(/[,;|]/).map((b) => b.trim()).filter(Boolean);
}

const LinkedinIcon = ({ size = 15, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
    <rect x="2" y="9" width="4" height="12" />
    <circle cx="4" cy="4" r="2" />
  </svg>
);

const FacebookIcon = ({ size = 15, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" />
  </svg>
);

const InstagramIcon = ({ size = 15, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
    <line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
  </svg>
);

const TikTokIcon = ({ size = 15, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M9 12a4 4 0 1 0 4 4V4a5 5 0 0 0 5 5" />
  </svg>
);

export function RowDetailExpander({
  lead = {},
  maskNames = true,
  urlStatus,
  keywordScan,
  className,
}) {
  const [copiedKey, setCopiedKey] = useState(null);

  const handleCopy = (text, label, key) => {
    if (!text) return;
    if (navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(text);
      setCopiedKey(key);
      toast.success(`Skopiowano ${label}: ${text}`);
      setTimeout(() => setCopiedKey(null), 1200);
    }
  };

  const decydentDisplay = maskNames ? maskName(lead.decydent) : lead.decydent || "—";
  const brandsList = splitBrands(lead.marki_nabijarki);

  return (
    <div
      onClick={(e) => e.stopPropagation()}
      className={cn(
        "p-4 md:p-5 bg-muted/20 border-y border-border/80 text-foreground animate-in fade-in slide-in-from-top-1 duration-150",
        className
      )}
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 lg:gap-6">
        {/* Column 1: Dane Biznesowe */}
        <div className="space-y-3">
          <div className="flex items-center gap-1.5 text-xs font-bold text-muted-foreground uppercase tracking-wider">
            <Building2 size={14} className="text-primary" />
            <span>Dane Biznesowe</span>
          </div>

          {/* Adres */}
          <div className="bg-card p-3 rounded-lg border border-border shadow-xs">
            <div className="text-[11px] text-muted-foreground mb-0.5">Pełny Adres</div>
            <div className="text-xs font-medium flex items-start gap-1.5">
              <MapPin size={14} className="mt-0.5 text-muted-foreground shrink-0" />
              <span>{lead.adres || `${lead.miasto || "—"}, ${lead.kraj || ""}`}</span>
            </div>
            {lead.adres && (
              <button
                type="button"
                onClick={() => handleCopy(lead.adres, "Adres", "adres")}
                className="mt-1.5 text-[11px] text-primary hover:underline inline-flex items-center gap-1 font-medium cursor-pointer"
              >
                {copiedKey === "adres" ? <Check size={11} className="text-emerald-500" /> : <Copy size={11} />}
                <span>Kopiuj adres</span>
              </button>
            )}
          </div>

          {/* NIP & KRS */}
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-card p-2.5 rounded-lg border border-border shadow-xs">
              <div className="text-[10.5px] text-muted-foreground">NIP / VAT</div>
              <div className="text-xs font-mono font-semibold mt-0.5 truncate">
                {lead.nip_vat || "—"}
              </div>
              {lead.nip_vat && (
                <button
                  type="button"
                  onClick={() => handleCopy(lead.nip_vat, "NIP", "nip")}
                  className="mt-1 text-[10.5px] text-primary hover:underline inline-flex items-center gap-0.5 cursor-pointer"
                >
                  {copiedKey === "nip" ? <Check size={10} className="text-emerald-500" /> : <Copy size={10} />}
                  <span>Kopiuj</span>
                </button>
              )}
            </div>

            <div className="bg-card p-2.5 rounded-lg border border-border shadow-xs">
              <div className="text-[10.5px] text-muted-foreground">Rejestr / KRS</div>
              <div className="text-xs font-mono font-semibold mt-0.5 truncate">
                {lead.rejestr_id || "—"}
              </div>
            </div>
          </div>

          {/* Strona WWW & UrlBadge */}
          {lead.www && (
            <div className="bg-card p-2.5 rounded-lg border border-border shadow-xs space-y-1">
              <div className="text-[10.5px] text-muted-foreground">Strona WWW</div>
              <UrlBadge
                url={lead.www}
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
            </div>
          )}

          {/* Marki maszynek */}
          {brandsList.length > 0 && (
            <div className="bg-card p-2.5 rounded-lg border border-border shadow-xs">
              <div className="text-[10.5px] text-muted-foreground mb-1">Marki Maszynek</div>
              <div className="flex flex-wrap gap-1">
                {brandsList.map((m, i) => (
                  <span
                    key={i}
                    className="px-1.5 py-0.5 bg-muted text-foreground rounded text-[10.5px] font-medium border border-border/80"
                  >
                    {m}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Column 2: Kontakt & Social */}
        <div className="space-y-3">
          <div className="flex items-center gap-1.5 text-xs font-bold text-muted-foreground uppercase tracking-wider">
            <Mail size={14} className="text-primary" />
            <span>Kontakt &amp; Social</span>
          </div>

          <div className="bg-card p-3 rounded-lg border border-border shadow-xs space-y-2">
            <div>
              <div className="text-[10.5px] text-muted-foreground">Decydent</div>
              <div className="text-xs font-semibold text-foreground">
                {decydentDisplay}
              </div>
              {lead.stanowisko && (
                <div className="text-[11px] text-muted-foreground mt-0.5">{lead.stanowisko}</div>
              )}
            </div>

            <hr className="border-border/60" />

            <div className="grid grid-cols-1 gap-1.5 text-xs">
              {lead.email_decydent && (
                <a
                  href={`mailto:${lead.email_decydent}`}
                  className="inline-flex items-center gap-1.5 text-muted-foreground hover:text-primary transition-colors truncate"
                  title={`Napisz do decydenta: ${lead.email_decydent}`}
                >
                  <Mail size={12} className="text-primary shrink-0" />
                  <span className="truncate">{lead.email_decydent}</span>
                </a>
              )}
              {lead.email && lead.email !== lead.email_decydent && (
                <a
                  href={`mailto:${lead.email}`}
                  className="inline-flex items-center gap-1.5 text-muted-foreground hover:text-primary transition-colors truncate"
                  title={`Email ogólny: ${lead.email}`}
                >
                  <Mail size={12} className="shrink-0" />
                  <span className="truncate">{lead.email}</span>
                </a>
              )}
              {lead.telefon && (
                <a
                  href={`tel:${lead.telefon}`}
                  className="inline-flex items-center gap-1.5 text-muted-foreground hover:text-primary transition-colors font-mono"
                  title={`Zadzwoń: ${lead.telefon}`}
                >
                  <Phone size={12} className="text-emerald-500 shrink-0" />
                  <span>{lead.telefon}</span>
                </a>
              )}
            </div>
          </div>

          {/* Social Links */}
          <div className="bg-card p-3 rounded-lg border border-border shadow-xs">
            <div className="text-[10.5px] text-muted-foreground mb-1.5">Social Media</div>
            <div className="flex gap-1.5 flex-wrap">
              {lead.linkedin && (
                <a
                  href={lead.linkedin.startsWith("http") ? lead.linkedin : `https://${lead.linkedin}`}
                  target="_blank"
                  rel="noreferrer"
                  className="p-1.5 bg-[#0077b5] text-white rounded hover:opacity-90 transition-opacity"
                  title="LinkedIn"
                >
                  <LinkedinIcon size={14} />
                </a>
              )}
              {lead.facebook && (
                <a
                  href={lead.facebook.startsWith("http") ? lead.facebook : `https://${lead.facebook}`}
                  target="_blank"
                  rel="noreferrer"
                  className="p-1.5 bg-[#1877F2] text-white rounded hover:opacity-90 transition-opacity"
                  title="Facebook"
                >
                  <FacebookIcon size={14} />
                </a>
              )}
              {lead.instagram && (
                <a
                  href={lead.instagram.startsWith("http") ? lead.instagram : `https://${lead.instagram}`}
                  target="_blank"
                  rel="noreferrer"
                  className="p-1.5 bg-gradient-to-tr from-yellow-500 to-purple-600 text-white rounded hover:opacity-90 transition-opacity"
                  title="Instagram"
                >
                  <InstagramIcon size={14} />
                </a>
              )}
              {lead.tiktok && (
                <a
                  href={lead.tiktok.startsWith("http") ? lead.tiktok : `https://${lead.tiktok}`}
                  target="_blank"
                  rel="noreferrer"
                  className="p-1.5 bg-zinc-900 text-white rounded hover:opacity-90 transition-opacity border border-zinc-700"
                  title="TikTok"
                >
                  <TikTokIcon size={14} />
                </a>
              )}
              {!lead.linkedin && !lead.facebook && !lead.instagram && !lead.tiktok && (
                <span className="text-[11px] text-muted-foreground italic">Brak profili social</span>
              )}
            </div>
          </div>
        </div>

        {/* Column 3: Notatki & Źródło (Amber theme) */}
        <div className="space-y-3">
          <div className="flex items-center gap-1.5 text-xs font-bold text-amber-700 dark:text-amber-400 uppercase tracking-wider">
            <ShieldCheck size={14} className="text-amber-600 dark:text-amber-400" />
            <span>Notatki &amp; Źródło</span>
          </div>

          <div className="bg-amber-50/70 dark:bg-amber-950/30 p-3.5 rounded-lg border border-amber-200/80 dark:border-amber-900/50 shadow-xs flex flex-col justify-between h-[calc(100%-24px)] min-h-[140px]">
            <div>
              <div className="text-[10.5px] font-bold text-amber-900 dark:text-amber-300 mb-1 flex items-center gap-1">
                <span>Notatki Operacyjne</span>
              </div>
              <p className="text-xs text-amber-950 dark:text-amber-200 leading-relaxed whitespace-pre-wrap">
                {lead.notatki || "Brak dodatkowych notatek do tego podmiotu."}
              </p>
            </div>

            <div className="mt-3 pt-2 border-t border-amber-200/60 dark:border-amber-800/40 flex justify-between items-center text-[10.5px] text-amber-800 dark:text-amber-400">
              <span>Źródło: {lead.zrodlo_danych || lead.sourcing || "KRS / B2B"}</span>
              <span>Weryfikacja: {lead.data_weryfikacji ? String(lead.data_weryfikacji).slice(0, 10) : "—"}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default RowDetailExpander;
