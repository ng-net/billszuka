import React, { useMemo, useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Compass,
  Zap,
  Globe2,
  ShieldCheck,
  Building2,
  TrendingUp,
  MapPin,
  Mail,
  Phone,
  ExternalLink,
  Copy,
  ChevronDown,
  ChevronRight,
  Filter,
  Sparkles,
  Terminal,
  Activity,
  Layers,
  Database,
  ArrowUpRight,
  CheckCircle2,
} from "lucide-react";
import { useCsv } from "@/hooks/useCsv";
import { useUrlStatus } from "@/hooks/useUrlStatus";
import { useKeywordScan } from "@/hooks/useKeywordScan";
import { toast } from "sonner";

const MASTER_URL = "/api/master.csv";
const withCacheBuster = (url) => `${url}?v=${Date.now()}`;

function fmtDate(val) {
  if (!val) return "—";
  if (val instanceof Date) {
    if (isNaN(val.getTime())) return "—";
    return val.toISOString().slice(0, 10);
  }
  const s = String(val).trim();
  return s.length >= 10 ? s.slice(0, 10) : s || "—";
}

function maskName(str) {
  if (!str) return "—";
  const parts = str.trim().split(/\s+/);
  if (parts.length === 1) return parts[0];
  const first = parts[0];
  const lastInitial = parts[parts.length - 1][0] + ".";
  return `${first} ${lastInitial}`;
}

