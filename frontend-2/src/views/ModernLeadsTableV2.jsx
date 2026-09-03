import React, { useState, useMemo, useRef, useEffect } from "react";
import {
  Copy,
  Mail,
  Phone,
  Globe,
  ChevronDown,
  Check,
  Search,
  ChevronRight,
  MapPin,
  Building2,
  ShieldCheck,
  TrendingUp,
  Download,
  X,
  Sparkles,
  Eye,
  EyeOff,
  LayoutGrid,
  ExternalLink,
  CheckCircle2,
  CircleDot,
  CircleDashed,
  Gauge,
  Timer,
  Flame,
} from "lucide-react";
import { toast } from "sonner";
import { UrlBadge, parseWwwStatus } from "../components/UrlBadge";
import { useUrlStatus } from "../hooks/useUrlStatus";
import { useKeywordScan } from "../hooks/useKeywordScan";

// data_weryfikacji can be a Date object (when useCsv applies schema) or
// a plain string. Render either safely.
const fmtDate = (v) => {
  if (v == null || v === "") return "—";
  if (v instanceof Date) return isNaN(v.getTime()) ? "—" : v.toISOString().slice(0, 10);
  return String(v);
};

// --- Helpers ---
function classifyBrand(marki) {
  const s = (marki || "").toLowerCase();
  const hasPM = /powermatic/.test(s);
  const hasHawk = /hawk/.test(s);
  if (hasPM && hasHawk) return "PowerMatic + Hawk";
  if (hasPM) return "PowerMatic";
  if (hasHawk) return "Hawk";
  return "Inna";
}

function splitBrands(s) {
  if (!s) return [];
  return s.split(/[,;|]/).map((b) => b.trim()).filter(Boolean);
}

function maskName(text) {
  if (!text) return "-";
  const parts = text.trim().split(/\s+/);
  if (parts.length >= 2) {
    const surname = parts[parts.length - 1];
    const maskedSurname = surname.substring(0, 2) + "***" + surname.substring(surname.length - 1);
    return `${parts[0]} ${maskedSurname}`;
  }
  const visible = text.substring(0, 3);
  const masked = "*".repeat(Math.max(0, text.length - 3));
  return `${visible}${masked}`;
}

function getVolumePct(wolumen) {
  const v = (wolumen || "").toLowerCase();
  if (v.startsWith("duż") || v === "wysoki" || v === "high") return 90;
  if (v.startsWith("śred") || v === "medium") return 60;
  return 30;
}

function confidenceToNumber(c) {
  if (typeof c === "number") return c;
  const s = String(c || "").replace("%", "").trim();
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
}

function formatCleanNotes(notatki, _lead) {
  if (!notatki || typeof notatki !== "string") return null;
  let text = notatki.trim();
  if (!text || text.toLowerCase() === "brak") return null;

  // Split pipeline artifacts separated by "|"
  const parts = text.split(/\s*\|\s*/);
  const badges = [];
  const cleanParts = [];

  for (const part of parts) {
    const p = part.trim();
    if (!p) continue;
    
    // Extract phone cleanup notices
    if (p.toLowerCase().startsWith("tel cleanup") || p.toLowerCase().startsWith("telefony dodatkowe")) {
      badges.push({ type: "phone", text: p });
      continue;
    }
    // Extract volume detail
    if (p.toLowerCase().startsWith("wolumen detail:")) {
      badges.push({ type: "volume", text: p.replace(/^wolumen detail:\s*/i, "") });
      continue;
    }
    // Extract cf detail
    if (p.toLowerCase().startsWith("cf detail:")) {
      badges.push({ type: "detail", text: p.replace(/^cf detail:\s*/i, "") });
      continue;
    }
    // Extract do weryfikacji / warnings
    if (p.includes("DO-WERYFIKACJI") || p.includes("Weryfikacja:") || p.includes("⚠️")) {
      badges.push({ type: "warning", text: p });
      continue;
    }
    cleanParts.push(p);
  }

  const mainText = cleanParts.join(" • ");

  return {
    mainText: mainText || text,
    badges,
  };
}

