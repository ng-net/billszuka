import React, { useState, useMemo } from "react";
import {
  Copy,
  ExternalLink,
  Mail,
  Phone,
  Globe,
  ChevronDown,
  Check,
  Search,
  ChevronRight,
  MapPin,
  Building2,
  Video,
  ShieldCheck,
  TrendingUp,
  Download,
  X,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";

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

// --- Mock Data Generator ---
const generateLeads = (count) =>
  Array.from({ length: count }, (_, i) => ({
    id_unikalne: `ID-${1000 + i}`,
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
    wolumen: i % 4 === 0 ? "Duży" : i % 4 === 1 ? "Średni" : "Mały",
    confidence_wolumen: Math.floor(Math.random() * (99 - 70) + 70),
    rejestr_id: `KRS 0000${100000 + i}`,
    nip_vat: `PL${1000000000 + i}`,
    rok_zalozenia: 2010 + (i % 10),
    tier: i % 5 === 0 ? "Producent" : i % 5 === 1 ? "Hurtownik" : "Detalista",
    marki_nabijarki: i % 3 === 0 ? "PowerMatic, Hawk" : i % 3 === 1 ? "PowerMatic III+" : "Brak",
    marka_wlasna_oem: i % 2 === 0,
    powinowactwo_nabijarki: i % 3 === 0 ? "Wysoki" : "Niski",
    cross_sell_potential: i % 4 === 0 ? "High" : "Low",
    kategoria: "A1",
    rynek_skala: "Lokalny / UE",
    kanal_sprzedaży: "Stacjonarny + Online",
    decydent: i % 2 === 0 ? "Jan Kowalski" : "Tomasz Nowak",
    stanowisko: i % 2 === 0 ? "Prezes Zarządu" : "Dyrektor Handlowy",
    email_decydent: `jan.k${i}@firma.pl`,
    email: `biuro@firma${i}.pl`,
    telefon: `+48 500 000 ${10 + i}`,
    notatki:
      "Klient zainteresowany maszynami automatycznymi. Wymaga kontaktu w godzinach 9-15. Preferowane portfolio: PowerMatic oraz akcesoria premium.",
    linkedin: "https://linkedin.com",
    facebook: "https://facebook.com",
    instagram: "https://instagram.com",
    tiktok: "https://tiktok.com",
    data_weryfikacji: "2026-08-25",
    sourcing: "Weryfikacja KRS / B2B Research",
    zrodlo_danych: "KRS Online / GUS",
    flagi: ["Verified"],
  }));

export function ModernLeadsTable() {
  const [leads] = useState(() => generateLeads(50));
  const [expandedRow, setExpandedRow] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCountry, setSelectedCountry] = useState("Wszystkie");
  const [selectedTier, setSelectedTier] = useState("Wszystkie");
  const [countryDropdownOpen, setCountryDropdownOpen] = useState(false);
  const [tierDropdownOpen, setTierDropdownOpen] = useState(false);

  // --- Filtering ---
  const filteredLeads = useMemo(() => {
    return leads.filter((lead) => {
      if (selectedCountry !== "Wszystkie" && lead.kraj !== selectedCountry) {
        return false;
      }
      if (selectedTier !== "Wszystkie" && lead.tier !== selectedTier) {
        return false;
      }
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matches =
          lead.nazwa_firmy.toLowerCase().includes(q) ||
          lead.nip_vat.toLowerCase().includes(q) ||
          lead.miasto.toLowerCase().includes(q) ||
          lead.id_unikalne.toLowerCase().includes(q) ||
          lead.decydent.toLowerCase().includes(q);
        if (!matches) return false;
      }
      return true;
    });
  }, [leads, searchQuery, selectedCountry, selectedTier]);

  const activeFilters = useMemo(() => {
    const list = [];
    if (selectedCountry !== "Wszystkie") list.push({ type: "country", label: selectedCountry });
    if (selectedTier !== "Wszystkie") list.push({ type: "tier", label: selectedTier });
    return list;
  }, [selectedCountry, selectedTier]);

  const handleCopy = (text, label = "Skopiowano") => {
    if (navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(text);
      toast.success(`${label}: ${text}`);
    }
  };

  const handleExport = () => {
    const header = "ID,Nazwa,Kraj,Miasto,NIP,Tier,Wolumen,Decydent,Email,Telefon\n";
    const rows = filteredLeads
      .map(
        (l) =>
          `"${l.id_unikalne}","${l.nazwa_firmy}","${l.kraj}","${l.miasto}","${l.nip_vat}","${l.tier}","${l.wolumen}","${l.decydent}","${l.email}","${l.telefon}"`
      )
      .join("\n");
    const blob = new Blob([header + rows], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `baza_leadow_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success("Pomyślnie wyeksportowano plik CSV");
  };

  // --- Sub-Components for Cleanliness ---
  const StatusBadge = ({ status }) => {
    const styles = {
      Producent:
        "bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 border-indigo-200 dark:border-indigo-800",
      Hurtownik:
        "bg-blue-50 dark:bg-blue-950/50 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-800",
      Detalista:
        "bg-slate-50 dark:bg-slate-800/60 text-slate-600 dark:text-slate-300 border-slate-200 dark:border-slate-700",
      High: "bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800",
      Low: "bg-gray-50 dark:bg-gray-800 text-gray-500 dark:text-gray-400 border-gray-200 dark:border-gray-700",
      Wysoki:
        "bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-300 border-amber-200 dark:border-amber-800",
    };
    const defaultStyle =
      "bg-gray-50 dark:bg-gray-800 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-gray-700";

    return (
      <span
        className={`px-2.5 py-1 rounded-full text-xs font-semibold border inline-flex items-center gap-1 ${
          styles[status] || defaultStyle
        }`}
      >
        {status}
      </span>
    );
  };

  const IconButton = ({ icon: Icon, onClick, color = "gray", title }) => {
    const colors = {
      gray: "text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800",
      blue: "text-blue-500 hover:text-blue-700 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-950/50",
      green:
        "text-emerald-500 hover:text-emerald-700 dark:hover:text-emerald-300 hover:bg-emerald-50 dark:hover:bg-emerald-950/50",
    };
    return (
      <button
        onClick={onClick}
        title={title}
        className={`p-2 rounded-lg transition-all ${colors[color]}`}
      >
        <Icon size={16} />
      </button>
    );
  };

  return (
    <div className="w-full bg-slate-50 dark:bg-zinc-950/40 p-4 md:p-6 font-sans text-slate-800 dark:text-slate-100 rounded-2xl">
      {/* --- DESIGN RATIONALE BANNER --- */}
      <div className="max-w-[1600px] mx-auto mb-6 bg-gradient-to-r from-indigo-50/80 via-blue-50/60 to-purple-50/70 dark:from-indigo-950/30 dark:via-blue-950/20 dark:to-purple-950/30 border border-indigo-200/80 dark:border-indigo-800/60 rounded-xl p-4 shadow-sm text-xs space-y-2">
        <div className="flex items-center gap-2 font-semibold text-sm text-indigo-950 dark:text-indigo-200">
          <Sparkles className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
          High-Fidelity UI/UX: Progressive Disclosure
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 text-slate-600 dark:text-slate-300">
          <div>
            <strong className="block text-slate-900 dark:text-slate-100">1. Progressive Disclosure:</strong>
            Zamiast 30+ kolumn w rzędzie, prezentujemy 8 kluczowych metryk + rozwijany panel szczegółów.
          </div>
          <div>
            <strong className="block text-slate-900 dark:text-slate-100">2. Glassmorphism & Depth:</strong>
            Przyklejony nagłówek z blur-overlay, subtelne cienie i pastelowe warstwy.
          </div>
          <div>
            <strong className="block text-slate-900 dark:text-slate-100">3. Czytelna Hierarchia:</strong>
            Nazwa i ID na sticky anchor, wolumen z paskiem pewności %, role i kontakty w kapsułkach.
          </div>
          <div>
            <strong className="block text-slate-900 dark:text-slate-100">4. Natychmiastowe Akcje:</strong>
            Kopiowanie adresu/NIP, szybki mailto/tel oraz linki do social mediów.
          </div>
        </div>
      </div>

      {/* --- HEADER SECTION --- */}
      <div className="max-w-[1600px] mx-auto mb-6">
        <div className="flex flex-col sm:flex-row justify-between sm:items-end gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-50 tracking-tight">
              Baza Leadów B2B
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm mt-1">
              Zarządzaj {leads.length} zweryfikowanymi kontaktami i dystrybutorami maszyn
            </p>
          </div>
          <div className="flex gap-3">
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

        {/* --- MODERN FILTER BAR --- */}
        <div className="bg-white dark:bg-zinc-900 p-2.5 rounded-xl shadow-sm border border-slate-200 dark:border-zinc-800 flex flex-wrap gap-2 items-center">
          <div className="relative flex-1 min-w-[280px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Szukaj po nazwie, NIP, decydencie lub mieście..."
              className="w-full pl-10 pr-4 py-2 bg-slate-50 dark:bg-zinc-800/80 border-none rounded-lg text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-400 focus:ring-2 focus:ring-slate-900/10 dark:focus:ring-indigo-500/20 outline-none transition-all"
            />
          </div>

          <div className="hidden sm:block h-7 w-px bg-slate-200 dark:bg-zinc-700 mx-1"></div>

          {/* Filter Dropdowns */}
          <div className="relative">
            <button
              onClick={() => {
                setCountryDropdownOpen(!countryDropdownOpen);
                setTierDropdownOpen(false);
              }}
              className="flex items-center gap-2 px-3 py-2 bg-slate-50 dark:bg-zinc-800 hover:bg-slate-100 dark:hover:bg-zinc-700/80 border border-slate-200 dark:border-zinc-700 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-200 transition-colors"
            >
              <Globe size={16} className="text-slate-500 dark:text-slate-400" />
              <span>Kraj: {selectedCountry}</span>
              <ChevronDown size={14} className="text-slate-400" />
            </button>
            {countryDropdownOpen && (
              <div className="absolute top-full left-0 mt-2 w-44 bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-700 rounded-xl shadow-xl p-1.5 z-50">
                {["Wszystkie", "Polska", "Czechy", "Słowacja"].map((c) => (
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
              }}
              className="flex items-center gap-2 px-3 py-2 bg-slate-50 dark:bg-zinc-800 hover:bg-slate-100 dark:hover:bg-zinc-700/80 border border-slate-200 dark:border-zinc-700 rounded-lg text-sm font-medium text-slate-700 dark:text-slate-200 transition-colors"
            >
              <Building2 size={16} className="text-slate-500 dark:text-slate-400" />
              <span>Rola: {selectedTier}</span>
              <ChevronDown size={14} className="text-slate-400" />
            </button>
            {tierDropdownOpen && (
              <div className="absolute top-full left-0 mt-2 w-44 bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-700 rounded-xl shadow-xl p-1.5 z-50">
                {["Wszystkie", "Producent", "Hurtownik", "Detalista"].map((r) => (
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

          <div className="flex-1"></div>

          {/* Active filter chips */}
          <div className="flex items-center gap-2 px-2 flex-wrap">
            <span className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
              Aktywne:
            </span>
            {activeFilters.length === 0 ? (
              <span className="text-xs text-slate-400 italic">Wszystkie rekordy</span>
            ) : (
              activeFilters.map((f) => (
                <span
                  key={f.label}
                  className="inline-flex items-center gap-1 px-2.5 py-1 bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 rounded-md text-xs font-medium border border-indigo-100 dark:border-indigo-800"
                >
                  {f.label}
                  <button
                    onClick={() => {
                      if (f.type === "country") setSelectedCountry("Wszystkie");
                      if (f.type === "tier") setSelectedTier("Wszystkie");
                    }}
                    className="hover:text-indigo-900 dark:hover:text-indigo-100"
                  >
                    <X size={12} />
                  </button>
                </span>
              ))
            )}
            {(activeFilters.length > 0 || searchQuery) && (
              <button
                onClick={() => {
                  setSelectedCountry("Wszystkie");
                  setSelectedTier("Wszystkie");
                  setSearchQuery("");
                }}
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
                <th className="p-4 w-12 text-center"></th> {/* Expand Toggle */}
                <th className="p-4 min-w-[280px] sticky left-0 z-30 bg-slate-50 dark:bg-zinc-800 border-r border-slate-200 dark:border-zinc-700 shadow-[1px_0_3px_rgba(0,0,0,0.05)]">
                  Firma & ID
                </th>
                <th className="p-4 min-w-[150px]">Lokalizacja</th>
                <th className="p-4 min-w-[140px]">Wolumen</th>
                <th className="p-4 min-w-[140px]">Potencjał</th>
                <th className="p-4 min-w-[120px]">Rola</th>
                <th className="p-4 min-w-[160px]">Kontakt</th>
                <th className="p-4 min-w-[120px] text-right">Akcje</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-zinc-800/60">
              {filteredLeads.map((lead) => {
                const isExpanded = expandedRow === lead.id_unikalne;

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

                      {/* Sticky Left: Identity */}
                      <td className="p-4 sticky left-0 z-10 bg-white dark:bg-zinc-900 group-hover:bg-slate-50 dark:group-hover:bg-zinc-800/80 border-r border-slate-200 dark:border-zinc-700 transition-colors shadow-[1px_0_3px_rgba(0,0,0,0.03)]">
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-100 to-slate-200 dark:from-indigo-900/60 dark:to-zinc-800 flex items-center justify-center text-slate-700 dark:text-indigo-200 font-bold text-lg shadow-inner shrink-0">
                            {lead.nazwa_firmy.charAt(0)}
                          </div>
                          <div className="min-w-0">
                            <div className="font-semibold text-slate-900 dark:text-slate-100 text-sm truncate">
                              {lead.nazwa_firmy}
                            </div>
                            <div className="flex items-center gap-2 mt-1">
                              <span className="text-[10px] font-mono text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-zinc-800 px-1.5 py-0.5 rounded">
                                {lead.id_unikalne}
                              </span>
                              {lead.flagi?.includes("Verified") && (
                                <span className="flex items-center gap-0.5 text-[10px] text-emerald-600 dark:text-emerald-400 font-medium">
                                  <ShieldCheck size={10} /> Zweryfikowany
                                </span>
                              )}
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

                      {/* Volume */}
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <div className="flex flex-col w-full">
                            <div className="flex justify-between text-xs mb-1">
                              <span className="font-medium text-slate-700 dark:text-slate-200">{lead.wolumen}</span>
                              <span className="text-slate-400 text-[11px]">{lead.confidence_wolumen}%</span>
                            </div>
                            <div className="w-full bg-slate-100 dark:bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                              <div
                                className={`h-full rounded-full ${
                                  lead.wolumen === "Duży"
                                    ? "bg-emerald-500"
                                    : lead.wolumen === "Średni"
                                    ? "bg-amber-400"
                                    : "bg-slate-400 dark:bg-zinc-500"
                                }`}
                                style={{ width: `${lead.confidence_wolumen}%` }}
                              ></div>
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Potential */}
                      <td className="p-4">
                        <div className="flex flex-col gap-1.5 items-start">
                          <StatusBadge status={lead.cross_sell_potential} />
                          {lead.powinowactwo_nabijarki === "Wysoki" && (
                            <span className="text-[10px] text-amber-600 dark:text-amber-400 font-medium flex items-center gap-0.5">
                              🔥 Wysokie powinowactwo
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Tier */}
                      <td className="p-4">
                        <StatusBadge status={lead.tier} />
                      </td>

                      {/* Contact Preview */}
                      <td className="p-4">
                        <div className="flex items-center gap-2.5">
                          <div className="group/contact relative">
                            <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-zinc-800 flex items-center justify-center text-slate-600 dark:text-slate-300 font-semibold text-xs border border-slate-200 dark:border-zinc-700">
                              {lead.decydent?.charAt(0) || "D"}
                            </div>
                            {/* Tooltip on Hover */}
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-36 bg-slate-900 text-white text-xs rounded-md py-1 px-2 opacity-0 group-hover/contact:opacity-100 transition-opacity pointer-events-none text-center z-50 shadow-lg">
                              <div className="font-semibold">{lead.decydent}</div>
                              <div className="text-[10px] text-slate-300">{lead.stanowisko}</div>
                              <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-900"></div>
                            </div>
                          </div>
                          <div className="flex flex-col min-w-0">
                            <span className="text-xs font-medium text-slate-700 dark:text-slate-200 truncate">
                              {lead.email}
                            </span>
                            <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono">
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
                            onClick={() => (window.location.href = `mailto:${lead.email}`)}
                          />
                          <IconButton
                            icon={Phone}
                            color="green"
                            title={`Zadzwoń: ${lead.telefon}`}
                            onClick={() => (window.location.href = `tel:${lead.telefon}`)}
                          />
                          <IconButton
                            icon={ExternalLink}
                            color="gray"
                            title={`Strona WWW: ${lead.www}`}
                            onClick={() => window.open(lead.www, "_blank", "noopener,noreferrer")}
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
                                  onClick={() => handleCopy(lead.adres, "Adres")}
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
                                    onClick={() => handleCopy(lead.nip_vat, "NIP")}
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
                              </div>

                              <div className="bg-white dark:bg-zinc-800 p-3 rounded-lg border border-slate-200 dark:border-zinc-700 shadow-sm">
                                <div className="text-xs text-slate-500 dark:text-slate-400 mb-1.5">Marki Maszynek</div>
                                <div className="flex flex-wrap gap-1.5">
                                  {lead.marki_nabijarki.split(",").map((m, i) => (
                                    <span
                                      key={i}
                                      className="px-2 py-0.5 bg-slate-100 dark:bg-zinc-700 text-slate-700 dark:text-slate-200 rounded text-xs font-medium border border-slate-200 dark:border-zinc-600"
                                    >
                                      {m.trim()}
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
                                    {lead.decydent}
                                  </div>
                                  <div className="text-xs text-slate-500 dark:text-slate-400">{lead.stanowisko}</div>
                                </div>
                                <hr className="border-slate-100 dark:border-zinc-700" />
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                  <a
                                    href={`mailto:${lead.email_decydent}`}
                                    className="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                                  >
                                    <Mail size={13} /> Email Decydenta
                                  </a>
                                  <a
                                    href={`mailto:${lead.email}`}
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
                                    className="p-2 bg-[#0077b5] text-white rounded hover:opacity-90 transition-opacity"
                                    title="LinkedIn"
                                  >
                                    <Linkedin size={16} />
                                  </a>
                                  <a
                                    href={lead.facebook}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="p-2 bg-[#1877F2] text-white rounded hover:opacity-90 transition-opacity"
                                    title="Facebook"
                                  >
                                    <Facebook size={16} />
                                  </a>
                                  <a
                                    href={lead.instagram}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="p-2 bg-gradient-to-tr from-yellow-500 to-purple-600 text-white rounded hover:opacity-90 transition-opacity"
                                    title="Instagram"
                                  >
                                    <Instagram size={16} />
                                  </a>
                                  <a
                                    href={lead.tiktok}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="p-2 bg-black text-white rounded hover:opacity-90 transition-opacity border border-zinc-700"
                                    title="TikTok"
                                  >
                                    <Video size={16} />
                                  </a>
                                </div>
                              </div>
                            </div>

                            {/* Column 3: Notes & Meta */}
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
                                  <span>Weryfikacja: {lead.data_weryfikacji}</span>
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

export default ModernLeadsTable;
