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
} from "lucide-react";
import { toast } from "sonner";
import { UrlBadge } from "../components/UrlBadge";
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
      id_unikalne: `LEAD-${1000 + i}`,
      nazwa_firmy:
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
    () => (leadsProp && leadsProp.length > 0 ? leadsProp : generateLeads(50)),
    [leadsProp]
  );

  const [expandedRow, setExpandedRow] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  // Multi-select country: empty array = all countries. Backwards-compat:
  // if `selectedCountry` (string) is set, single-select still works.
  const [selectedCountries, setSelectedCountries] = useState([]);
  const [selectedCountry, setSelectedCountry] = useState("Wszystkie");
  const [selectedTiers, setSelectedTiers] = useState([]);
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
      if (l.kraj && String(l.kraj).trim()) found.add(String(l.kraj).trim());
    }
    return ["Wszystkie", ...Array.from(found)];
  }, [leads]);

  const tierOptions = useMemo(() => {
    const defaultTiers = ["Producent", "hurtownik", "reseller", "detalista", "marketplace", "autoryzowany"];
    const found = new Set(defaultTiers);
    for (const l of leads) {
      if (l.tier && String(l.tier).trim()) found.add(String(l.tier).trim());
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

      // URL scanner state filter
      if (selectedUrlFilter === "ok") {
        const u = urlStatusById[lead.id_unikalne];
        if (u?.state !== "ok") return false;
      } else if (selectedUrlFilter === "error") {
        const u = urlStatusById[lead.id_unikalne];
        if (!u || !["4xx", "5xx", "timeout", "ssl", "dns", "error"].includes(u.state)) return false;
      } else if (selectedUrlFilter === "none") {
        const u = urlStatusById[lead.id_unikalne];
        const rawWww = String(lead.www || "").trim().toLowerCase();
        const hasNoUrl = !rawWww || ["brak", "-", "n/a", "nie dotyczy", "brak www"].includes(rawWww);
        const isUnknown = !u || !u.state || u.state === "unknown";
        if (!hasNoUrl && !isUnknown) return false;
      }

      // Global search: search across multiple relevant fields
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const haystack = [
          lead.nazwa_firmy,
          lead.nip_vat,
          lead.miasto,
          lead.id_unikalne,
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
  }, [leads, searchQuery, selectedCountry, selectedCountries, selectedTier, selectedTiers, selectedBrands, selectedConfidence, selectedUrlFilter, urlStatusById]);

  // --- Active filter pills ---
  const activeFilters = useMemo(() => {
    const list = [];
    if (selectedCountry !== "Wszystkie") list.push({ type: "country", label: `Kraj: ${selectedCountry}` });
    if (selectedTier !== "Wszystkie") list.push({ type: "tier", label: `Rola: ${selectedTier}` });
    if (selectedUrlFilter !== "Wszystkie") {
      const label =
        selectedUrlFilter === "ok"
          ? "WWW: Działające (200)"
          : selectedUrlFilter === "error"
          ? "WWW: Błędy"
          : "WWW: Brak/Nieznane";
      list.push({ type: "url", label });
    }
    for (const b of selectedBrands) list.push({ type: "brand", label: `Marka: ${b}`, value: b });
    if (searchQuery.trim()) list.push({ type: "search", label: `Szukaj: "${searchQuery.trim()}"` });
    return list;
  }, [selectedCountry, selectedTier, selectedUrlFilter, selectedBrands, searchQuery]);

  const removeFilter = (f) => {
    if (f.type === "country") setSelectedCountry("Wszystkie");
    if (f.type === "tier") setSelectedTier("Wszystkie");
    if (f.type === "url") setSelectedUrlFilter("Wszystkie");
    if (f.type === "brand") setSelectedBrands((prev) => prev.filter((b) => b !== f.value));
    if (f.type === "search") setSearchQuery("");
  };

  const resetAll = () => {
    setSelectedCountry("Wszystkie");
    setSelectedTier("Wszystkie");
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
        const u = urlStatusById[l.id_unikalne];
        const kw = keywordById[l.id_unikalne];
        return [
          escapeCsv(l.id_unikalne),
          escapeCsv(l.nazwa_firmy),
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

  const IconButton = ({ icon: Icon, onClick, color = "gray", title, stopPropagation = false }) => {
    const colors = {
      gray: "text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800",
      blue: "text-blue-500 hover:text-blue-700 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-950/50",
      green: "text-emerald-500 hover:text-emerald-700 dark:hover:text-emerald-300 hover:bg-emerald-50 dark:hover:bg-emerald-950/50",
    };
    return (
      <button
        onClick={(e) => {
          if (stopPropagation) e.stopPropagation();
          onClick?.(e);
        }}
        title={title}
        className={`p-2 rounded-lg transition-all ${colors[color]}`}
      >
        <Icon size={16} />
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
                    ? "bg-slate-100 dark:bg-zinc-800 text-slate-900 dark:text-slate-100 shadow-inner"
                    : "text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-zinc-800/50")
                }
              >
                {b.label}
                <span className="ml-0.5 text-[10px] font-mono tabular-nums px-1.5 rounded-full bg-slate-200/70 dark:bg-zinc-700 text-slate-500 dark:text-slate-400">
                  {b.count}
                </span>
              </button>
            );
          })}
        </div>

        {/* --- MODERN FILTER BAR --- */}
        <div ref={filterBarRef} className="bg-white dark:bg-zinc-900 p-2.5 rounded-xl shadow-sm border border-slate-200 dark:border-zinc-800 flex flex-wrap gap-2 items-center">
          <div className="relative flex-1 min-w-[280px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Szukaj po nazwie, NIP, decydencie, telefonie lub mieście..."
              className="w-full pl-10 pr-9 py-2 bg-slate-50 dark:bg-zinc-800/80 border-none rounded-lg text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:ring-2 focus:ring-slate-900/10 dark:focus:ring-indigo-500/20 outline-none transition-all"
            />
            {searchQuery && (
              <button
                type="button"
                onClick={() => setSearchQuery("")}
                title="Wyczyść szukanie"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
              >
                <X size={15} />
              </button>
            )}
          </div>

          <div className="hidden sm:block h-7 w-px bg-slate-200 dark:bg-zinc-700 mx-1"></div>

          {/* Filter Dropdowns */}
          <div className="relative">
            <button
              onClick={() => {
                setCountryDropdownOpen(!countryDropdownOpen);
                setTierDropdownOpen(false);
                setUrlDropdownOpen(false);
              }}
              className="flex items-center gap-2 px-3 py-2 bg-slate-50 dark:bg-zinc-800 hover:bg-slate-100 dark:hover:bg-zinc-700/80 border border-slate-200 dark:border-zinc-700 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-200 transition-colors"
            >
              <Globe size={16} className="text-slate-500 dark:text-slate-400" />
              <span>Kraj: {selectedCountry}</span>
              <ChevronDown size={14} className="text-slate-400" />
            </button>
            {countryDropdownOpen && (
              <div className="absolute top-full left-0 mt-2 w-48 bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-700 rounded-xl shadow-xl p-1.5 z-50 max-h-64 overflow-y-auto">
                {countryOptions.map((c) => (
                  <button
                    key={c}
                    onClick={() => {
                      setSelectedCountry(c);
                      setCountryDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3 py-1.5 rounded-lg text-xs font-medium flex items-center justify-between transition-colors ${
                      selectedCountry === c
                        ? "bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300"
                        : "text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-zinc-800"
                    }`}
                  >
                    <span>{c}</span>
                    {selectedCountry === c && <Check size={14} />}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="relative">
            <button
              onClick={() => {
                setTierDropdownOpen(!tierDropdownOpen);
                setCountryDropdownOpen(false);
                setUrlDropdownOpen(false);
              }}
              className="flex items-center gap-2 px-3 py-2 bg-slate-50 dark:bg-zinc-800 hover:bg-slate-100 dark:hover:bg-zinc-700/80 border border-slate-200 dark:border-zinc-700 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-200 transition-colors"
            >
              <Building2 size={16} className="text-slate-500 dark:text-slate-400" />
              <span>Rola: {selectedTier}</span>
              <ChevronDown size={14} className="text-slate-400" />
            </button>
            {tierDropdownOpen && (
              <div className="absolute top-full left-0 mt-2 w-44 bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-700 rounded-xl shadow-xl p-1.5 z-50">
                {tierOptions.map((r) => (
                  <button
                    key={r}
                    onClick={() => {
                      setSelectedTier(r);
                      setTierDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3 py-1.5 rounded-lg text-xs font-medium flex items-center justify-between transition-colors ${
                      selectedTier === r
                        ? "bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300"
                        : "text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-zinc-800"
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
              className="flex items-center gap-2 px-3 py-2 bg-slate-50 dark:bg-zinc-800 hover:bg-slate-100 dark:hover:bg-zinc-700/80 border border-slate-200 dark:border-zinc-700 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-200 transition-colors"
            >
              <ExternalLink size={16} className="text-slate-500 dark:text-slate-400" />
              <span>
                WWW:{" "}
                {selectedUrlFilter === "ok"
                  ? "200 OK"
                  : selectedUrlFilter === "error"
                  ? "Błędy"
                  : selectedUrlFilter === "none"
                  ? "Brak/Nieznane"
                  : "Wszystkie"}
              </span>
              <ChevronDown size={14} className="text-slate-400" />
            </button>
            {urlDropdownOpen && (
              <div className="absolute top-full left-0 mt-2 w-48 bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-700 rounded-xl shadow-xl p-1.5 z-50">
                {[
                  { id: "Wszystkie", label: "Wszystkie WWW" },
                  { id: "ok", label: "🟢 Działające (200 OK)" },
                  { id: "error", label: "🔴 Błędy (4xx/5xx/DNS)" },
                  { id: "none", label: "⚪ Brak / Nieznane" },
                ].map((opt) => (
                  <button
                    key={opt.id}
                    onClick={() => {
                      setSelectedUrlFilter(opt.id);
                      setUrlDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3 py-1.5 rounded-lg text-xs font-medium flex items-center justify-between transition-colors ${
                      selectedUrlFilter === opt.id
                        ? "bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300"
                        : "text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-zinc-800"
                    }`}
                  >
                    <span>{opt.label}</span>
                    {selectedUrlFilter === opt.id && <Check size={14} />}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="flex-1"></div>

          {/* Active filter chips (V3 faceted-style with X) */}
          <div className="flex items-center gap-2 px-2 flex-wrap">
            <span className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
              Aktywne:
            </span>
            {activeFilters.length === 0 && !searchQuery ? (
              <span className="text-xs text-slate-400 italic">Wszystkie rekordy</span>
            ) : (
              activeFilters.map((f) => (
                <span
                  key={`${f.type}-${f.label}`}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 rounded-md text-xs font-medium border border-indigo-100 dark:border-indigo-800"
                >
                  {f.label}
                  <button
                    onClick={() => removeFilter(f)}
                    className="hover:text-indigo-900 dark:hover:text-indigo-100"
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
                className="text-xs text-rose-600 dark:text-rose-400 hover:underline ml-1"
              >
                Resetuj
              </button>
            )}
          </div>
        </div>
      </div>

      {/* --- TABLE CONTAINER --- */}
      <div className="max-w-[1600px] mx-auto bg-white dark:bg-zinc-900 rounded-xl shadow-sm border border-slate-200 dark:border-zinc-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50/90 dark:bg-zinc-800/80 backdrop-blur-md border-b border-slate-200 dark:border-zinc-800 text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400 font-semibold sticky top-0 z-20">
                <th className="p-4 w-12 text-center" aria-label="Expand"></th>
                <th className="p-4 min-w-[280px] sticky left-0 z-30 bg-slate-50 dark:bg-zinc-800 border-r border-slate-200 dark:border-zinc-700 shadow-[1px_0_3px_rgba(0,0,0,0.05)]">
                  Firma &amp; ID
                </th>
                <th className="p-4 min-w-[150px]">Lokalizacja</th>
                <th className="p-4 min-w-[180px]">Wolumen</th>
                <th className="p-4 min-w-[140px]">Potencjał</th>
                <th className="p-4 min-w-[140px]">Rola</th>
                <th className="p-4 min-w-[200px]">Kontakt</th>
                <th className="p-4 min-w-[120px] text-right">Akcje</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-zinc-800/60">
              {filteredLeads.map((lead) => {
                const isExpanded = expandedRow === lead.id_unikalne;
                const brand = classifyBrand(lead.marki_nabijarki);
                const confNum = confidenceToNumber(lead.confidence_wolumen) ?? getVolumePct(lead.wolumen);
                const initial = (lead.nazwa_firmy || "?").trim().charAt(0).toUpperCase();

                return (
                  <React.Fragment key={lead.id_unikalne}>
                    {/* Main Row */}
                    <tr
                      className={`group hover:bg-slate-50 dark:hover:bg-zinc-800/50 transition-colors cursor-pointer ${
                        isExpanded ? "bg-slate-50/80 dark:bg-zinc-800/60" : ""
                      }`}
                      onClick={() => setExpandedRow(isExpanded ? null : lead.id_unikalne)}
                    >
                      <td className="p-4 border-r border-slate-100 dark:border-zinc-800/60 w-12 text-center">
                        <div
                          className={`w-5 h-5 mx-auto rounded-full border flex items-center justify-center transition-colors ${
                            isExpanded
                              ? "bg-slate-900 dark:bg-indigo-600 border-slate-900 dark:border-indigo-600"
                              : "border-slate-300 dark:border-zinc-600 bg-white dark:bg-zinc-800"
                          }`}
                        >
                          {isExpanded ? (
                            <ChevronDown size={12} className="text-white" />
                          ) : (
                            <ChevronRight size={12} className="text-slate-400 dark:text-slate-400" />
                          )}
                        </div>
                      </td>

                      {/* Sticky Left: Identity (sticky ID + Firma from VideoGrid) */}
                      <td className="p-4 sticky left-0 z-10 bg-white dark:bg-zinc-900 group-hover:bg-slate-50 dark:group-hover:bg-zinc-800/80 border-r border-slate-200 dark:border-zinc-700 transition-colors shadow-[1px_0_3px_rgba(0,0,0,0.03)]">
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-100 to-slate-200 dark:from-indigo-900/60 dark:to-zinc-800 flex items-center justify-center text-slate-700 dark:text-indigo-200 font-bold text-lg shadow-inner shrink-0">
                            {initial}
                          </div>
                          <div className="min-w-0">
                            <div className="font-semibold text-slate-900 dark:text-slate-100 text-sm truncate">
                              {lead.nazwa_firmy}
                            </div>
                            <div className="flex items-center gap-2 mt-1 flex-wrap">
                              <CopyableId value={lead.id_unikalne} label="ID" />
                              {lead.flagi?.includes("Verified") && (
                                <span className="flex items-center gap-0.5 text-[10px] text-emerald-600 dark:text-emerald-400 font-medium">
                                  <ShieldCheck size={10} /> Zweryfikowany
                                </span>
                              )}
                              <span
                                className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border ${BRAND_STYLES[brand]}`}
                              >
                                {brand}
                              </span>
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Location */}
                      <td className="p-4 text-sm text-slate-600 dark:text-slate-300">
                        <div className="font-medium text-slate-900 dark:text-slate-100">{lead.miasto}</div>
                        <div className="text-xs text-slate-400 dark:text-slate-400 flex items-center gap-1 mt-0.5">
                          <Globe size={10} /> {lead.kraj}
                        </div>
                      </td>

                      {/* Volume with confidence bar (enhanced) */}
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <div className="flex flex-col w-full">
                            <div className="flex justify-between text-xs mb-1">
                              <span className="font-medium text-slate-700 dark:text-slate-200">{lead.wolumen}</span>
                              <span className="text-slate-400 text-[11px]">{confNum}%</span>
                            </div>
                            <div className="w-full bg-slate-100 dark:bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                              <div
                                className={`h-full rounded-full ${
                                  lead.wolumen?.toLowerCase().startsWith("duż")
                                    ? "bg-emerald-500"
                                    : lead.wolumen?.toLowerCase().startsWith("śred")
                                    ? "bg-amber-400"
                                    : "bg-slate-400 dark:bg-zinc-500"
                                }`}
                                style={{ width: `${confNum}%` }}
                              ></div>
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Potential */}
                      <td className="p-4">
                        <div className="flex flex-col gap-1.5 items-start">
                          <StatusBadge status={lead.cross_sell_potential} />
                          {lead.powinowactwo_nabijarki?.toLowerCase() === "wysoki" && (
                            <span className="text-[10px] text-amber-600 dark:text-amber-400 font-medium flex items-center gap-0.5">
                              �� Wysokie powinowactwo
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Tier */}
                      <td className="p-4">
                        <StatusBadge status={lead.tier} />
                      </td>

                      {/* Contact Preview with masking toggle */}
                      <td className="p-4">
                        <div className="flex items-center gap-2.5">
                          <div className="group/contact relative">
                            <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-zinc-800 flex items-center justify-center text-slate-600 dark:text-slate-300 font-semibold text-xs border border-slate-200 dark:border-zinc-700">
                              {lead.decydent?.charAt(0) || "D"}
                            </div>
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-40 bg-slate-900 text-white text-xs rounded-md py-1 px-2 opacity-0 group-hover/contact:opacity-100 transition-opacity pointer-events-none text-center z-50 shadow-lg">
                              <div className="font-semibold">{maskNames ? maskName(lead.decydent) : lead.decydent}</div>
                              <div className="text-[10px] text-slate-300">{lead.stanowisko}</div>
                              <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-900"></div>
                            </div>
                          </div>
                          <div className="flex flex-col min-w-0">
                            <span className="text-xs font-medium text-slate-700 dark:text-slate-200 truncate">
                              {maskNames ? maskName(lead.decydent) : lead.decydent}
                            </span>
                            <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono truncate">
                              {lead.telefon}
                            </span>
                          </div>
                        </div>
                      </td>

                      {/* Actions */}
                      <td className="p-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <IconButton
                            icon={Mail}
                            color="blue"
                            title={`Napisz: ${lead.email}`}
                            stopPropagation
                            onClick={() => (window.location.href = `mailto:${lead.email}`)}
                          />
                          <IconButton
                            icon={Phone}
                            color="green"
                            title={`Zadzwoń: ${lead.telefon}`}
                            stopPropagation
                            onClick={() => (window.location.href = `tel:${lead.telefon}`)}
                          />
                          {lead.www && (
                            <span onClick={(e) => e.stopPropagation()}>
                              <UrlBadge
                                url={lead.www}
                                status={urlStatusById[lead.id_unikalne]?.status || "unknown"}
                                state={urlStatusById[lead.id_unikalne]?.state || "unknown"}
                                http_code={urlStatusById[lead.id_unikalne]?.http_code}
                                error={urlStatusById[lead.id_unikalne]?.error}
                                redirect_url={urlStatusById[lead.id_unikalne]?.redirect_url}
                                checked_at={urlStatusById[lead.id_unikalne]?.checked_at}
                                keyword_score={keywordById[lead.id_unikalne]?.score_pct}
                                keyword_hits={keywordById[lead.id_unikalne]?.keywords_found}
                                showUrl={false}
                                compact={true}
                              />
                            </span>
                          )}
                          <IconButton
                            icon={Copy}
                            color="gray"
                            title={`Kopiuj NIP: ${lead.nip_vat}`}
                            stopPropagation
                            onClick={() => handleCopy(lead.nip_vat, "NIP")}
                          />
                        </div>
                      </td>
                    </tr>

                    {/* --- EXPANDED DETAIL ROW (Progressive Disclosure) --- */}
                    {isExpanded && (
                      <tr className="bg-slate-50/70 dark:bg-zinc-800/40 border-b border-slate-200 dark:border-zinc-800 transition-all">
                        <td colSpan="8" className="p-0">
                          <div className="p-6 grid grid-cols-1 md:grid-cols-3 gap-6 bg-slate-50/50 dark:bg-zinc-900/50">
                            {/* Column 1: Business Details */}
                            <div className="space-y-4">
                              <h4 className="text-xs font-bold text-slate-400 dark:text-slate-400 uppercase tracking-wider mb-2">
                                Dane Biznesowe
                              </h4>

                              <div className="bg-white dark:bg-zinc-800 p-3.5 rounded-lg border border-slate-200 dark:border-zinc-700 shadow-sm">
                                <div className="text-xs text-slate-500 dark:text-slate-400 mb-1">Pełny Adres</div>
                                <div className="text-sm font-medium text-slate-800 dark:text-slate-100 flex items-start gap-2">
                                  <MapPin size={16} className="mt-0.5 text-slate-400 shrink-0" />
                                  <span>{lead.adres}</span>
                                </div>
                                <button
                                  className="mt-2 text-xs text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1 font-medium"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleCopy(lead.adres, "Adres");
                                  }}
                                >
                                  <Copy size={12} /> Kopiuj adres
                                </button>
                              </div>

                              <div className="grid grid-cols-2 gap-3">
                                <div className="bg-white dark:bg-zinc-800 p-3 rounded-lg border border-slate-200 dark:border-zinc-700 shadow-sm">
                                  <div className="text-xs text-slate-500 dark:text-slate-400">NIP / VAT</div>
                                  <div className="text-sm font-mono font-semibold text-slate-800 dark:text-slate-200 mt-0.5">
                                    {lead.nip_vat}
                                  </div>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleCopy(lead.nip_vat, "NIP");
                                    }}
                                    className="mt-1 text-[11px] text-blue-600 dark:text-blue-400 hover:underline flex items-center gap-1"
                                  >
                                    <Copy size={10} /> Kopiuj
                                  </button>
                                </div>
                                <div className="bg-white dark:bg-zinc-800 p-3 rounded-lg border border-slate-200 dark:border-zinc-700 shadow-sm">
                                  <div className="text-xs text-slate-500 dark:text-slate-400">KRS</div>
                                  <div className="text-sm font-mono font-semibold text-slate-800 dark:text-slate-200 mt-0.5">
                                    {lead.rejestr_id}
                                  </div>
                                </div>

                                {lead.www && (
                                  <div className="bg-white dark:bg-zinc-800 p-3 rounded-lg border border-slate-200 dark:border-zinc-700 shadow-sm">
                                    <div className="text-xs text-slate-500 dark:text-slate-400 mb-1.5">Strona WWW</div>
                                    <UrlBadge
                                      url={lead.www}
                                      status={urlStatusById[lead.id_unikalne]?.status || "unknown"}
                                      state={urlStatusById[lead.id_unikalne]?.state || "unknown"}
                                      http_code={urlStatusById[lead.id_unikalne]?.http_code}
                                      error={urlStatusById[lead.id_unikalne]?.error}
                                      redirect_url={urlStatusById[lead.id_unikalne]?.redirect_url}
                                      checked_at={urlStatusById[lead.id_unikalne]?.checked_at}
                                      keyword_score={keywordById[lead.id_unikalne]?.score_pct}
                                      keyword_hits={keywordById[lead.id_unikalne]?.keywords_found}
                                      showUrl={true}
                                      compact={true}
                                    />
                                  </div>
                                )}
                              </div>

                              <div className="bg-white dark:bg-zinc-800 p-3 rounded-lg border border-slate-200 dark:border-zinc-700 shadow-sm">
                                <div className="text-xs text-slate-500 dark:text-slate-400 mb-1.5">Marki Maszynek</div>
                                <div className="flex flex-wrap gap-1.5">
                                  {splitBrands(lead.marki_nabijarki).map((m, i) => (
                                    <span
                                      key={i}
                                      className="px-2 py-0.5 bg-slate-100 dark:bg-zinc-700 text-slate-700 dark:text-slate-200 rounded text-xs font-medium border border-slate-200 dark:border-zinc-600"
                                    >
                                      {m}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            </div>

                            {/* Column 2: Contact & Socials */}
                            <div className="space-y-4">
                              <h4 className="text-xs font-bold text-slate-400 dark:text-slate-400 uppercase tracking-wider mb-2">
                                Kontakt & Social
                              </h4>

                              <div className="bg-white dark:bg-zinc-800 p-4 rounded-lg border border-slate-200 dark:border-zinc-700 shadow-sm space-y-3">
                                <div>
                                  <div className="text-xs text-slate-500 dark:text-slate-400">Decydent</div>
                                  <div className="text-sm font-semibold text-slate-900 dark:text-slate-100">
                                    {maskNames ? maskName(lead.decydent) : lead.decydent}
                                  </div>
                                  <div className="text-xs text-slate-500 dark:text-slate-400">{lead.stanowisko}</div>
                                </div>
                                <hr className="border-slate-100 dark:border-zinc-700" />
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                  <a
                                    href={`mailto:${lead.email_decydent}`}
                                    onClick={(e) => e.stopPropagation()}
                                    className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                                  >
                                    <Mail size={13} /> Email Decydenta
                                  </a>
                                  <a
                                    href={`mailto:${lead.email}`}
                                    onClick={(e) => e.stopPropagation()}
                                    className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                                  >
                                    <Mail size={13} /> Email Ogólny
                                  </a>
                                </div>
                              </div>

                              <div className="bg-white dark:bg-zinc-800 p-3.5 rounded-lg border border-slate-200 dark:border-zinc-700 shadow-sm">
                                <div className="text-xs text-slate-500 dark:text-slate-400 mb-2">Social Media</div>
                                <div className="flex gap-2">
                                  <a
                                    href={lead.linkedin}
                                    target="_blank"
                                    rel="noreferrer"
                                    onClick={(e) => e.stopPropagation()}
                                    className="p-2 bg-[#0077b5] text-white rounded hover:opacity-90 transition-opacity"
                                    title="LinkedIn"
                                  >
                                    <LinkedinIcon size={16} />
                                  </a>
                                  <a
                                    href={lead.facebook}
                                    target="_blank"
                                    rel="noreferrer"
                                    onClick={(e) => e.stopPropagation()}
                                    className="p-2 bg-[#1877F2] text-white rounded hover:opacity-90 transition-opacity"
                                    title="Facebook"
                                  >
                                    <FacebookIcon size={16} />
                                  </a>
                                  <a
                                    href={lead.instagram}
                                    target="_blank"
                                    rel="noreferrer"
                                    onClick={(e) => e.stopPropagation()}
                                    className="p-2 bg-gradient-to-tr from-yellow-500 to-purple-600 text-white rounded hover:opacity-90 transition-opacity"
                                    title="Instagram"
                                  >
                                    <InstagramIcon size={16} />
                                  </a>
                                  <a
                                    href={lead.tiktok}
                                    target="_blank"
                                    rel="noreferrer"
                                    onClick={(e) => e.stopPropagation()}
                                    className="p-2 bg-black text-white rounded hover:opacity-90 transition-opacity border border-zinc-700"
                                    title="TikTok"
                                  >
                                    <TikTokIcon size={16} />
                                  </a>
                                </div>
                              </div>
                            </div>

                            {/* Column 3: Notes & Meta (amber card) */}
                            <div className="space-y-4">
                              <h4 className="text-xs font-bold text-slate-400 dark:text-slate-400 uppercase tracking-wider mb-2">
                                Notatki & Źródło
                              </h4>

                              <div className="bg-amber-50/80 dark:bg-amber-950/30 p-4 rounded-lg border border-amber-200/80 dark:border-amber-900/50 shadow-sm flex flex-col justify-between h-full">
                                <div>
                                  <div className="text-xs font-bold text-amber-900 dark:text-amber-300 mb-2 flex items-center gap-1.5">
                                    <ShieldCheck size={15} /> Notatki Wewnętrzne
                                  </div>
                                  <p className="text-xs text-amber-950 dark:text-amber-200 leading-relaxed">
                                    {lead.notatki}
                                  </p>
                                </div>
                                <div className="mt-4 pt-3 border-t border-amber-200/60 dark:border-amber-800/40 flex justify-between items-center text-[11px] text-amber-800 dark:text-amber-400">
                                  <span>Źródło: {lead.zrodlo_danych}</span>
                                  <span>Weryfikacja: {fmtDate(lead.data_weryfikacji)}</span>
                                </div>
                              </div>
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