// --- Social Icons ---
const LinkedinIcon = ({ size = 16, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
    <rect x="2" y="9" width="4" height="12" />
    <circle cx="4" cy="4" r="2" />
  </svg>
);
const FacebookIcon = ({ size = 16, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" />
  </svg>
);
const InstagramIcon = ({ size = 16, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
    <line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
  </svg>
);
const TikTokIcon = ({ size = 16, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M9 12a4 4 0 1 0 4 4V4a5 5 0 0 0 5 5" />
  </svg>
);

// --- Brand style (color-coded chips) ---
const BRAND_STYLES = {
  "PowerMatic":
    "bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800",
  "Hawk":
    "bg-rose-50 dark:bg-rose-950/50 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-800",
  "PowerMatic + Hawk":
    "bg-gradient-to-r from-indigo-50 to-rose-50 dark:from-indigo-950/40 dark:to-rose-950/40 text-slate-700 dark:text-slate-200 border-indigo-200 dark:border-indigo-800",
  "Inna":
    "bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700",
};

const STATUS_STYLES = {
  // Tier
  Producent: "bg-purple-50 dark:bg-purple-950/50 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-800",
  hurtownik: "bg-blue-50 dark:bg-blue-950/50 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800",
  autoryzowany: "bg-blue-50 dark:bg-blue-950/50 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800",
  reseller: "bg-blue-50 dark:bg-blue-950/50 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800",
  detalista: "bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700",
  marketplace: "bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800",
  // Cross-sell potential
  High: "bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800",
  Medium: "bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800",
  Low: "bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 border-gray-200 dark:border-gray-700",
  // Powinowactwo
  wysoki: "bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800",
  średni: "bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700",
  niski: "bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 border-gray-200 dark:border-gray-700",
};
const DEFAULT_BADGE = "bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-700";

// --- Mock Data Generator (kept compatible with sampleLeads shape) ---
const generateLeads = (count) =>
  Array.from({ length: count }, (_, i) => {
    const tierPool = ["Producent", "hurtownik", "hurtownik", "reseller", "detalista", "marketplace"];
    const tier = tierPool[i % tierPool.length];
    const brandPool = [
      "PowerMatic III+",
      "PowerMatic V+",
      "PowerMatic, Hawk",
      "PowerMatic II+, Hawk Electric",
      "Hawk Roller",
      "Hawk Industrial",
      "BongGo",
      "TopMatic",
    ];
    const marki = brandPool[i % brandPool.length];
    return {
      id: `LEAD-${1000 + i}`,
      nazwa:
        i === 0
          ? "PowerMatic Polska Distribution Sp. z o.o."
          : i === 1
          ? "Hawk Rollers Europe B2B"
          : `Firma Handlowa ${i + 1} Sp. z o.o.`,
      kraj: i % 3 === 0 ? "Polska" : i % 3 === 1 ? "Czechy" : "Słowacja",
      miasto: i % 2 === 0 ? "Warszawa" : "Praga",
      adres: `ul. Przemysłowa ${i + 12}, 00-001 ${i % 2 === 0 ? "Warszawa" : "Praga"}`,
      www: "https://example.com",
      wolumen: ["Duży", "Średni", "Mały", "Duży"][i % 4],
      confidence_wolumen: 70 + (i % 28),
      rejestr_id: `KRS 0000${100000 + i}`,
      nip_vat: `PL${1000000000 + i}`,
      rok_zalozenia: 2010 + (i % 12),
      tier,
      marki_nabijarki: marki,
      marka_wlasna_oem: i % 2 === 0,
      powinowactwo_nabijarki: ["wysoki", "średni", "niski"][i % 3],
      cross_sell_potential: ["High", "Medium", "Low", "High"][i % 4],
      kategoria: "A1",
      rynek_skala: "Lokalny / UE",
      kanal_sprzedaży: "Stacjonarny + Online",
      decydent: ["Jan Kowalski", "Tomasz Nowak", "Anna Wiśniewska", "Piotr Zieliński"][i % 4],
      stanowisko: ["Prezes Zarządu", "Dyrektor Handlowy", "Head of Procurement"][i % 3],
      email_decydent: `kontakt${i}@firma${i}.pl`,
      email: `biuro@firma${i}.pl`,
      telefon: `+48 500 000 ${10 + i}`,
      notatki:
        "Klient zainteresowany maszynami automatycznymi. Preferowane portfolio: PowerMatic oraz akcesoria premium.",
      linkedin: "https://linkedin.com",
      facebook: "https://facebook.com",
      instagram: "https://instagram.com",
      tiktok: "https://tiktok.com",
      data_weryfikacji: "2026-08-28",
      sourcing: "Weryfikacja KRS / B2B Research",
      zrodlo_danych: "KRS Online / GUS",
      flagi: ["Verified"],
    };
  });

export function ModernLeadsTableV2({ leads: leadsProp }) {
  const leads = useMemo(
    // Fallback to demo data only when leadsProp is undefined (not passed).
    // An explicit empty array `[]` means "no data" — render empty state.
    () => (leadsProp === undefined ? generateLeads(50) : leadsProp),
    [leadsProp]
  );

  const [expandedRow, setExpandedRow] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  // Multi-select country: empty array = all countries. Backwards-compat:
  // if `selectedCountry` (string) is set, single-select still works.
  const [selectedCountries, setSelectedCountries] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState("Wszystkie");
  const [selectedTiers, _setSelectedTiers] = useState([]);
  const [selectedTier, setSelectedTier] = useState("Wszystkie");
  const [selectedConfidence, setSelectedConfidence] = useState("all"); // all | green | green_yellow | none
  const [selectedBrands, setSelectedBrands] = useState([]);
  const [selectedUrlFilter, setSelectedUrlFilter] = useState("Wszystkie");
  const [countryDropdownOpen, setCountryDropdownOpen] = useState(false);
  const [tierDropdownOpen, setTierDropdownOpen] = useState(false);
  const [urlDropdownOpen, setUrlDropdownOpen] = useState(false);
  const [confidenceDropdownOpen, setConfidenceDropdownOpen] = useState(false);
  const [maskNames, setMaskNames] = useState(true);

  const filterBarRef = useRef(null);
  const searchInputRef = useRef(null);

  // useUrlStatus/useKeywordScan: pass null/empty so the hook loads all rows
  // once (the per-row filtering happens in JS). This keeps the multi-country
  // filter cheap.
  const urlCountryArg = selectedCountries.length > 0
    ? null  // load all; row filter handles per-country
    : (selectedCountry && selectedCountry !== "Wszystkie" ? selectedCountry : null);
  const { byId: urlStatusById } = useUrlStatus(urlCountryArg);
  const { byId: keywordById } = useKeywordScan(urlCountryArg);

  // ⌘K / Ctrl+K to focus the search input
  useEffect(() => {
    const onKey = (e) => {
      const isK = e.key === "k" || e.key === "K";
      const meta = e.metaKey || e.ctrlKey;
      if (isK && meta) {
        e.preventDefault();
        searchInputRef.current?.focus();
        searchInputRef.current?.select?.();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // Close dropdowns on click outside or Escape
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (filterBarRef.current && !filterBarRef.current.contains(e.target)) {
        setCountryDropdownOpen(false);
        setTierDropdownOpen(false);
        setUrlDropdownOpen(false);
        setConfidenceDropdownOpen(false);
      }
    };
    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        setCountryDropdownOpen(false);
        setTierDropdownOpen(false);
        setUrlDropdownOpen(false);
        setConfidenceDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  const countryOptions = useMemo(() => {
    const defaultList = ["Polska", "Czechy", "Słowacja", "Słowenia", "Chorwacja", "Bułgaria", "Rumunia", "Mołdawia", "Serbia", "Litwa", "Łotwa", "Estonia", "Francja"];
    const found = new Set(defaultList);
    for (const l of leads) {
      if (l.kraj && String(l.kraj).trim() && String(l.kraj).trim().toLowerCase() !== "wszystkie") {
        found.add(String(l.kraj).trim());
      }
    }
    return Array.from(found);
  }, [leads]);

  const tierOptions = useMemo(() => {
    const defaultTiers = ["Producent", "hurtownik", "reseller", "detalista", "marketplace", "autoryzowany"];
    const found = new Set(defaultTiers);
    for (const l of leads) {
      if (l.tier && String(l.tier).trim() && String(l.tier).trim().toLowerCase() !== "wszystkie") {
        found.add(String(l.tier).trim());
      }
    }
    return ["Wszystkie", ...Array.from(found)];
  }, [leads]);

  // --- Top-level brand bookmark counts ---
  const brandCounts = useMemo(() => {
    const counts = { Wszystko: leads.length, PowerMatic: 0, "PowerMatic + Hawk": 0, Hawk: 0, Inna: 0 };
    for (const l of leads) {
      const b = classifyBrand(l.marki_nabijarki);
      if (b === "PowerMatic" || b === "PowerMatic + Hawk") counts.PowerMatic += 1;
      if (b === "Hawk" || b === "PowerMatic + Hawk") counts.Hawk += 1;
      if (b === "PowerMatic + Hawk") counts["PowerMatic + Hawk"] += 1;
      if (b === "Inna") counts.Inna += 1;
    }
    return counts;
  }, [leads]);

  // --- Filtering ---
  const filteredLeads = useMemo(() => {
    return leads.filter((lead) => {
      // Country filter — multi-select (selectedCountries) takes priority over
      // the legacy single-select (selectedCountry). Empty array = all.
      const leadCountry = (lead.kraj || "").trim().toLowerCase();
      if (selectedCountries.length > 0) {
        const ok = selectedCountries.some((c) => c.trim().toLowerCase() === leadCountry);
        if (!ok) return false;
      } else if (selectedCountry !== "Wszystkie") {
        if (leadCountry !== selectedCountry.trim().toLowerCase()) return false;
      }

      // Tier filter — multi-select (selectedTiers) over legacy (selectedTier).
      const leadTier = (lead.tier || "").trim().toLowerCase();
      if (selectedTiers.length > 0) {
        const ok = selectedTiers.some((t) => t.trim().toLowerCase() === leadTier);
        if (!ok) return false;
      } else if (selectedTier !== "Wszystkie") {
        if (leadTier !== selectedTier.trim().toLowerCase()) return false;
      }

      // Brand filter: handles single brands, combos ("PowerMatic + Hawk"), and multiple selections
      if (selectedBrands.length > 0) {
        const b = classifyBrand(lead.marki_nabijarki);
        const matchesBrand = selectedBrands.some((selected) => {
          if (selected === "PowerMatic") return b === "PowerMatic" || b === "PowerMatic + Hawk";
          if (selected === "Hawk") return b === "Hawk" || b === "PowerMatic + Hawk";
          if (selected === "PowerMatic + Hawk") return b === "PowerMatic + Hawk";
          if (selected === "Inna") return b === "Inna";
          return b === selected;
        });
        if (!matchesBrand) return false;
      }

      // Confidence filter (🟢/🟡/🔴). Matches emoji in confidence_wolumen
      // OR the percentage bucket (90/60/30).
      if (selectedConfidence !== "all") {
        const c = String(lead.confidence_wolumen || "");
        const hasGreen = c.includes("🟢");
        const hasYellow = c.includes("🟡");
        const hasRed = c.includes("🔴");
        if (selectedConfidence === "green" && !hasGreen) return false;
        if (selectedConfidence === "green_yellow" && !(hasGreen || hasYellow)) return false;
        if (selectedConfidence === "none" && (hasGreen || hasYellow || hasRed)) return false;
      }

      // URL scanner state filter (reads from SQLite endpoint or fallback to lead.www_status)
      if (selectedUrlFilter !== "Wszystkie") {
        const u = urlStatusById[lead.id];
        const parsedCsvStatus = (!u || u.state === "unknown") && lead.www_status ? parseWwwStatus(lead.www_status) : null;
        const resolvedState = u?.state && u.state !== "unknown" ? u.state : (parsedCsvStatus?.state || "unknown");
        const resolvedStatus = u?.status && u.status !== "unknown" ? u.status : (parsedCsvStatus?.status || "unknown");

        const rawWww = String(lead.www || "").trim().toLowerCase();
        const hasNoUrl = !rawWww || ["brak", "-", "n/a", "nie dotyczy", "brak www"].includes(rawWww);

        if (selectedUrlFilter === "ok") {
          if (resolvedState !== "ok" && resolvedStatus !== "green") return false;
        } else if (selectedUrlFilter === "error") {
          if (!["4xx", "5xx", "timeout", "ssl", "dns", "error"].includes(resolvedState) && resolvedStatus !== "red") return false;
        } else if (selectedUrlFilter === "timeout") {
          if (resolvedState !== "timeout" && resolvedState !== "dns" && resolvedState !== "ssl") return false;
        } else if (selectedUrlFilter === "red_high_kw") {
          const isRed = ["4xx", "5xx", "timeout", "ssl", "dns", "error"].includes(resolvedState) || resolvedStatus === "red";
          const kwScore = keywordById[lead.id]?.score_pct ?? (lead.keyword_score ? Number(lead.keyword_score) : 0);
          if (!isRed || kwScore < 20) return false;
        } else if (selectedUrlFilter === "none") {
          const isUnknown = resolvedState === "unknown" && resolvedStatus === "unknown";
          if (!hasNoUrl && !isUnknown) return false;
        }
      }

      // Global search: search across multiple relevant fields
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const haystack = [
          lead.nazwa,
          lead.nip_vat,
          lead.miasto,
          lead.id,
          lead.decydent,
          lead.email,
          lead.email_decydent,
          lead.telefon,
          lead.marki_nabijarki,
          lead.kraj,
          lead.adres,
          lead.stanowisko,
          lead.rejestr_id,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();

        if (!haystack.includes(q)) return false;
      }

      return true;
    });
  }, [leads, searchQuery, selectedCountry, selectedCountries, selectedTier, selectedTiers, selectedBrands, selectedConfidence, selectedUrlFilter, urlStatusById, keywordById]);

  // --- Active filter pills ---
  const activeFilters = useMemo(() => {
    const list = [];
    if (selectedCountries.length > 0) {
      list.push({ type: "countries", label: `Kraje (${selectedCountries.length})` });
    } else if (selectedCountry !== "Wszystkie") {
      list.push({ type: "country", label: `Kraj: ${selectedCountry}` });
    }
    if (selectedTier !== "Wszystkie") list.push({ type: "tier", label: `Rola: ${selectedTier}` });
    if (selectedConfidence !== "all") {
      const confLabel =
        selectedConfidence === "green"
          ? "Confidence: 🟢 Tylko zweryfikowane"
          : selectedConfidence === "green_yellow"
          ? "Confidence: 🟢 + 🟡"
          : "Confidence: Brak znacznika";
      list.push({ type: "confidence", label: confLabel });
    }
    if (selectedUrlFilter !== "Wszystkie") {
      const label =
        selectedUrlFilter === "ok"
          ? "WWW: Działające (200)"
          : selectedUrlFilter === "error"
          ? "WWW: Błędy (4xx/5xx)"
          : selectedUrlFilter === "timeout"
          ? "WWW: Timeouts / DNS"
          : selectedUrlFilter === "red_high_kw"
          ? "WWW: 🎯 Red + High KW"
          : "WWW: Brak/Nieznane";
      list.push({ type: "url", label });
    }
    for (const b of selectedBrands) list.push({ type: "brand", label: `Marka: ${b}`, value: b });
    if (searchQuery.trim()) list.push({ type: "search", label: `Szukaj: "${searchQuery.trim()}"` });
    return list;
  }, [selectedCountry, selectedCountries, selectedTier, selectedConfidence, selectedUrlFilter, selectedBrands, searchQuery]);

  const removeFilter = (f) => {
    if (f.type === "country" || f.type === "countries") {
      setSelectedCountry("Wszystkie");
      setSelectedCountries([]);
    }
    if (f.type === "tier") setSelectedTier("Wszystkie");
    if (f.type === "confidence") setSelectedConfidence("all");
    if (f.type === "url") setSelectedUrlFilter("Wszystkie");
    if (f.type === "brand") setSelectedBrands((prev) => prev.filter((b) => b !== f.value));
    if (f.type === "search") setSearchQuery("");
  };

  const resetAll = () => {
    setSelectedCountry("Wszystkie");
    setSelectedCountries([]);
    setSelectedTier("Wszystkie");
    setSelectedConfidence("all");
    setSelectedUrlFilter("Wszystkie");
    setSelectedBrands([]);
    setSearchQuery("");
  };

  const handleCopy = (text, label = "Skopiowano") => {
    if (navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(text);
      toast.success(`${label}: ${text}`);
    }
  };

  const escapeCsv = (val) => {
    if (val == null) return '""';
    const s = String(val);
    return `"${s.replace(/"/g, '""')}"`;
  };

  const handleExport = () => {
    const header = "ID,Nazwa,Kraj,Miasto,NIP,Tier,Wolumen,Decydent,Email,Telefon,WWW,Status WWW,Kod HTTP,Błąd WWW,Keyword Score\n";
    const rows = filteredLeads
      .map((l) => {
        const u = urlStatusById[l.id];
        const kw = keywordById[l.id];
        return [
          escapeCsv(l.id),
          escapeCsv(l.nazwa),
          escapeCsv(l.kraj),
          escapeCsv(l.miasto),
          escapeCsv(l.nip_vat),
          escapeCsv(l.tier),
          escapeCsv(l.wolumen),
          escapeCsv(l.decydent),
          escapeCsv(l.email),
          escapeCsv(l.telefon),
          escapeCsv(l.www || ""),
          escapeCsv(u?.state || "nieznane"),
          escapeCsv(u?.http_code || ""),
          escapeCsv(u?.error || ""),
          escapeCsv(kw?.score_pct ?? ""),
        ].join(",");
      })
      .join("\n");
    const blob = new Blob(["\ufeff" + header + rows], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `baza_leadow_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success("Pomyślnie wyeksportowano plik CSV");
  };

  // --- Reusable subcomponents ---
  const StatusBadge = ({ status }) => (
    <span
      className={`px-2.5 py-1 rounded-full text-xs font-semibold border inline-flex items-center gap-1 ${
        STATUS_STYLES[status] || DEFAULT_BADGE
      }`}
    >
      {status}
    </span>
  );

  const CopyableId = ({ value, label }) => {
    const [copied, setCopied] = useState(false);
    const onClick = (e) => {
      e.stopPropagation();
      handleCopy(value, label);
      setCopied(true);
      setTimeout(() => setCopied(false), 1200);
    };
    return (
      <button
        onClick={onClick}
        title={`Kopiuj ${label}: ${value}`}
        className="inline-flex items-center gap-1 font-mono text-xs text-slate-500 hover:text-indigo-600 dark:text-slate-400 dark:hover:text-indigo-400 transition-colors"
      >
        <span className="truncate">{value}</span>
        {copied ? <Check size={11} className="text-emerald-500 shrink-0" /> : <Copy size={11} className="shrink-0" />}
      </button>
    );
  };

  const toggleBrand = (brand) => {
    setSelectedBrands((prev) =>
      prev.includes(brand) ? prev.filter((b) => b !== brand) : [...prev, brand]
    );
  };

  return (
    <div className="w-full bg-slate-50 dark:bg-zinc-950/40 p-4 md:p-6 font-sans text-slate-800 dark:text-slate-100 rounded-2xl">
      {/* --- HEADER SECTION --- */}
      <div className="max-w-[1600px] mx-auto mb-6">
        <div className="flex flex-col sm:flex-row justify-between sm:items-end gap-4 mb-6">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50 tracking-tight">
                Baza Leadów B2B
              </h1>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-gradient-to-r from-indigo-500 to-violet-500 text-white shadow-sm">
                <Sparkles size={10} /> v2
              </span>
            </div>
            <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
              Zarządzaj {leads.length} zweryfikowanymi kontaktami i dystrybutorami maszyn
            </p>
          </div>
          <div className="flex gap-2 flex-wrap">
            <button
              onClick={() => setMaskNames((v) => !v)}
              className="px-3 py-2 bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-700 text-slate-700 dark:text-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 dark:hover:bg-zinc-800 shadow-sm transition-all flex items-center gap-2"
              title={maskNames ? "Pokaż pełne nazwiska decydentów" : "Maskuj nazwiska (RODO)"}
            >
              {maskNames ? <Eye size={15} /> : <EyeOff size={15} />}
              {maskNames ? "Maskuj" : "Odkryj"}
            </button>
            <button
              onClick={handleExport}
              className="px-4 py-2 bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-700 text-slate-700 dark:text-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 dark:hover:bg-zinc-800 shadow-sm transition-all flex items-center gap-2"
            >
              <Download size={16} /> Eksportuj
            </button>
            <button
              onClick={() => toast.info("Formularz dodawania leadu zostanie wdrożony w kolejnej wersji.")}
              className="px-4 py-2 bg-slate-900 dark:bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-slate-800 dark:hover:bg-indigo-500 shadow-md shadow-slate-200 dark:shadow-none transition-all flex items-center gap-2"
            >
              <TrendingUp size={16} /> Nowy Lead
            </button>
          </div>
        </div>

        {/* --- TOP-LEVEL BRAND BOOKMARKS (from V3) --- */}
        <div className="bg-white dark:bg-zinc-900 p-1.5 rounded-xl shadow-sm border border-slate-200 dark:border-zinc-800 flex flex-wrap gap-1 items-center mb-3">
          <LayoutGrid size={14} className="text-slate-400 ml-2 shrink-0" />
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 ml-1 mr-2">
            Szybki filtr
          </span>
          {[
            { label: "Wszystko", count: brandCounts.Wszystko, on: selectedBrands.length === 0, action: () => setSelectedBrands([]) },
            { label: "PowerMatic", count: brandCounts.PowerMatic, brand: "PowerMatic" },
            { label: "PowerMatic + Hawk", count: leads.filter((l) => classifyBrand(l.marki_nabijarki) === "PowerMatic + Hawk").length, brand: "PowerMatic + Hawk" },
            { label: "Hawk", count: brandCounts.Hawk, brand: "Hawk" },
          ].map((b) => {
            const isOn = b.on !== undefined ? b.on : selectedBrands.includes(b.brand);
            return (
              <button
                key={b.label}
                onClick={() => (b.action ? b.action() : toggleBrand(b.brand))}
                className={
                  "inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all " +
                  (isOn
                    ? "bg-primary/10 text-primary font-semibold border border-primary/20 shadow-sm"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/60")
                }
              >
                {b.label}
                <span className="ml-0.5 text-[10px] font-mono tabular-nums px-1.5 rounded-full bg-muted text-muted-foreground">
                  {b.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* --- MODERN FILTER BAR --- */}
        <div ref={filterBarRef} className="bg-card p-2.5 rounded-xl shadow-sm border border-border flex flex-wrap gap-2 items-center">
          <div className="relative flex-1 min-w-[280px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Szukaj po nazwie, NIP, decydencie, telefonie lub mieście..."
              className="w-full pl-10 pr-20 py-2 bg-muted/40 border border-input rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus:border-primary/50 focus:ring-1 focus:ring-primary/30 outline-none transition-all"
            />
            {!searchQuery && (
              <kbd
                aria-label="Skrót klawiaturowy: Command lub Control + K"
                className="hidden sm:inline-flex absolute right-3 top-1/2 -translate-y-1/2 items-center gap-1 px-1.5 py-0.5 text-[10px] font-mono font-semibold text-muted-foreground bg-card border border-border rounded shadow-sm pointer-events-none"
              >
                ⌘K
              </kbd>
            )}
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                title="Wyczyść szukanie"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                <X size={15} />
              </button>
            )}
          </div>

          <div className="hidden sm:block h-7 w-px bg-border mx-1"></div>

          {/* Filter Dropdowns */}
          <div className="relative">
            <button
              type="button"
              aria-haspopup="listbox"
              aria-expanded={countryDropdownOpen}
              onClick={() => {
                setCountryDropdownOpen(!countryDropdownOpen);
                setTierDropdownOpen(false);
                setUrlDropdownOpen(false);
                setConfidenceDropdownOpen(false);
              }}
              className="flex items-center gap-2 px-3 py-2 bg-card hover:bg-muted/60 border border-border rounded-lg text-sm font-medium text-foreground transition-colors"
            >
              <Globe size={16} className="text-muted-foreground" />
              <span>Kraj: {selectedCountry}</span>
              {selectedCountries.length > 1 && (
                <span className="ml-1 px-1.5 py-0.5 text-[10px] font-mono bg-primary/10 text-primary rounded">+{selectedCountries.length - 1}</span>
              )}
              <ChevronDown size={14} className="text-muted-foreground" />
            </button>
            <div
              role="listbox"
              aria-label="Wybór kraju (Multi-select: kliknij kilka aby zaznaczyć)"
              hidden={!countryDropdownOpen}
              className="absolute top-full left-0 mt-2 w-64 bg-popover text-popover-foreground border border-border rounded-xl shadow-xl p-1.5 z-50 max-h-64 overflow-y-auto"
            >
                <p className="px-3 py-1 text-[10px] uppercase tracking-wide font-semibold text-slate-400 dark:text-slate-500">Multi-select</p>
                <button
                  type="button"
                  role="option"
                  aria-selected={selectedCountries.length === 0}
                  onClick={() => {
                    setSelectedCountries([]);
                    setSelectedCountry("Wszystkie");
                    setCountryDropdownOpen(false);
                  }}
                  className={`w-full text-left px-3 py-1.5 rounded-lg text-xs font-medium flex items-center justify-between transition-colors ${
                    selectedCountries.length === 0
                      ? "bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300"
                      : "text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-zinc-800"
                  }`}
                >
                  <span>Wszystkie</span>
                  {selectedCountries.length === 0 && <Check size={14} />}
                </button>
                {countryOptions.map((c) => {
                  const isSelected = selectedCountries.includes(c);
                  return (
                    <button
                      key={c}
                      type="button"
                      role="option"
                      aria-selected={isSelected}
                      onClick={() => {
                        setSelectedCountries((prev) =>
                          isSelected ? prev.filter((x) => x !== c) : [...prev, c]
                        );
                        setSelectedCountry(c);
                      }}
                      className={`w-full text-left px-3 py-1.5 rounded-lg text-xs font-medium flex items-center justify-between transition-colors ${
                        isSelected
                          ? "bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300"
                          : "text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-zinc-800"
                      }`}
                    >
                      <span>{c}</span>
                      {isSelected && <Check size={14} />}
                    </button>
                  );
                })}
            </div>
          </div>

          <div className="relative">
            <button
              onClick={() => {
                setTierDropdownOpen(!tierDropdownOpen);
                setCountryDropdownOpen(false);
                setUrlDropdownOpen(false);
              }}
              className="flex items-center gap-2 px-3 py-2 bg-card hover:bg-muted/60 border border-border rounded-lg text-sm font-medium text-foreground transition-colors"
            >
              <Building2 size={16} className="text-muted-foreground" />
              <span>Rola: {selectedTier}</span>
              <ChevronDown size={14} className="text-muted-foreground" />
            </button>
            {tierDropdownOpen && (
              <div className="absolute top-full left-0 mt-2 w-44 bg-popover text-popover-foreground border border-border rounded-xl shadow-xl p-1.5 z-50">
                {tierOptions.map((r) => (
                  <button
                    key={r}
                    onClick={() => {
                      setSelectedTier(r);
                      setTierDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3 py-1.5 rounded-lg text-xs font-medium flex items-center justify-between transition-colors ${
                      selectedTier === r
                        ? "bg-primary/10 text-primary font-semibold"
                        : "text-foreground hover:bg-muted"
                    }`}
                  >
                    <span>{r}</span>
                    {selectedTier === r && <Check size={14} />}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="relative">
            <button
              onClick={() => {
                setUrlDropdownOpen(!urlDropdownOpen);
                setCountryDropdownOpen(false);
                setTierDropdownOpen(false);
              }}
              className="flex items-center gap-2 px-3 py-2 bg-card hover:bg-muted/60 border border-border rounded-lg text-sm font-medium text-foreground transition-colors"
            >
              <ExternalLink size={16} className="text-muted-foreground" />
              <span>
                WWW:{" "}
                {selectedUrlFilter === "ok"
                  ? "200 OK"
                  : selectedUrlFilter === "error"
                  ? "Błędy"
                  : selectedUrlFilter === "timeout"
                  ? "Timeouts"
                  : selectedUrlFilter === "red_high_kw"
                  ? "🎯 Red + High KW"
                  : selectedUrlFilter === "none"
                  ? "Brak/Nieznane"
                  : "Wszystkie"}
              </span>
              <ChevronDown size={14} className="text-muted-foreground" />
            </button>
            {urlDropdownOpen && (
              <div className="absolute top-full left-0 mt-2 w-56 bg-popover text-popover-foreground border border-border rounded-xl shadow-xl p-1.5 z-50">
                {[
                  { id: "Wszystkie", label: "Wszystkie WWW", icon: null },
                  { id: "ok", label: "Działające (200 OK)", icon: CheckCircle2 },
                  { id: "error", label: "Błędy (4xx/5xx/Red)", icon: X },
                  { id: "timeout", label: "Timeouts / DNS / SSL", icon: Timer },
                  { id: "red_high_kw", label: "🎯 Red + High KW (>20%)", icon: Flame },
                  { id: "none", label: "Brak / Nieznane", icon: CircleDashed },
                ].map((opt) => {
                  const Icon = opt.icon;
                  return (
                    <button
                      key={opt.id}
                      onClick={() => {
                        setSelectedUrlFilter(opt.id);
                        setUrlDropdownOpen(false);
                      }}
                      className={`w-full text-left px-3 py-1.5 rounded-lg text-xs font-medium flex items-center justify-between transition-colors ${
                        selectedUrlFilter === opt.id
                          ? "bg-primary/10 text-primary font-semibold"
                          : "text-foreground hover:bg-muted"
                      }`}
                    >
                      <span className="flex items-center gap-1.5">
                        {Icon && <Icon size={13} className={opt.id === "red_high_kw" ? "text-amber-500" : "text-muted-foreground"} />}
                        {opt.label}
                      </span>
                      {selectedUrlFilter === opt.id && <Check size={14} />}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Confidence dropdown (🟢/🟡/🔴) */}
          <div className="relative">
            <button
              type="button"
              aria-haspopup="listbox"
              aria-expanded={confidenceDropdownOpen}
              onClick={() => {
                setConfidenceDropdownOpen(!confidenceDropdownOpen);
                setCountryDropdownOpen(false);
                setTierDropdownOpen(false);
                setUrlDropdownOpen(false);
              }}
              className="flex items-center gap-2 px-3 py-2 bg-card hover:bg-muted/60 border border-border rounded-lg text-sm font-medium text-foreground transition-colors"
            >
              <Gauge size={16} className="text-muted-foreground" />
              <span>
                Confidence:{" "}
                {selectedConfidence === "green"
                  ? "🟢 tylko"
                  : selectedConfidence === "green_yellow"
                  ? "🟢+🟡"
                  : selectedConfidence === "none"
                  ? "brak"
                  : "wszystkie"}
              </span>
              <ChevronDown size={14} className="text-muted-foreground" />
            </button>
            <div
              role="listbox"
              aria-label="Filtr confidence"
              hidden={!confidenceDropdownOpen}
              className="absolute top-full left-0 mt-2 w-56 bg-popover text-popover-foreground border border-border rounded-xl shadow-xl p-1.5 z-50"
            >
                {[
                  { id: "all", label: "Wszystkie", icon: CircleDot },
                  { id: "green", label: "Tylko 🟢 zweryfikowane", icon: CheckCircle2 },
                  { id: "green_yellow", label: "🟢 + 🟡 (bez 🔴)", icon: Gauge },
                  { id: "none", label: "Bez znacznika", icon: CircleDashed },
                ].map((opt) => {
                  const Icon = opt.icon;
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      role="option"
                      aria-selected={selectedConfidence === opt.id}
                      onClick={() => {
                        setSelectedConfidence(opt.id);
                        setConfidenceDropdownOpen(false);
                      }}
                      className={`w-full text-left px-3 py-1.5 rounded-lg text-xs font-medium flex items-center justify-between transition-colors ${
                        selectedConfidence === opt.id
                          ? "bg-primary/10 text-primary font-semibold"
                          : "text-foreground hover:bg-muted"
                      }`}
                    >
                      <span className="flex items-center gap-1.5">
                        <Icon size={13} className="text-muted-foreground" />
                        {opt.label}
                      </span>
                      {selectedConfidence === opt.id && <Check size={14} />}
                    </button>
                  );
                })}
            </div>
          </div>

          <div className="flex-1"></div>

          {/* Active filter chips (V3 faceted-style with X) */}
          <div className="flex items-center gap-2 px-2 flex-wrap">
            <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Aktywne:
            </span>
            {activeFilters.length === 0 && !searchQuery ? (
              <span className="text-xs text-muted-foreground italic">Wszystkie rekordy</span>
            ) : (
              activeFilters.map((f) => (
                <span
                  key={`${f.type}-${f.label}`}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-primary/10 text-primary rounded-md text-xs font-medium border border-primary/20"
                >
                  {f.label}
                  <button
                    onClick={() => removeFilter(f)}
                    className="hover:opacity-75 transition-opacity"
                    title="Usuń filtr"
                  >
                    <X size={12} />
                  </button>
                </span>
              ))
            )}
            {(activeFilters.length > 0 || searchQuery) && (
              <button
                onClick={resetAll}
                className="text-xs text-destructive hover:underline ml-1 font-medium"
              >
                Resetuj
              </button>
            )}
          </div>
        </div>
      </div>

      {/* --- TABLE CONTAINER --- */}
      <div className="max-w-[1600px] mx-auto bg-card rounded-xl border border-border shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-muted/60 border-b border-border text-xs uppercase tracking-wider text-muted-foreground font-semibold sticky top-0 z-20">
                <th className="py-2.5 px-3 w-12 text-center" aria-label="Expand"></th>
                <th className="py-2.5 px-3 min-w-[80px]">ID</th>
                <th className="py-2.5 px-3 min-w-[100px]">Kraj</th>
                <th className="py-2.5 px-3 min-w-[200px] sticky left-0 z-30 bg-card border-r border-border shadow-[1px_0_3px_rgba(0,0,0,0.05)]">
                  Nazwa Firmy
                </th>
                <th className="py-2.5 px-3 min-w-[140px]">Marka</th>
                <th className="py-2.5 px-3 min-w-[140px]">Kategoria</th>
                <th className="py-2.5 px-3 min-w-[160px]">Decydent</th>
                <th className="py-2.5 px-3 min-w-[120px]">Data weryfikacji</th>
                <th className="py-2.5 px-3 min-w-[120px]">Status</th>
                <th className="py-2.5 px-3 min-w-[100px] text-center">Flagi</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {filteredLeads.length === 0 && (
                <tr>
                  <td colSpan={100} className="p-12 text-center">
                    <div className="flex flex-col items-center gap-3 max-w-md mx-auto">
                      <div className="p-3 bg-muted rounded-full">
                        <Search size={28} className="text-muted-foreground" />
                      </div>
                      <h3 className="text-base font-semibold text-foreground">
                        Brak wyników
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        Żaden lead nie pasuje do aktywnych filtrów. Spróbuj wyczyścić wszystkie filtry lub zawęzić szukanie.
                      </p>
                      <button
                        onClick={resetAll}
                        className="px-4 py-2 bg-primary text-primary-foreground text-xs font-semibold rounded-lg hover:bg-primary/90 transition-colors shadow-sm"
                      >
                        Wyczyść wszystkie filtry
                      </button>
                    </div>
                  </td>
                </tr>
              )}

              {filteredLeads.map((lead) => {
                const isExpanded = expandedRow === lead.id;
                const brand = classifyBrand(lead.marki_nabijarki);
                const confNum = confidenceToNumber(lead.confidence_wolumen) ?? getVolumePct(lead.wolumen);
                const initial = (lead.nazwa || "?").trim().charAt(0).toUpperCase();

                return (
                  <React.Fragment key={lead.id}>
                    {/* Main Row */}
                    <tr
                      className={`group hover:bg-muted/40 transition-colors cursor-pointer ${
                        isExpanded ? "bg-muted/30 border-l-4 border-primary" : "border-l-4 border-transparent"
                      }`}
                      onClick={() => setExpandedRow(isExpanded ? null : lead.id)}
                    >
                      <td className="py-2.5 px-3 border-r border-border/60 w-12 text-center">
                        <div
                          className={`w-5 h-5 mx-auto rounded flex items-center justify-center transition-colors ${
                            isExpanded
                              ? "bg-primary/10 text-primary font-bold"
                              : "bg-muted text-muted-foreground group-hover:bg-muted/80"
                          }`}
                        >
                          {isExpanded ? (
                            <ChevronDown size={14} />
                          ) : (
                            <ChevronRight size={14} />
                          )}
                        </div>
                      </td>

                      {/* ID */}
                      <td className="py-2.5 px-3 font-mono text-[11px] text-muted-foreground whitespace-nowrap">
                        <CopyableId value={lead.id} label="ID" />
                      </td>

                      {/* Kraj */}
                      <td className="py-2.5 px-3">
                        <div className="flex items-center gap-1.5 text-xs font-medium text-foreground">
                          <span className="text-base" role="img" aria-label={lead.kraj}>
                            {lead.kraj === "Polska" || lead.kraj === "PL" ? "🇵🇱" : lead.kraj === "Czechy" || lead.kraj === "CZ" ? "🇨🇿" : lead.kraj === "Słowacja" || lead.kraj === "SK" ? "🇸🇰" : lead.kraj === "Wielka Brytania" || lead.kraj === "UK" ? "🇬🇧" : "🌍"}
                          </span>
                          <span className="uppercase text-[10px] tracking-wider text-muted-foreground font-mono">
                            {lead.kraj === "Polska" ? "PL" : lead.kraj === "Czechy" ? "CZ" : lead.kraj === "Słowacja" ? "SK" : lead.kraj === "Wielka Brytania" ? "UK" : lead.kraj}
                          </span>
                        </div>
                      </td>

                      {/* Nazwa Firmy */}
                      <td className="py-2.5 px-3 sticky left-0 z-10 bg-card group-hover:bg-muted/40 border-r border-border transition-colors shadow-[1px_0_3px_rgba(0,0,0,0.02)]">
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded bg-muted flex items-center justify-center text-foreground font-bold text-xs shrink-0 border border-border">
                            {initial}
                          </div>
                          <div className="min-w-0">
                            <div className="font-semibold text-foreground text-xs truncate">
                              {lead.nazwa}
                            </div>
                            {lead.www && (
                              <div className="mt-0.5" onClick={(e) => e.stopPropagation()}>
                                <UrlBadge
                                  url={lead.www}
                                  status={urlStatusById[lead.id]?.status || "unknown"}
                                  state={urlStatusById[lead.id]?.state || "unknown"}
                                  http_code={urlStatusById[lead.id]?.http_code}
                                  error={urlStatusById[lead.id]?.error}
                                  redirect_url={urlStatusById[lead.id]?.redirect_url}
                                  checked_at={urlStatusById[lead.id]?.checked_at}
                                  raw_status={lead.www_status}
                                  keyword_score={keywordById[lead.id]?.score_pct}
                                  keyword_hits={keywordById[lead.id]?.keywords_found}
                                  showUrl={true}
                                  compact={true}
                                />
                              </div>
                            )}
                          </div>
                        </div>
                      </td>

                      {/* Marka */}
                      <td className="py-2.5 px-3 text-xs">
                        <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border ${BRAND_STYLES[brand]}`}>
                          {brand}
                        </span>
                      </td>

                      {/* Kategoria */}
                      <td className="py-2.5 px-3 text-[11px] text-muted-foreground font-medium">
                        {lead.kategoria || "—"}
                      </td>

                      {/* Decydent */}
                      <td className="py-2.5 px-3">
                        <div className="flex items-center gap-2">
                           <div className="w-6 h-6 rounded-full bg-muted flex items-center justify-center text-muted-foreground font-semibold text-xs border border-border shrink-0">
                             {lead.decydent?.charAt(0) || "D"}
                           </div>
                           <div className="flex flex-col min-w-0">
                             <span className="text-xs font-medium text-foreground truncate">
                               {maskNames ? maskName(lead.decydent) : lead.decydent}
                             </span>
                             <span className="text-[10px] text-muted-foreground truncate">
                               {lead.stanowisko || "—"}
                             </span>
                           </div>
                        </div>
                      </td>

                      {/* Data weryfikacji */}
                      <td className="py-2.5 px-3 text-[11px] font-mono text-muted-foreground">
                        {fmtDate(lead.data_weryfikacji)}
                      </td>

                      {/* Status */}
                      <td className="py-2.5 px-3">
                        <div className="flex items-center gap-1.5">
                          <StatusBadge status={lead.status || lead.tier} />
                          {confNum != null && (
                            <span className="text-[10px] text-muted-foreground font-mono" title={`Pewność: ${confNum}%`}>
                              {confNum}%
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Flagi */}
                      <td className="py-2.5 px-3 text-center">
                        <div className="flex justify-center items-center gap-1 text-muted-foreground">
                          {lead.flagi?.includes("Verified") && (
                            <ShieldCheck size={14} className="text-emerald-500" title="Zweryfikowany (Verified)" />
                          )}
                          {lead.flagi?.includes("FROZEN") && (
                            <span className="text-sky-500 font-bold" title="Zamrożony (FROZEN)">❄️</span>
                          )}
                          {(!lead.flagi || (!lead.flagi.includes("Verified") && !lead.flagi.includes("FROZEN"))) && (
                            <span className="text-muted-foreground/40">—</span>
                          )}
                        </div>
                      </td>
                    </tr>

                    {/* --- EXPANDED DETAIL ROW (Progressive Disclosure) --- */}
                    {isExpanded && (
                      <tr className="bg-muted/20 border-b border-border transition-all">
                        <td colSpan="10" className="p-0">
                          <div className="p-5 md:p-6 grid grid-cols-1 lg:grid-cols-3 gap-5 bg-muted/20 border-t border-border">
                            {/* Column 1: Business Identity & Legal Data */}
                            <div className="space-y-3.5">
                              <div className="flex items-center gap-2 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                                <Building2 size={14} className="text-primary" />
                                <span>Rejestr &amp; Adres</span>
                              </div>

                              <div className="bg-card p-4 rounded-xl border border-border shadow-sm space-y-3 text-card-foreground">
                                <div>
                                  <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide">Adres siedziby</div>
                                  <div className="text-sm font-medium text-foreground flex items-start gap-2 mt-0.5">
                                    <MapPin size={15} className="mt-0.5 text-primary shrink-0" />
                                    <span>{lead.adres || `${lead.miasto}, ${lead.kraj}`}</span>
                                  </div>
                                  {lead.adres && (
                                    <button
                                      className="mt-1.5 text-xs text-primary hover:underline flex items-center gap-1 font-medium transition-colors"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleCopy(lead.adres, "Adres");
                                      }}
                                    >
                                      <Copy size={12} /> Kopiuj adres
                                    </button>
                                  )}
                                </div>

                                <div className="grid grid-cols-2 gap-2.5 pt-2 border-t border-border">
                                  <div className="bg-muted/40 p-2.5 rounded-lg border border-border">
                                    <div className="text-[10px] font-medium text-muted-foreground uppercase">NIP / VAT</div>
                                    <div className="text-xs font-mono font-bold text-foreground mt-0.5 truncate">
                                      {lead.nip_vat || "Brak NIP"}
                                    </div>
                                    {lead.nip_vat && (
                                      <button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          handleCopy(lead.nip_vat, "NIP");
                                        }}
                                        className="mt-1 text-[10px] text-indigo-600 dark:text-indigo-400 hover:underline flex items-center gap-1 font-medium"
                                      >
                                        <Copy size={10} /> Kopiuj
                                      </button>
                                    )}
                                  </div>
                                  <div className="bg-muted/40 p-2.5 rounded-lg border border-border">
                                    <div className="text-[10px] font-medium text-muted-foreground uppercase">KRS / Rejestr</div>
                                    <div className="text-xs font-mono font-bold text-foreground mt-0.5 truncate">
                                      {lead.rejestr_id || "Brak KRS"}
                                    </div>
                                  </div>
                                </div>

                                {lead.marki_nabijarki && (
                                  <div className="pt-2 border-t border-border">
                                    <div className="text-[10px] font-medium text-muted-foreground uppercase mb-1.5">Wykryte Marki</div>
                                    <div className="flex flex-wrap gap-1.5">
                                      {splitBrands(lead.marki_nabijarki).map((m, i) => (
                                        <span
                                          key={i}
                                          className="px-2 py-0.5 bg-primary/10 text-primary rounded-md text-xs font-medium border border-primary/20"
                                        >
                                          {m}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Column 2: Decydent, Direct Contacts & Social */}
                            <div className="space-y-3.5">
                              <div className="flex items-center gap-2 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                                <Sparkles size={14} className="text-emerald-500" />
                                <span>Decydent &amp; Kanały Kontaktu</span>
                              </div>

                              <div className="bg-card p-4 rounded-xl border border-border shadow-sm space-y-3 text-card-foreground">
                                <div>
                                  <div className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide">Osoba Decyzyjna</div>
                                  <div className="text-sm font-bold text-foreground mt-0.5 flex items-center gap-2">
                                    <span>{maskNames ? maskName(lead.decydent) : (lead.decydent || "Brak danych decydenta")}</span>
                                    {lead.stanowisko && (
                                      <span className="text-[11px] font-normal px-2 py-0.5 rounded-full bg-muted text-muted-foreground border border-border">
                                        {lead.stanowisko}
                                      </span>
                                    )}
                                  </div>
                                </div>

                                <div className="space-y-1.5 pt-2 border-t border-border">
                                  {lead.telefon && (
                                    <a
                                      href={`tel:${lead.telefon}`}
                                      onClick={(e) => e.stopPropagation()}
                                      className="flex items-center justify-between p-2 rounded-lg bg-muted/40 hover:bg-emerald-500/10 text-xs font-medium text-foreground hover:text-emerald-600 dark:hover:text-emerald-400 border border-border transition-colors group"
                                    >
                                      <div className="flex items-center gap-2">
                                        <Phone size={13} className="text-emerald-500" />
                                        <span className="font-mono">{lead.telefon}</span>
                                      </div>
                                      <span className="text-[10px] text-muted-foreground group-hover:text-emerald-600">Zadzwoń ↗</span>
                                    </a>
                                  )}
                                  {lead.email_decydent && (
                                    <a
                                      href={`mailto:${lead.email_decydent}`}
                                      onClick={(e) => e.stopPropagation()}
                                      className="flex items-center justify-between p-2 rounded-lg bg-muted/40 hover:bg-sky-500/10 text-xs font-medium text-foreground hover:text-sky-600 dark:hover:text-sky-400 border border-border transition-colors group"
                                    >
                                      <div className="flex items-center gap-2 truncate">
                                        <Mail size={13} className="text-sky-500 shrink-0" />
                                        <span className="truncate">{lead.email_decydent}</span>
                                      </div>
                                      <span className="text-[10px] text-muted-foreground group-hover:text-sky-600 shrink-0 ml-1">E-mail Decydenta ↗</span>
                                    </a>
                                  )}
                                  {lead.email && lead.email !== lead.email_decydent && (
                                    <a
                                      href={`mailto:${lead.email}`}
                                      onClick={(e) => e.stopPropagation()}
                                      className="flex items-center justify-between p-2 rounded-lg bg-muted/40 hover:bg-sky-500/10 text-xs font-medium text-foreground hover:text-sky-600 dark:hover:text-sky-400 border border-border transition-colors group"
                                    >
                                      <div className="flex items-center gap-2 truncate">
                                        <Mail size={13} className="text-muted-foreground shrink-0" />
                                        <span className="truncate">{lead.email}</span>
                                      </div>
                                      <span className="text-[10px] text-muted-foreground group-hover:text-sky-600 shrink-0 ml-1">E-mail Ogólny ↗</span>
                                    </a>
                                  )}
                                </div>

                                {(lead.linkedin || lead.facebook || lead.instagram || lead.tiktok) && (
                                  <div className="pt-2 border-t border-slate-100 dark:border-zinc-700/60 flex items-center gap-2">
                                    <span className="text-[10px] font-medium text-slate-400 uppercase mr-1">Social:</span>
                                    {lead.linkedin && (
                                      <a
                                        href={lead.linkedin}
                                        target="_blank"
                                        rel="noreferrer"
                                        onClick={(e) => e.stopPropagation()}
                                        className="p-1.5 bg-[#0077b5] text-white rounded-lg hover:opacity-90 transition-opacity"
                                        title="LinkedIn"
                                      >
                                        <LinkedinIcon size={14} />
                                      </a>
                                    )}
                                    {lead.facebook && (
                                      <a
                                        href={lead.facebook}
                                        target="_blank"
                                        rel="noreferrer"
                                        onClick={(e) => e.stopPropagation()}
                                        className="p-1.5 bg-[#1877F2] text-white rounded-lg hover:opacity-90 transition-opacity"
                                        title="Facebook"
                                      >
                                        <FacebookIcon size={14} />
                                      </a>
                                    )}
                                    {lead.instagram && (
                                      <a
                                        href={lead.instagram}
                                        target="_blank"
                                        rel="noreferrer"
                                        onClick={(e) => e.stopPropagation()}
                                        className="p-1.5 bg-gradient-to-tr from-yellow-500 to-purple-600 text-white rounded-lg hover:opacity-90 transition-opacity"
                                        title="Instagram"
                                      >
                                        <InstagramIcon size={14} />
                                      </a>
                                    )}
                                    {lead.tiktok && (
                                      <a
                                        href={lead.tiktok}
                                        target="_blank"
                                        rel="noreferrer"
                                        onClick={(e) => e.stopPropagation()}
                                        className="p-1.5 bg-black text-white rounded-lg hover:opacity-90 transition-opacity border border-zinc-700"
                                        title="TikTok"
                                      >
                                        <TikTokIcon size={14} />
                                      </a>
                                    )}
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* Column 3: Analytical Notes & Sourcing Metadata */}
                            <div className="space-y-3.5">
                              <div className="flex items-center gap-2 text-xs font-bold text-muted-foreground uppercase tracking-wider">
                                <ShieldCheck size={14} className="text-amber-500" />
                                <span>Notatki Analityczne &amp; Źródło</span>
                              </div>

                              {(() => {
                                const parsedNotes = formatCleanNotes(lead.notatki, lead);
                                return (
                                  <div className="bg-amber-50/70 dark:bg-amber-950/30 p-4 rounded-xl border border-amber-200/80 dark:border-amber-900/60 shadow-sm flex flex-col justify-between h-full gap-3">
                                    <div>
                                      {/* Clean main note text */}
                                      <p className="text-xs text-amber-950 dark:text-amber-100 leading-relaxed font-sans">
                                        {parsedNotes ? parsedNotes.mainText : (lead.notatki || "Brak dodatkowych notatek analitycznych dla tego rekordu.")}
                                      </p>

                                      {/* Badges / Structured alerts */}
                                      {parsedNotes && parsedNotes.badges.length > 0 && (
                                        <div className="mt-3 flex flex-wrap gap-1.5">
                                          {parsedNotes.badges.map((b, i) => (
                                            <span
                                              key={i}
                                              className={`text-[10px] font-semibold px-2 py-0.5 rounded-md border ${
                                                b.type === "warning"
                                                  ? "bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border-rose-200 dark:border-rose-800"
                                                  : b.type === "volume"
                                                  ? "bg-amber-100 dark:bg-amber-900/60 text-amber-800 dark:text-amber-200 border-amber-300 dark:border-amber-700"
                                                  : "bg-white/80 dark:bg-zinc-800/80 text-amber-900 dark:text-amber-200 border-amber-200 dark:border-amber-800"
                                              }`}
                                            >
                                              {b.text}
                                            </span>
                                          ))}
                                        </div>
                                      )}
                                    </div>

                                    <div className="pt-3 border-t border-amber-200/60 dark:border-amber-800/40 flex justify-between items-center text-[11px] text-amber-800 dark:text-amber-400">
                                      <span className="truncate max-w-[55%]">Źródło: {lead.zrodlo_danych || "Rejestry publiczne"}</span>
                                      <span className="shrink-0 font-mono">Weryfikacja: {fmtDate(lead.data_weryfikacji)}</span>
                                    </div>
                                  </div>
                                );
                              })()}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="p-4 border-t border-slate-200 dark:border-zinc-800 bg-slate-50 dark:bg-zinc-800/60 flex justify-between items-center text-xs text-slate-500 dark:text-slate-400">
          <span>
            Pokazano {filteredLeads.length} z {leads.length} wyników
          </span>
          <div className="flex gap-2">
            <button
              className="px-3 py-1.5 bg-white dark:bg-zinc-800 border border-slate-300 dark:border-zinc-700 rounded-md text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-zinc-700 disabled:opacity-50"
              disabled
            >
              Poprzednia
            </button>
            <button
              className="px-3 py-1.5 bg-white dark:bg-zinc-800 border border-slate-300 dark:border-zinc-700 rounded-md text-xs font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-zinc-700"
            >
              Następna
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ModernLeadsTableV2;