export function AtlasGrokView() {
  const csv = useCsv();
  const { status, loadUrl } = csv;
  const [search, setSearch] = useState("");
  const [selectedCountry, setSelectedCountry] = useState("ALL");
  const [selectedBrand, setSelectedBrand] = useState("ALL");
  const [selectedTier, setSelectedTier] = useState("ALL");
  const [selectedLeadId, setSelectedLeadId] = useState(null);
  const [maskRODO, setMaskRODO] = useState(true);
  const [viewMode, setViewMode] = useState("grid"); // 'grid' | 'stream'

  // Fetch URL and Keyword statuses for live radar telemetry
  const { byId: urlStatusById = {} } = useUrlStatus(null);
  const { byId: keywordById = {} } = useKeywordScan(null);

  useEffect(() => {
    if (status === "idle") {
      loadUrl(withCacheBuster(MASTER_URL), "master.csv", 0);
    } else if (status === "error") {
      loadUrl(withCacheBuster("/master.csv"), "master.csv", 0);
    }
  }, [status, loadUrl]);

  const leads = useMemo(() => csv.rows || [], [csv.rows]);

  // Telemetry Aggregates
  const stats = useMemo(() => {
    const total = leads.length;
    let verified = 0;
    let powermaticCount = 0;
    let highVol = 0;
    const countries = new Set();

    for (const l of leads) {
      if (l.kraj) countries.add(l.kraj.trim());
      if (l.flagi?.includes("Verified")) verified++;
      const brand = (l.marki_nabijarki || "").toLowerCase();
      if (brand.includes("powermatic") || brand.includes("hawk")) powermaticCount++;
      const vol = (l.wolumen || "").toLowerCase();
      if (vol.includes("duż") || vol.includes("wysoki") || vol.includes("high")) highVol++;
    }

    return {
      total,
      verified,
      powermaticCount,
      highVol,
      countryCount: countries.size,
    };
  }, [leads]);

  // Country facets
  const countryList = useMemo(() => {
    const map = new Map();
    for (const l of leads) {
      if (!l.kraj) continue;
      const k = l.kraj.trim();
      map.set(k, (map.get(k) || 0) + 1);
    }
    return Array.from(map.entries()).sort((a, b) => b[1] - a[1]);
  }, [leads]);

  // Filter pipeline
  const filtered = useMemo(() => {
    return leads.filter((l) => {
      if (selectedCountry !== "ALL" && l.kraj !== selectedCountry) return false;
      if (selectedBrand !== "ALL") {
        const b = (l.marki_nabijarki || "").toLowerCase();
        if (selectedBrand === "PowerMatic" && !b.includes("powermatic")) return false;
        if (selectedBrand === "Hawk" && !b.includes("hawk")) return false;
      }
      if (selectedTier !== "ALL" && l.tier !== selectedTier) return false;

      if (search.trim()) {
        const q = search.toLowerCase();
        const match =
          (l.nazwa || "").toLowerCase().includes(q) ||
          (l.miasto || "").toLowerCase().includes(q) ||
          (l.nip_vat || "").toLowerCase().includes(q) ||
          (l.decydent || "").toLowerCase().includes(q) ||
          (l.notatki || "").toLowerCase().includes(q);
        if (!match) return false;
      }
      return true;
    });
  }, [leads, selectedCountry, selectedBrand, selectedTier, search]);

  const activeLead = useMemo(() => {
    if (!selectedLeadId) return filtered[0] || null;
    return leads.find((l) => l.id === selectedLeadId) || filtered[0] || null;
  }, [leads, selectedLeadId, filtered]);

  const copyToClipboard = (text, label) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    toast.success(`Skopiowano ${label}: ${text}`);
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-background text-foreground font-sans antialiased">
      {/* Main Container */}
      <div className="max-w-[1700px] mx-auto p-4 md:p-6 space-y-6">
        {/* Top Atlas HUD Header */}
        <header className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-5 rounded-2xl bg-card border border-border shadow-sm relative overflow-hidden text-card-foreground">
          <div className="flex items-center gap-4 relative z-10">
            <div className="h-12 w-12 rounded-xl bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-sm">
              <Compass className="h-6 w-6 animate-[spin_12s_linear_infinite]" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="text-xl font-black tracking-tight text-foreground flex items-center gap-1.5">
                  ATLAS <span className="text-primary">GROK</span>
                </h1>
                <span className="px-2 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 text-[10px] font-mono tracking-widest uppercase font-semibold">
                  Telemetry v2.2
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5 flex items-center gap-2">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Global B2B Market Intelligence &amp; Lead Vector Engine
              </p>
            </div>
          </div>

          {/* Quick HUD Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 relative z-10 font-mono">
            <div className="px-3.5 py-2 rounded-xl bg-muted/40 border border-border">
              <div className="text-[10px] uppercase text-muted-foreground tracking-wider font-semibold">Total Targets</div>
              <div className="text-lg font-bold text-foreground flex items-center gap-1.5 tabular-nums mt-0.5">
                {stats.total}
                <Database size={13} className="text-primary" />
              </div>
            </div>
            <div className="px-3.5 py-2 rounded-xl bg-muted/40 border border-border">
              <div className="text-[10px] uppercase text-muted-foreground tracking-wider font-semibold">Active Markets</div>
              <div className="text-lg font-bold text-foreground flex items-center gap-1.5 tabular-nums mt-0.5">
                {stats.countryCount}
                <Globe2 size={13} className="text-sky-500" />
              </div>
            </div>
            <div className="px-3.5 py-2 rounded-xl bg-muted/40 border border-border">
              <div className="text-[10px] uppercase text-muted-foreground tracking-wider font-semibold">PM &amp; Hawk Affinity</div>
              <div className="text-lg font-bold text-amber-600 dark:text-amber-400 flex items-center gap-1.5 tabular-nums mt-0.5">
                {stats.powermaticCount}
                <Zap size={13} className="text-amber-500" />
              </div>
            </div>
            <div className="px-3.5 py-2 rounded-xl bg-muted/40 border border-border">
              <div className="text-[10px] uppercase text-muted-foreground tracking-wider font-semibold">High Volume Tier</div>
              <div className="text-lg font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5 tabular-nums mt-0.5">
                {stats.highVol}
                <TrendingUp size={13} className="text-emerald-500" />
              </div>
            </div>
          </div>
        </header>

        {/* Command & Control Filter Strip */}
        <section className="p-3.5 rounded-xl bg-card border border-border shadow-sm flex flex-wrap items-center justify-between gap-3 text-card-foreground">
          {/* Search Bar */}
          <div className="relative flex-1 min-w-[280px]">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Szybkie przeszukiwanie wektorów (Firma, NIP, Decydent, Notatki)..."
              className="w-full pl-10 pr-4 py-2 rounded-lg bg-muted/40 border border-input focus:border-primary/60 focus:ring-1 focus:ring-primary/40 text-xs text-foreground placeholder:text-muted-foreground transition-all outline-none"
            />
          </div>

          {/* Quick Filters */}
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {/* Country Selector */}
            <select
              value={selectedCountry}
              onChange={(e) => setSelectedCountry(e.target.value)}
              className="px-3 py-2 rounded-lg bg-card border border-border text-foreground text-xs focus:border-primary outline-none cursor-pointer shadow-sm"
            >
              <option value="ALL">🌍 Wszystkie Rynki ({leads.length})</option>
              {countryList.map(([k, cnt]) => (
                <option key={k} value={k}>
                  {k} ({cnt})
                </option>
              ))}
            </select>

            {/* Brand Filter */}
            <div className="flex bg-muted/50 p-1 rounded-lg border border-border">
              {["ALL", "PowerMatic", "Hawk"].map((b) => (
                <button
                  key={b}
                  onClick={() => setSelectedBrand(b)}
                  className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${
                    selectedBrand === b
                      ? "bg-card text-foreground font-semibold shadow-sm border border-border/60"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {b === "ALL" ? "Wszystkie Marki" : b}
                </button>
              ))}
            </div>

            {/* RODO Toggle */}
            <button
              onClick={() => setMaskRODO(!maskRODO)}
              className={`px-3 py-2 rounded-lg border transition-all flex items-center gap-1.5 text-xs font-medium shadow-sm ${
                maskRODO
                  ? "bg-card border-border text-muted-foreground hover:text-foreground"
                  : "bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400"
              }`}
            >
              <ShieldCheck size={14} />
              <span>RODO: {maskRODO ? "Maskuj" : "Odkryj"}</span>
            </button>
          </div>
        </section>

        {/* Dynamic Split Layout: Lead Stream & Inspector */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Interactive Radar Grid (7 cols) */}
          <div className="lg:col-span-7 space-y-3">
            <div className="flex items-center justify-between text-xs text-muted-foreground px-1 font-mono">
              <span>Zlokalizowano: {filtered.length} podmiotów</span>
              <span className="text-primary font-medium">Kliknij rekord, aby dokonać inspekcji</span>
            </div>

            <div className="space-y-2.5 max-h-[750px] overflow-y-auto pr-1 custom-scrollbar">
              {filtered.map((lead) => {
                const isSelected = activeLead?.id === lead.id;
                const urlTelemetry = urlStatusById[lead.id];
                const keywordData = keywordById[lead.id];

                return (
                  <motion.div
                    key={lead.id}
                    onClick={() => setSelectedLeadId(lead.id)}
                    whileHover={{ scale: 1.006 }}
                    transition={{ duration: 0.15 }}
                    className={`p-4 rounded-xl border transition-all cursor-pointer relative overflow-hidden ${
                      isSelected
                        ? "bg-primary/5 border-primary shadow-sm"
                        : "bg-card border-border hover:border-border hover:bg-muted/30 shadow-sm"
                    }`}
                  >
                    {/* Left Active Indicator Strip */}
                    {isSelected && (
                      <div className="absolute left-0 top-0 bottom-0 w-1 bg-primary" />
                    )}

                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="px-1.5 py-0.5 rounded bg-muted text-muted-foreground font-mono text-[10px] border border-border">
                            {lead.kraj || "EU"}
                          </span>
                          <h3 className="text-sm font-bold text-foreground truncate group-hover:text-primary">
                            {lead.nazwa}
                          </h3>
                          {lead.flagi?.includes("Verified") && (
                            <span className="flex items-center gap-0.5 text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold font-mono">
                              <ShieldCheck size={11} /> VERIFIED
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground flex-wrap">
                          <span className="flex items-center gap-1">
                            <MapPin size={12} className="text-muted-foreground/70" />
                            {lead.miasto || "—"}
                          </span>
                          <span className="text-muted-foreground/40">•</span>
                          <span className="font-mono text-foreground">NIP: {lead.nip_vat || "—"}</span>
                          <span className="text-muted-foreground/40">•</span>
                          <span className="text-primary font-medium">{lead.tier || "Dystrybutor"}</span>
                        </div>
                      </div>

                      {/* Right Telemetry Pill */}
                      <div className="flex flex-col items-end gap-1 shrink-0 font-mono">
                        <span className="px-2 py-0.5 rounded-full text-[10px] bg-muted text-muted-foreground border border-border">
                          {lead.wolumen || "Średni"}
                        </span>
                        {urlTelemetry?.status === "ok" ? (
                          <span className="text-[10px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1 font-medium">
                            <CheckCircle2 size={10} /> DOMENA OK
                          </span>
                        ) : (
                          <span className="text-[10px] text-muted-foreground/60">DNS UNVERIFIED</span>
                        )}
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>

          {/* Right Column: Deep Intel Inspector (5 cols) */}
          <div className="lg:col-span-5 sticky top-20">
            {activeLead ? (
              <div className="rounded-2xl bg-card border border-border p-5 shadow-sm space-y-5 text-card-foreground">
                {/* Header Profile */}
                <div className="flex items-start justify-between gap-3 border-b border-border pb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded-md bg-primary/10 text-primary border border-primary/20 font-mono text-[10px] font-bold">
                        {activeLead.id}
                      </span>
                      <span className="px-2 py-0.5 rounded-md bg-muted text-muted-foreground font-mono text-[10px] border border-border">
                        {activeLead.kraj}
                      </span>
                    </div>
                    <h2 className="text-lg font-bold text-foreground mt-1.5 leading-snug">
                      {activeLead.nazwa}
                    </h2>
                    <p className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
                      <MapPin size={12} className="text-primary" />
                      {activeLead.adres || `${activeLead.miasto}, ${activeLead.kraj}`}
                    </p>
                  </div>

                  {activeLead.www && (
                    <a
                      href={activeLead.www.startsWith("http") ? activeLead.www : `https://${activeLead.www}`}
                      target="_blank"
                      rel="noreferrer"
                      className="p-2.5 rounded-xl bg-muted hover:bg-muted/80 text-foreground border border-border transition-all shadow-sm"
                      title="Otwórz stronę WWW"
                    >
                      <ArrowUpRight size={16} />
                    </a>
                  )}
                </div>

                {/* Key Legal Registry */}
                <div className="grid grid-cols-2 gap-2.5 font-mono text-xs">
                  <div className="p-3 rounded-xl bg-muted/40 border border-border">
                    <div className="text-[10px] uppercase text-muted-foreground font-semibold">NIP / VAT ID</div>
                    <div className="text-foreground font-bold mt-0.5 truncate">{activeLead.nip_vat || "Brak"}</div>
                    {activeLead.nip_vat && (
                      <button
                        onClick={() => copyToClipboard(activeLead.nip_vat, "NIP")}
                        className="text-[10px] text-primary hover:underline flex items-center gap-1 mt-1 font-sans font-medium"
                      >
                        <Copy size={10} /> Kopiuj NIP
                      </button>
                    )}
                  </div>
                  <div className="p-3 rounded-xl bg-muted/40 border border-border">
                    <div className="text-[10px] uppercase text-muted-foreground font-semibold">KRS / Rejestr</div>
                    <div className="text-foreground font-bold mt-0.5 truncate">{activeLead.rejestr_id || "Brak"}</div>
                    {activeLead.rejestr_id && (
                      <button
                        onClick={() => copyToClipboard(activeLead.rejestr_id, "KRS")}
                        className="text-[10px] text-primary hover:underline flex items-center gap-1 mt-1 font-sans font-medium"
                      >
                        <Copy size={10} /> Kopiuj KRS
                      </button>
                    )}
                  </div>
                </div>

                {/* Decision Maker & Channels */}
                <div className="p-4 rounded-xl bg-muted/30 border border-border space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="text-xs uppercase tracking-wider text-muted-foreground font-semibold flex items-center gap-1.5">
                      <Sparkles size={13} className="text-primary" />
                      <span>Decydent &amp; Kanały</span>
                    </div>
                  </div>

                  <div>
                    <div className="text-sm font-bold text-foreground">
                      {maskRODO ? maskName(activeLead.decydent) : (activeLead.decydent || "Brak danych decydenta")}
                    </div>
                    <div className="text-xs text-muted-foreground">{activeLead.stanowisko || "Zarząd / Właściciel"}</div>
                  </div>

                  <div className="space-y-1.5 pt-2 border-t border-border">
                    {activeLead.telefon && (
                      <a
                        href={`tel:${activeLead.telefon}`}
                        className="flex items-center justify-between p-2 rounded-lg bg-card hover:bg-emerald-500/10 text-xs text-foreground hover:text-emerald-600 dark:hover:text-emerald-400 border border-border transition-colors group"
                      >
                        <div className="flex items-center gap-2">
                          <Phone size={13} className="text-emerald-500" />
                          <span className="font-mono">{activeLead.telefon}</span>
                        </div>
                        <span className="text-[10px] text-muted-foreground group-hover:text-emerald-600 font-mono">Zadzwoń ↗</span>
                      </a>
                    )}
                    {activeLead.email && (
                      <a
                        href={`mailto:${activeLead.email}`}
                        className="flex items-center justify-between p-2 rounded-lg bg-card hover:bg-sky-500/10 text-xs text-foreground hover:text-sky-600 dark:hover:text-sky-400 border border-border transition-colors group"
                      >
                        <div className="flex items-center gap-2 truncate">
                          <Mail size={13} className="text-sky-500 shrink-0" />
                          <span className="truncate">{activeLead.email}</span>
                        </div>
                        <span className="text-[10px] text-muted-foreground group-hover:text-sky-600 font-mono shrink-0 ml-1">E-mail ↗</span>
                      </a>
                    )}
                  </div>
                </div>

                {/* Analytical Notes */}
                <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20 space-y-2">
                  <div className="text-xs uppercase tracking-wider text-amber-600 dark:text-amber-400 font-semibold flex items-center gap-1.5">
                    <Activity size={13} />
                    <span>Notatki Strategiczne &amp; Intel</span>
                  </div>
                  <p className="text-xs text-foreground/90 leading-relaxed font-sans">
                    {activeLead.notatki || "Brak dodatkowych notatek analitycznych."}
                  </p>
                  <div className="pt-2 border-t border-amber-500/20 flex items-center justify-between text-[10px] font-mono text-muted-foreground">
                    <span>Źródło: {activeLead.zrodlo_danych || "Rejestry publiczne"}</span>
                    <span>Weryfikacja: {fmtDate(activeLead.data_weryfikacji)}</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-12 text-center rounded-2xl bg-card border border-border text-muted-foreground font-mono text-xs">
                Wybierz podmiot z radaru, aby dokonać pełnej analizy wektorowej.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
