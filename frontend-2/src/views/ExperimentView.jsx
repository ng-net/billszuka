import React, { useState, useMemo } from "react";
import {
  Copy,
  ExternalLink,
  Mail,
  Phone,
  Globe,
  Filter,
  ChevronDown,
  Check,
  Search,
  MoreHorizontal,
  Video,
  Sparkles,
  Download,
  Play,
  Pause,
  Volume2,
  Maximize2,
  Film,
  Layers,
} from "lucide-react";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { ModernLeadsTable } from "./ModernLeadsTable";
import { ExperimentViewV3 } from "./ExperimentViewV3";
import { getSampleLeads } from "@/lib/sampleLeads";

const LinkedinIcon = ({ size = 14, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
    <rect x="2" y="9" width="4" height="12" />
    <circle cx="4" cy="4" r="2" />
  </svg>
);

const FacebookIcon = ({ size = 14, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" />
  </svg>
);

const InstagramIcon = ({ size = 14, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
    <line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
  </svg>
);

const TikTokIcon = ({ size = 14, className }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M9 12a4 4 0 1 0 4 4V4a5 5 0 0 0 5 5" />
  </svg>
);

// --- Mock Data Generator (with video demos for LEAD-1000 and LEAD-1001) ---
const generateLeads = (count) =>
  Array.from({ length: count }, (_, i) => {
    const id = `LEAD-${1000 + i}`;
    const isDemo1 = id === "LEAD-1000";
    const isDemo2 = id === "LEAD-1001";
    const hasVideo = isDemo1 || isDemo2;
    return {
      id_unikalne: id,
      nazwa_firmy: isDemo1
        ? "PowerMatic Polska Distribution Sp. z o.o."
        : isDemo2
        ? "Hawk Rollers Europe B2B"
        : `Firma Handlowa ${i + 1} Sp. z o.o.`,
      kraj: isDemo1 ? "Polska" : isDemo2 ? "Czechy" : i % 3 === 0 ? "Polska" : i % 3 === 1 ? "Czechy" : "Słowacja",
      miasto: isDemo1 ? "Warszawa" : isDemo2 ? "Praga" : i % 2 === 0 ? "Warszawa" : "Praga",
      adres: `ul. Przemysłowa ${i}, 00-001 ${i % 2 === 0 ? "Warszawa" : "Praga"}`,
      www: "https://example.com",
      wolumen: isDemo1 || isDemo2 ? "Duży" : i % 4 === 0 ? "Duży" : i % 4 === 1 ? "Średni" : "Mały",
      confidence_wolumen: "95%",
      rejestr_id: `KRS 0000${100000 + i}`,
      nip_vat: `PL${1000000000 + i}`,
      rok_zalozenia: isDemo1 ? 2012 : isDemo2 ? 2015 : 2010 + (i % 10),
      tier: isDemo1 ? "Dystrybutor Główny" : isDemo2 ? "Hurtownik" : i % 5 === 0 ? "Producent" : i % 5 === 1 ? "Hurtownik" : "Detalista",
      marki_nabijarki: isDemo1 ? "PowerMatic III+, PowerMatic II+" : isDemo2 ? "Hawk Electric Roller, PowerMatic" : i % 3 === 0 ? "PowerMatic, Hawk" : "Brak danych",
      marka_wlasna_oem: "Tak",
      powinowactwo_nabijarki: "Bardzo wysoki",
      cross_sell_potential: "High",
      kategoria: "A1",
      rynek_skala: "Krajowy / UE",
      kanal_sprzedaży: "Hurt + Sieci Sklepów",
      decydent: isDemo1 ? "Marek Wiśniewski" : isDemo2 ? "Tomáš Novák" : "Jan Kowalski",
      stanowisko: isDemo1 ? "Dyrektor Handlowy" : isDemo2 ? "Head of Procurement" : "Prezes Zarządu",
      email_decydent: isDemo1 ? "m.wisniewski@powermatic-pl.com" : isDemo2 ? "t.novak@hawk-eu.cz" : `jan.k${i}@firma.pl`,
      email: isDemo1 ? "kontakt@powermatic-pl.com" : isDemo2 ? "b2b@hawk-eu.cz" : `biuro@firma${i}.pl`,
      telefon: isDemo1 ? "+48 22 800 10 20" : isDemo2 ? "+420 220 500 600" : `+48 500 000 ${10 + i}`,
      notatki: isDemo1
        ? "Oficjalny dystrybutor maszyn PowerMatic. Dostępne pełne wideo demo automatycznego cyklu ubijania i nabijania."
        : isDemo2
        ? "Czołowy hurtownik maszyn Hawk. Wideo demo przedstawia test obciążeniowy (120 gilz/min)."
        : "Klient zainteresowany maszynami automatycznymi.",
      linkedin: "https://linkedin.com",
      facebook: "https://facebook.com",
      instagram: "https://instagram.com",
      tiktok: "https://tiktok.com",
      data_weryfikacji: "2026-08-28",
      sourcing: "Weryfikacja bezpośrednia B2B",
      zrodlo_danych: "KRS / ASO",
      flagi: hasVideo ? ["Verified", "Wideo Demo"] : ["Verified"],
      has_video_demo: hasVideo,
      video_demo_title: isDemo1
        ? "PowerMatic III+ — Test Pracy Cyklu Automatycznego"
        : "Hawk Electric Roller — Przemysłowy Test Wydajności B2B",
      video_demo_duration: isDemo1 ? "03:45" : "02:18",
      video_demo_specs: isDemo1
        ? ["Elektroniczny podajnik tytoniu", "Tytanowe ostrze tnące", "Licznik dzienny/całkowity", "Regulacja gęstości 3-stopniowa"]
        : ["Wydajność: do 120 gilz/min", "Wzmocniona przekładnia metalowa", "Obsługa gilz 84mm i 100mm", "Cicha praca <62dB"],
      video_demo_desc: isDemo1
        ? "Oficjalny materiał prezentujący automatyczne napełnianie gilz standardowych i 100mm z cyfrową kontrolą ubicia."
        : "Prezentacja pracy nabijarki Hawk w warunkach ciągłej eksploatacji hurtowej z demonstracją podajnika taśmowego.",
      related_to: null,
    };
  });

export function ExperimentView() {
  const [activeExperiment, setActiveExperiment] = useState("modern");

  return (
    <div className="p-4 space-y-4 max-w-full">
      {/* Top Sub-Navigation Tabs for Experiments */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-white dark:bg-zinc-900 border border-slate-200 dark:border-zinc-800 p-2 rounded-2xl shadow-sm">
        <div className="flex items-center gap-1.5 p-1 bg-slate-100 dark:bg-zinc-800 rounded-xl">
          <button
            onClick={() => setActiveExperiment("modern")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeExperiment === "modern"
                ? "bg-white dark:bg-zinc-900 text-indigo-600 dark:text-indigo-400 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <Sparkles size={14} className="text-indigo-500" />
            <span>Modern Leads (Progressive Disclosure)</span>
            <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 font-bold border border-indigo-200 dark:border-indigo-800">
              Nowość
            </span>
          </button>

          <button
            onClick={() => setActiveExperiment("video-grid")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeExperiment === "video-grid"
                ? "bg-white dark:bg-zinc-900 text-rose-600 dark:text-rose-400 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <Film size={14} className="text-rose-500" />
            <span>Video Demos & Sticky Grid</span>
          </button>

          <button
            onClick={() => setActiveExperiment("v3")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
              activeExperiment === "v3"
                ? "bg-white dark:bg-zinc-900 text-emerald-600 dark:text-emerald-400 shadow-sm"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            <Layers size={14} className="text-emerald-500" />
            <span>Compact · Filter Rail · Faceted</span>
            <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 font-bold border border-emerald-200 dark:border-emerald-800">
              Nowość
            </span>
          </button>
        </div>

        <div className="text-xs text-slate-500 dark:text-slate-400 pr-2 hidden md:block">
          Laboratorium UI/UX · BILLSzuka Experimental Hub
        </div>
      </div>

      {/* Render Selected Experiment */}
      {activeExperiment === "modern" ? (
        <ModernLeadsTable leads={getSampleLeads()} />
      ) : activeExperiment === "v3" ? (
        <ExperimentViewV3 leads={getSampleLeads()} />
      ) : (
        <VideoGridExperiment leads={getSampleLeads()} />
      )}
    </div>
  );
}

function VideoGridExperiment({ leads: leadsProp }) {
  const [leads] = useState(() => leadsProp || generateLeads(50));
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCountryFilters, setActiveCountryFilters] = useState([]);
  const [countryFilterOpen, setCountryFilterOpen] = useState(false);
  const [tierFilter, setTierFilter] = useState(null);
  const [volumeFilter, setVolumeFilter] = useState(null);
  const [videoOnlyFilter, setVideoOnlyFilter] = useState(false);
  const [selectedVideoLead, setSelectedVideoLead] = useState(null);
  const [isPlaying, setIsPlaying] = useState(true);

  // --- Filtering ---
  const filteredLeads = useMemo(() => {
    return leads.filter((lead) => {
      if (videoOnlyFilter && !lead.has_video_demo) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const match =
          lead.nazwa_firmy.toLowerCase().includes(q) ||
          lead.nip_vat.toLowerCase().includes(q) ||
          lead.id_unikalne.toLowerCase().includes(q) ||
          lead.miasto.toLowerCase().includes(q);
        if (!match) return false;
      }
      if (activeCountryFilters.length > 0 && !activeCountryFilters.includes(lead.kraj)) {
        return false;
      }
      if (tierFilter && lead.tier !== tierFilter) return false;
      if (volumeFilter && lead.wolumen !== volumeFilter) return false;
      return true;
    });
  }, [leads, searchQuery, activeCountryFilters, tierFilter, volumeFilter]);

  const toggleCountry = (country) => {
    setActiveCountryFilters((prev) =>
      prev.includes(country) ? prev.filter((c) => c !== country) : [...prev, country]
    );
  };

  // --- Helper Components ---
  const Badge = ({ children, type = "default" }) => {
    const styles = {
      default: "bg-gray-100 text-gray-700 border-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-700",
      success: "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800",
      warning: "bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800",
      info: "bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-800",
      purple: "bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-950/40 dark:text-purple-300 dark:border-purple-800",
    };

    let styleClass = styles.default;
    if (type === "Producent") styleClass = styles.purple;
    if (type === "Hurtownik") styleClass = styles.info;
    if (type === "High" || type === "Wysoki" || type === "Duży") styleClass = styles.success;
    if (type === "Tak" || type === "Średni") styleClass = styles.warning;

    return (
      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${styleClass}`}>
        {children}
      </span>
    );
  };

  const ActionButton = ({ icon: Icon, onClick, tooltip }) => (
    <button
      onClick={(e) => {
        e.stopPropagation();
        onClick?.(e);
      }}
      className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-gray-800 rounded transition-colors"
      title={tooltip}
      aria-label={tooltip}
    >
      <Icon size={14} />
    </button>
  );

  const MaskedText = ({ text }) => {
    if (!text) return "-";
    const parts = text.trim().split(/\s+/);
    if (parts.length >= 2) {
      const surname = parts[parts.length - 1];
      const maskedSurname = surname.substring(0, 2) + "***" + surname.substring(surname.length - 1);
      return <span className="font-mono text-gray-500">{parts[0]} {maskedSurname}</span>;
    }
    const visible = text.substring(0, 3);
    const masked = "*".repeat(Math.max(0, text.length - 3));
    return <span className="font-mono text-gray-500">{visible}{masked}</span>;
  };

  const handleCopy = (text, label = "Skopiowano") => {
    navigator.clipboard?.writeText(text);
    toast.success(`${label}: ${text}`);
  };

  const handleExport = () => {
    const csvContent =
      "data:text/csv;charset=utf-8," +
      ["ID,Nazwa,Kraj,Miasto,NIP,Tier,Wolumen"]
        .concat(
          filteredLeads.map(
            (l) => `${l.id_unikalne},"${l.nazwa_firmy}",${l.kraj},${l.miasto},${l.nip_vat},${l.tier},${l.wolumen}`
          )
        )
        .join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "experiment_leads.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success("Wyeksportowano CSV");
  };

  return (
    <div className="space-y-4 max-w-full">
      {/* Design Rationale Banner */}
      <div className="bg-blue-50/70 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-xl p-4 text-xs text-blue-900 dark:text-blue-200 space-y-2">
        <div className="flex items-center gap-2 font-semibold text-sm text-blue-950 dark:text-blue-100">
          <Sparkles className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          Eksperymentalny Grid Leadów (Design Rationale)
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 pt-1">
          <div>
            <strong className="block text-foreground">Sticky Anchors:</strong>
            ID i Firma są stale przypięte z lewej strony przy przewijaniu.
          </div>
          <div>
            <strong className="block text-foreground">Hierarchia Wizualna:</strong>
            Kolorystyczne badge dla Tieru, Wolumenu i Potencjału Maszynek.
          </div>
          <div>
            <strong className="block text-foreground">Aktywne Komórki:</strong>
            1-klik kopiowanie NIP, bezpośrednie linki tel:, mailto: i social w nowej karcie.
          </div>
          <div>
            <strong className="block text-foreground">QuickChips:</strong>
            Szybkie filtry krajów i ról bez konieczności otwierania bocznych paneli.
          </div>
        </div>
      </div>

      {/* Main Table Card */}
      <div className="w-full bg-white dark:bg-card rounded-xl shadow-sm border border-gray-200 dark:border-border overflow-hidden font-sans text-sm">
        {/* --- TOP CONTROL BAR --- */}
        <div className="p-4 border-b border-gray-200 dark:border-border bg-gray-50/50 dark:bg-muted/20 flex flex-col gap-4">
          <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-3">
            <div className="flex items-center gap-2">
              <h2 className="text-lg font-semibold text-gray-800 dark:text-foreground">Baza Leadów</h2>
              <span className="bg-gray-200 dark:bg-muted text-gray-600 dark:text-muted-foreground px-2 py-0.5 rounded-md text-xs font-medium">
                {filteredLeads.length} wyników
              </span>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative flex-1 sm:flex-initial">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Szukaj po nazwie, NIP..."
                  className="pl-9 pr-4 py-2 border border-gray-300 dark:border-input bg-background rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none w-full sm:w-64"
                />
              </div>
              <button
                onClick={handleExport}
                className="flex items-center gap-1.5 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium shadow-sm shadow-blue-200 dark:shadow-none"
              >
                <Download size={15} />
                Eksportuj CSV
              </button>
            </div>
          </div>

          {/* QuickChips (Country, Tier, Volume, Video Demo) */}
          <div className="flex items-center gap-2 flex-wrap text-xs">
            <span className="text-gray-400 dark:text-muted-foreground font-medium mr-1">Filtry:</span>

            {/* Video Demo Quick Chip */}
            <button
              onClick={() => setVideoOnlyFilter((prev) => !prev)}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold transition-all shadow-sm ${
                videoOnlyFilter
                  ? "bg-gradient-to-r from-rose-500 to-amber-500 text-white shadow-rose-500/25 ring-2 ring-rose-400/40"
                  : "bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800 hover:bg-rose-100"
              }`}
            >
              <Film className="h-3 w-3" />
              <span>Wideo Demos</span>
              <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${videoOnlyFilter ? "bg-white/20 text-white" : "bg-rose-200/60 dark:bg-rose-900/60 text-rose-800 dark:text-rose-200 font-bold"}`}>
                2
              </span>
            </button>

            <span className="text-xs font-semibold text-gray-500 dark:text-muted-foreground uppercase tracking-wider mr-1">
              Aktywne filtry:
            </span>

            {/* Country Popover Trigger */}
            <div className="relative">
              <button
                onClick={() => setCountryFilterOpen(!countryFilterOpen)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
                  activeCountryFilters.length > 0
                    ? "bg-blue-50 border-blue-200 text-blue-700 dark:bg-blue-950/40 dark:border-blue-800 dark:text-blue-300"
                    : "bg-white dark:bg-background border-gray-300 dark:border-input text-gray-600 dark:text-muted-foreground hover:border-gray-400"
                }`}
              >
                <Globe size={12} />
                Kraj: {activeCountryFilters.length > 0 ? activeCountryFilters.join(", ") : "Wybierz"}
                <ChevronDown size={12} />
              </button>

              {countryFilterOpen && (
                <div className="absolute top-full left-0 mt-2 w-48 bg-white dark:bg-popover rounded-lg shadow-xl border border-gray-200 dark:border-border p-2 z-50">
                  {["Polska", "Czechy", "Słowacja", "Niemcy"].map((country) => (
                    <div
                      key={country}
                      onClick={() => toggleCountry(country)}
                      className="flex items-center gap-2 px-3 py-2 hover:bg-gray-50 dark:hover:bg-muted rounded cursor-pointer text-sm text-gray-700 dark:text-foreground"
                    >
                      <div
                        className={`w-4 h-4 rounded border flex items-center justify-center ${
                          activeCountryFilters.includes(country)
                            ? "bg-blue-600 border-blue-600"
                            : "border-gray-300 dark:border-input"
                        }`}
                      >
                        {activeCountryFilters.includes(country) && <Check size={10} className="text-white" />}
                      </div>
                      {country}
                    </div>
                  ))}
                  {activeCountryFilters.length > 0 && (
                    <button
                      onClick={() => setActiveCountryFilters([])}
                      className="w-full mt-2 pt-2 border-t text-xs text-blue-600 dark:text-blue-400 text-center hover:underline"
                    >
                      Wyczyść filtry kraju
                    </button>
                  )}
                </div>
              )}
            </div>

            {/* Dynamic Chips */}
            <button
              onClick={() => setTierFilter(tierFilter === "Producent" ? null : "Producent")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                tierFilter === "Producent"
                  ? "bg-purple-100 text-purple-800 border-purple-300 dark:bg-purple-950/60 dark:text-purple-200"
                  : "bg-gray-100 text-gray-600 border-gray-200 hover:bg-gray-200 dark:bg-muted dark:text-muted-foreground"
              }`}
            >
              Tier: Producent
              {tierFilter === "Producent" && <Check size={12} />}
            </button>

            <button
              onClick={() => setVolumeFilter(volumeFilter === "Duży" ? null : "Duży")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                volumeFilter === "Duży"
                  ? "bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-950/60 dark:text-emerald-200"
                  : "bg-gray-100 text-gray-600 border-gray-200 hover:bg-gray-200 dark:bg-muted dark:text-muted-foreground"
              }`}
            >
              Wolumen: Duży
              {volumeFilter === "Duży" && <Check size={12} />}
            </button>

            {(activeCountryFilters.length > 0 || tierFilter || volumeFilter || searchQuery) && (
              <button
                onClick={() => {
                  setActiveCountryFilters([]);
                  setTierFilter(null);
                  setVolumeFilter(null);
                  setSearchQuery("");
                }}
                className="text-xs text-red-600 dark:text-red-400 hover:underline ml-2"
              >
                Resetuj filtry
              </button>
            )}
          </div>
        </div>

        {/* --- TABLE HEADER --- */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50 dark:bg-muted/40 border-b border-gray-200 dark:border-border text-xs uppercase tracking-wider text-gray-500 dark:text-muted-foreground font-semibold">
                {/* Sticky Left Group */}
                <th className="sticky left-0 z-20 bg-gray-50 dark:bg-muted p-3 border-r border-gray-200 dark:border-border w-28">
                  id
                </th>
                <th className="sticky left-28 z-20 bg-gray-50 dark:bg-muted p-3 border-r border-gray-200 dark:border-border min-w-[260px]">
                  Nazwa
                </th>

                {/* Standard Columns */}
                <th className="p-3 border-r border-gray-100 dark:border-border/50 min-w-[140px]">Miasto / Kraj</th>
                <th className="p-3 border-r border-gray-100 dark:border-border/50 min-w-[130px]">Wolumen</th>
                <th className="p-3 border-r border-gray-100 dark:border-border/50 min-w-[120px]">Rola (Tier)</th>
                <th className="p-3 border-r border-gray-100 dark:border-border/50 min-w-[160px]">NIP / KRS</th>
                <th className="p-3 border-r border-gray-100 dark:border-border/50 min-w-[160px]">Marki Maszynek</th>
                <th className="p-3 border-r border-gray-100 dark:border-border/50 min-w-[140px]">Potencjał</th>
                <th className="p-3 border-r border-gray-100 dark:border-border/50 min-w-[100px]">Start</th>

                {/* Contact Group */}
                <th className="p-3 border-r border-gray-100 dark:border-border/50 min-w-[200px]">Kontakt</th>
                <th className="p-3 border-r border-gray-100 dark:border-border/50 min-w-[120px]">Social</th>
                <th className="p-3 min-w-[100px]">Data</th>
              </tr>
            </thead>

            {/* --- TABLE BODY --- */}
            <tbody className="divide-y divide-gray-100 dark:divide-border/40">
              {filteredLeads.map((lead) => (
                <tr
                  key={lead.id_unikalne}
                  className="hover:bg-blue-50/30 dark:hover:bg-muted/30 transition-colors group"
                >
                  {/* 1. ID (Sticky) */}
                  <td className="sticky left-0 z-10 bg-white dark:bg-card group-hover:bg-blue-50/30 dark:group-hover:bg-muted/40 p-3 border-r border-gray-200 dark:border-border font-mono text-xs text-gray-500">
                    <div className="flex items-center justify-between">
                      <span>{lead.id_unikalne}</span>
                      <ActionButton
                        icon={Copy}
                        tooltip="Kopiuj ID"
                        onClick={() => handleCopy(lead.id_unikalne, "ID")}
                      />
                    </div>
                  </td>

                  {/* 2. Company Name (Sticky) */}
                  <td className="sticky left-28 z-10 bg-white dark:bg-card group-hover:bg-blue-50/30 dark:group-hover:bg-muted/40 p-3 border-r border-gray-200 dark:border-border">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-gray-900 dark:text-foreground truncate max-w-[220px]" title={lead.nazwa_firmy}>
                        {lead.nazwa_firmy}
                      </span>
                      {lead.has_video_demo && (
                        <button
                          onClick={() => {
                            setSelectedVideoLead(lead);
                            setIsPlaying(true);
                          }}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-gradient-to-r from-rose-500 to-amber-500 text-white shadow-sm hover:scale-105 active:scale-95 transition-transform shrink-0"
                          title="Odtwórz wideo demo"
                        >
                          <Play className="h-2.5 w-2.5 fill-current" />
                          <span>Demo ({lead.video_demo_duration})</span>
                        </button>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      {lead.marki_nabijarki !== "Brak danych" && (
                        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 border border-indigo-100 dark:border-indigo-800">
                          🏭 Posiada maszynę
                        </span>
                      )}
                      <span className="text-[10px] text-gray-400">{lead.kategoria}</span>
                    </div>
                  </td>

                  {/* 3. Location */}
                  <td className="p-3 border-r border-gray-100 dark:border-border/50 text-gray-600 dark:text-muted-foreground">
                    <div className="font-medium text-foreground">{lead.miasto}</div>
                    <div className="text-xs text-gray-400">{lead.kraj}</div>
                  </td>

                  {/* 4. Volume */}
                  <td className="p-3 border-r border-gray-100 dark:border-border/50">
                    <div className="flex items-center gap-2">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          lead.wolumen === "Duży"
                            ? "bg-green-500"
                            : lead.wolumen === "Średni"
                            ? "bg-amber-500"
                            : "bg-gray-300"
                        }`}
                      ></span>
                      <span className="text-gray-700 dark:text-foreground">{lead.wolumen}</span>
                    </div>
                    <div className="text-[10px] text-gray-400 mt-0.5 flex items-center gap-1">
                      Pewność: {lead.confidence_wolumen}
                    </div>
                  </td>

                  {/* 5. Tier */}
                  <td className="p-3 border-r border-gray-100 dark:border-border/50">
                    <Badge type={lead.tier}>{lead.tier}</Badge>
                  </td>

                  {/* 6. IDs (Copyable) */}
                  <td className="p-3 border-r border-gray-100 dark:border-border/50 font-mono text-xs text-gray-600 dark:text-muted-foreground">
                    <div className="flex items-center justify-between group/id">
                      <span className="truncate mr-2 font-medium text-foreground">{lead.nip_vat}</span>
                      <ActionButton
                        icon={Copy}
                        tooltip="Kopiuj NIP"
                        onClick={() => handleCopy(lead.nip_vat, "NIP")}
                      />
                    </div>
                    <div className="text-[10px] text-gray-400 truncate">{lead.rejestr_id}</div>
                  </td>

                  {/* 7. Brands */}
                  <td className="p-3 border-r border-gray-100 dark:border-border/50 text-xs text-gray-600 dark:text-muted-foreground">
                    {lead.marki_nabijarki.split(",").map((m, i) => (
                      <span
                        key={i}
                        className="bg-gray-100 dark:bg-muted px-1.5 py-0.5 rounded mr-1 text-gray-600 dark:text-foreground text-[11px]"
                      >
                        {m.trim()}
                      </span>
                    ))}
                  </td>

                  {/* 8. Potential */}
                  <td className="p-3 border-r border-gray-100 dark:border-border/50">
                    <div className="flex flex-col gap-1">
                      <Badge type={lead.cross_sell_potential}>{lead.cross_sell_potential}</Badge>
                      <Badge type={lead.powinowactwo_nabijarki === "Wysoki" ? "success" : "default"}>
                        {lead.powinowactwo_nabijarki}
                      </Badge>
                    </div>
                  </td>

                  {/* 9. Start Year */}
                  <td className="p-3 border-r border-gray-100 dark:border-border/50 text-xs tabular-nums text-muted-foreground">
                    {lead.rok_zalozenia}
                  </td>

                  {/* 10. Contact Actions */}
                  <td className="p-3 border-r border-gray-100 dark:border-border/50">
                    <div className="flex flex-col gap-1.5">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500 w-16 truncate">
                          <MaskedText text={lead.decydent} />
                        </span>
                        <a
                          href={`mailto:${lead.email_decydent}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 dark:text-blue-400 hover:underline text-xs truncate max-w-[120px]"
                        >
                          {lead.email_decydent}
                        </a>
                      </div>
                      <div className="flex items-center gap-2">
                        <ActionButton
                          icon={Phone}
                          tooltip={`Zadzwoń: ${lead.telefon}`}
                          onClick={() => (window.location.href = `tel:${lead.telefon}`)}
                        />
                        <ActionButton
                          icon={Mail}
                          tooltip={`Email: ${lead.email}`}
                          onClick={() => (window.location.href = `mailto:${lead.email}`)}
                        />
                        {lead.www && (
                          <ActionButton
                            icon={ExternalLink}
                            tooltip={`Strona WWW: ${lead.www}`}
                            onClick={() => window.open(lead.www, "_blank", "noopener,noreferrer")}
                          />
                        )}
                      </div>
                    </div>
                  </td>

                  {/* 11. Socials */}
                  <td className="p-3 border-r border-gray-100 dark:border-border/50">
                    <div className="flex gap-1">
                      {lead.linkedin && (
                        <ActionButton
                          icon={LinkedinIcon}
                          tooltip="LinkedIn"
                          onClick={() => window.open(lead.linkedin, "_blank", "noopener,noreferrer")}
                        />
                      )}
                      {lead.facebook && (
                        <ActionButton
                          icon={FacebookIcon}
                          tooltip="Facebook"
                          onClick={() => window.open(lead.facebook, "_blank", "noopener,noreferrer")}
                        />
                      )}
                      {lead.instagram && (
                        <ActionButton
                          icon={InstagramIcon}
                          tooltip="Instagram"
                          onClick={() => window.open(lead.instagram, "_blank", "noopener,noreferrer")}
                        />
                      )}
                      {lead.tiktok && (
                        <ActionButton
                          icon={TikTokIcon}
                          tooltip="TikTok"
                          onClick={() => window.open(lead.tiktok, "_blank", "noopener,noreferrer")}
                        />
                      )}
                    </div>
                  </td>

                  {/* 12. Date */}
                  <td className="p-3 text-gray-500 dark:text-muted-foreground text-xs tabular-nums">
                    {lead.data_weryfikacji}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="p-4 border-t border-gray-200 dark:border-border bg-gray-50 dark:bg-muted/20 flex justify-between items-center text-xs text-gray-500 dark:text-muted-foreground">
          <span>Pokazano 1-{filteredLeads.length} z {leads.length} wyników</span>
          <div className="flex gap-2">
            <button className="px-3 py-1 border border-gray-300 dark:border-border rounded bg-white dark:bg-card disabled:opacity-50" disabled>
              Poprzednia
            </button>
            <button className="px-3 py-1 border border-gray-300 dark:border-border rounded bg-white dark:bg-card hover:bg-gray-50 dark:hover:bg-muted">
              Następna
            </button>
          </div>
        </div>
      </div>

      {/* --- Interactive Video Demo Modal --- */}
      <Dialog
        open={Boolean(selectedVideoLead)}
        onOpenChange={(open) => !open && setSelectedVideoLead(null)}
      >
        <DialogContent className="max-w-3xl p-0 overflow-hidden bg-zinc-950 border-zinc-800 text-zinc-100">
          {selectedVideoLead && (
            <div>
              <DialogHeader className="p-4 bg-zinc-900/80 border-b border-zinc-800/80">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 text-[10px] font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30 rounded">
                        {selectedVideoLead.id_unikalne}
                      </span>
                      <span className="text-xs text-zinc-400 font-mono">
                        {selectedVideoLead.kraj} · {selectedVideoLead.tier}
                      </span>
                    </div>
                    <DialogTitle className="text-lg font-bold text-white">
                      {selectedVideoLead.video_demo_title}
                    </DialogTitle>
                    <DialogDescription className="text-xs text-zinc-400">
                      {selectedVideoLead.nazwa_firmy} — {selectedVideoLead.video_demo_desc}
                    </DialogDescription>
                  </div>
                </div>
              </DialogHeader>

              {/* Simulated Video Player Screen */}
              <div className="relative aspect-video bg-gradient-to-br from-zinc-900 via-zinc-950 to-black flex items-center justify-center border-b border-zinc-800 overflow-hidden group/player">
                {/* Visual Ambient Glow */}
                <div className="absolute inset-0 bg-radial-gradient from-rose-500/10 via-transparent to-transparent pointer-events-none" />

                {/* Animated Graphic Center */}
                <div className="text-center space-y-3 z-10">
                  <div className="relative inline-flex items-center justify-center">
                    <div className={`absolute -inset-4 bg-rose-500/20 rounded-full blur-xl ${isPlaying ? "animate-pulse" : ""}`} />
                    <button
                      onClick={() => setIsPlaying(!isPlaying)}
                      className="relative h-16 w-16 rounded-full bg-rose-600 hover:bg-rose-500 text-white flex items-center justify-center shadow-lg shadow-rose-600/40 transition-transform hover:scale-105 active:scale-95"
                    >
                      {isPlaying ? <Pause className="h-7 w-7" /> : <Play className="h-7 w-7 ml-1 fill-current" />}
                    </button>
                  </div>
                  <div className="space-y-1">
                    <p className="text-sm font-semibold text-white">
                      {isPlaying ? "Odtwarzanie demonstracji live..." : "Wstrzymano"}
                    </p>
                    <p className="text-xs text-zinc-400 font-mono">
                      1080p 60fps · Auto-Feed Sensor Active
                    </p>
                  </div>
                </div>

                {/* Bottom Video Controls Overlay */}
                <div className="absolute bottom-0 left-0 right-0 p-3 bg-gradient-to-t from-black/90 via-black/50 to-transparent flex flex-col gap-2">
                  {/* Progress bar */}
                  <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden cursor-pointer">
                    <div
                      className={`h-full bg-gradient-to-r from-rose-500 to-amber-500 ${isPlaying ? "w-2/3 animate-pulse" : "w-1/3"}`}
                    />
                  </div>
                  <div className="flex items-center justify-between text-xs text-zinc-400">
                    <div className="flex items-center gap-3">
                      <button onClick={() => setIsPlaying(!isPlaying)} className="hover:text-white">
                        {isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                      </button>
                      <Volume2 className="h-4 w-4" />
                      <span className="font-mono text-[11px]">01:14 / {selectedVideoLead.video_demo_duration}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="px-1.5 py-0.5 rounded bg-zinc-800 text-[10px] font-bold text-zinc-300">HD</span>
                      <Maximize2 className="h-4 w-4 hover:text-white cursor-pointer" />
                    </div>
                  </div>
                </div>
              </div>

              {/* Technical Details Footer */}
              <div className="p-4 bg-zinc-900/50 space-y-3">
                <div className="text-xs font-semibold text-zinc-300">Specyfikacja techniczna i parametry testu:</div>
                <div className="grid grid-cols-2 gap-2">
                  {selectedVideoLead.video_demo_specs?.map((spec, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-xs text-zinc-300 bg-zinc-800/60 px-2.5 py-1.5 rounded border border-zinc-700/50">
                      <Check className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                      <span>{spec}</span>
                    </div>
                  ))}
                </div>
                <div className="flex items-center justify-between pt-2 border-t border-zinc-800">
                  <div className="text-xs text-zinc-400">
                    Decydent: <span className="text-zinc-200 font-medium">{selectedVideoLead.decydent}</span> ({selectedVideoLead.telefon})
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        window.open(`mailto:${selectedVideoLead.email_decydent}?subject=B2B Inquiry: ${selectedVideoLead.video_demo_title}`, "_blank");
                      }}
                      className="px-3 py-1.5 text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white rounded shadow transition-colors"
                    >
                      Skontaktuj się w sprawie maszyn
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default ExperimentView;
