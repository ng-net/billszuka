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
  Linkedin,
  Facebook,
  Instagram,
  Video,
  Sparkles,
  Download,
} from "lucide-react";
import { toast } from "sonner";

// --- Mock Data Generator (for demonstration fallback) ---
const generateLeads = (count) =>
  Array.from({ length: count }, (_, i) => ({
    id_unikalne: `LEAD-${1000 + i}`,
    nazwa_firmy: `Firma Handlowa ${i + 1} Sp. z o.o.`,
    kraj: i % 3 === 0 ? "Polska" : i % 3 === 1 ? "Czechy" : "Słowacja",
    miasto: i % 2 === 0 ? "Warszawa" : "Praga",
    adres: `ul. Przemysłowa ${i}, 00-001 ${i % 2 === 0 ? "Warszawa" : "Praga"}`,
    www: "https://example.com",
    wolumen: i % 4 === 0 ? "Duży" : i % 4 === 1 ? "Średni" : "Mały",
    confidence_wolumen: "85%",
    rejestr_id: `KRS 0000${100000 + i}`,
    nip_vat: `PL${1000000000 + i}`,
    rok_zalozenia: 2010 + (i % 10),
    tier: i % 5 === 0 ? "Producent" : i % 5 === 1 ? "Hurtownik" : "Detalista",
    marki_nabijarki: i % 3 === 0 ? "PowerMatic, Hawk" : "Brak danych",
    marka_wlasna_oem: i % 2 === 0 ? "Tak" : "Nie",
    powinowactwo_nabijarki: i % 3 === 0 ? "Wysoki" : "Niski",
    cross_sell_potential: i % 4 === 0 ? "High" : "Low",
    kategoria: "A1",
    rynek_skala: "Lokalny",
    kanal_sprzedaży: "Stacjonarny + Online",
    decydent: "Jan Kowalski",
    stanowisko: "Prezes Zarządu",
    email_decydent: `jan.k${i}@firma.pl`,
    email: `biuro@firma${i}.pl`,
    telefon: `+48 500 000 ${10 + i}`,
    notatki: "Klient zainteresowany maszynami automatycznymi.",
    linkedin: "https://linkedin.com",
    facebook: "https://facebook.com",
    instagram: "https://instagram.com",
    tiktok: "https://tiktok.com",
    data_weryfikacji: "2023-10-25",
    sourcing: "Cold Call",
    zrodlo_danych: "KRS Online",
    flagi: ["Verified"],
    related_to: null,
  }));

export function ExperimentView() {
  const [leads] = useState(() => generateLeads(50));
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCountryFilters, setActiveCountryFilters] = useState([]);
  const [countryFilterOpen, setCountryFilterOpen] = useState(false);
  const [tierFilter, setTierFilter] = useState(null);
  const [volumeFilter, setVolumeFilter] = useState(null);

  // --- Filtering ---
  const filteredLeads = useMemo(() => {
    return leads.filter((lead) => {
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
    <div className="p-4 space-y-4 max-w-full">
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

          {/* --- QUICK CHIPS & POPOVER AREA --- */}
          <div className="flex flex-wrap items-center gap-2">
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
                    <div className="font-semibold text-gray-900 dark:text-foreground truncate max-w-[220px]" title={lead.nazwa_firmy}>
                      {lead.nazwa_firmy}
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
                          icon={Linkedin}
                          tooltip="LinkedIn"
                          onClick={() => window.open(lead.linkedin, "_blank", "noopener,noreferrer")}
                        />
                      )}
                      {lead.facebook && (
                        <ActionButton
                          icon={Facebook}
                          tooltip="Facebook"
                          onClick={() => window.open(lead.facebook, "_blank", "noopener,noreferrer")}
                        />
                      )}
                      {lead.instagram && (
                        <ActionButton
                          icon={Instagram}
                          tooltip="Instagram"
                          onClick={() => window.open(lead.instagram, "_blank", "noopener,noreferrer")}
                        />
                      )}
                      {lead.tiktok && (
                        <ActionButton
                          icon={Video}
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
    </div>
  );
}

export default ExperimentView;
