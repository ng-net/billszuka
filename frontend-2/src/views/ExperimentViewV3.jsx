import React, { useMemo, useState } from "react";
import {
  Search,
  Sparkles,
  ChevronRight,
  Sun,
  Moon,
  LayoutGrid,
  X,
  Download,
} from "lucide-react";

const FACET_DEFS = [
  { key: "kraj", label: "Kraj" },
  { key: "tier", label: "Tier" },
  { key: "wolumen", label: "Wolumen" },
  { key: "marki_nabijarki", label: "Marka" },
  { key: "cross_sell_potential", label: "Cross-sell" },
];

function uniqValues(rows, key) {
  const counts = new Map();
  for (const r of rows) {
    const v = (r[key] || "").toString().trim();
    if (!v) continue;
    counts.set(v, (counts.get(v) || 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1]);
}

function splitBrands(s) {
  if (!s) return [];
  return s.split(/[,;|]/).map((b) => b.trim()).filter(Boolean);
}

export function ExperimentViewV3({ leads = [] }) {
  const [search, setSearch] = useState("");
  const [activeFilters, setActiveFilters] = useState({});
  const [activeBrand, setActiveBrand] = useState(null);
  const [density, setDensity] = useState("cozy");
  const [theme, setTheme] = useState("light");
  const [openSections, setOpenSections] = useState({
    kraj: true,
    tier: true,
    wolumen: false,
    marki_nabijarki: false,
    cross_sell_potential: false,
  });

  const toggleFilter = (key, value) => {
    setActiveFilters((prev) => {
      const current = prev[key];
      if (!current) return { ...prev, [key]: [value] };
      if (current.includes(value)) {
        const next = current.filter((v) => v !== value);
        const { [key]: _, ...rest } = prev;
        return next.length ? { ...prev, [key]: next } : rest;
      }
      return { ...prev, [key]: [...current, value] };
    });
  };

  const clearAll = () => {
    setActiveFilters({});
    setActiveBrand(null);
  };

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return leads.filter((r) => {
      if (q) {
        const hay =
          (r.nazwa_firmy || "") + " " + (r.miasto || "") + " " + (r.nip_vat || "");
        if (!hay.toLowerCase().includes(q)) return false;
      }
      if (activeBrand === "PowerMatic" && !/powermatic/i.test(r.marki_nabijarki || "")) return false;
      if (activeBrand === "Hawk" && !/\bhawk\b/i.test(r.marki_nabijarki || "")) return false;
      for (const [key, vals] of Object.entries(activeFilters)) {
        const v = (r[key] || "").toString();
        if (!vals.includes(v)) return false;
      }
      return true;
    });
  }, [leads, search, activeFilters, activeBrand]);

  const rowH = density === "compact" ? "38px" : density === "cozy" ? "48px" : "56px";

  return (
    <div
      data-theme={theme}
      data-density={density}
      className="flex h-full w-full font-sans text-[13px] bg-slate-50 text-slate-900"
    >
      {/* ───── LEFT FILTER RAIL ───── */}
      <aside className="w-[274px] shrink-0 bg-white border-r border-slate-200 flex flex-col">
        <div className="px-4 py-4 flex items-center gap-2.5 border-b border-slate-100">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 text-white grid place-items-center font-bold text-[13px] shadow-sm">
            B
          </div>
          <div className="leading-tight">
            <div className="font-semibold text-[14px]">BILLSzuka · v3</div>
            <div className="text-[11px] text-slate-500">Compact · Faceted</div>
          </div>
        </div>

        <div className="px-2 py-2">
          {[
            { label: "Wszystko", count: leads.length, on: Object.keys(activeFilters).length === 0 && !activeBrand, action: clearAll },
            { label: "PowerMatic", count: leads.filter((r) => /powermatic/i.test(r.marki_nabijarki || "")).length, on: activeBrand === "PowerMatic", action: () => setActiveBrand((p) => p === "PowerMatic" ? null : "PowerMatic") },
            { label: "Hawk", count: leads.filter((r) => /\bhawk\b/i.test(r.marki_nabijarki || "")).length, on: activeBrand === "Hawk", action: () => setActiveBrand((p) => p === "Hawk" ? null : "Hawk") },
          ].map((v) => (
            <button
              key={v.label}
              onClick={v.action}
              className={
                "w-full flex items-center gap-2 px-2.5 py-1.5 rounded-md text-[13px] " +
                (v.on ? "bg-slate-100 font-semibold text-slate-900" : "text-slate-600 hover:bg-slate-100")
              }
            >
              <LayoutGrid size={14} className="text-slate-400" />
              {v.label}
              <span className="ml-auto text-[11px] font-mono tabular-nums text-slate-500 bg-slate-100 px-1.5 rounded-full">
                {v.count}
              </span>
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto px-2 pb-6">
          {FACET_DEFS.map((facet) => {
            const values = uniqValues(filtered, facet.key);
            const isOpen = openSections[facet.key];
            const active = activeFilters[facet.key] || [];
            return (
              <div key={facet.key} className={"border-t border-slate-100 " + (isOpen ? "" : "")}>
                <button
                  onClick={() => setOpenSections((p) => ({ ...p, [facet.key]: !p[facet.key] }))}
                  className="w-full flex items-center gap-2 px-2 py-2 text-[10.5px] font-bold uppercase tracking-wider text-slate-500 hover:text-slate-700"
                >
                  <ChevronRight
                    size={10}
                    className={"transition-transform " + (isOpen ? "rotate-90" : "")}
                  />
                  {facet.label}
                  {active.length > 0 && (
                    <span className="ml-auto bg-indigo-600 text-white text-[10px] font-bold px-1.5 rounded-full">
                      {active.length}
                    </span>
                  )}
                </button>
                {isOpen && (
                  <div className="px-2 pb-2 space-y-0.5">
                    {values.map(([val, count]) => (
                      <label
                        key={val}
                        className="flex items-center gap-2 px-1.5 py-1 rounded hover:bg-slate-100 cursor-pointer text-[12.5px]"
                      >
                        <input
                          type="checkbox"
                          checked={active.includes(val)}
                          onChange={() => toggleFilter(facet.key, val)}
                          className="w-3.5 h-3.5 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                        />
                        <span className="flex-1 truncate text-slate-700">{val}</span>
                        <span className="ml-2 w-7 h-1 bg-slate-200 rounded-full overflow-hidden">
                          <span
                            className="block h-full bg-indigo-500"
                            style={{ width: Math.min(100, (count / values[0][1]) * 100) + "%" }}
                          />
                        </span>
                        <span className="ml-1.5 text-[11px] font-mono tabular-nums text-slate-400 w-6 text-right">
                          {count}
                        </span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="border-t border-slate-100 p-2 flex items-center gap-1 text-[11px]">
          <button
            onClick={() => setDensity("compact")}
            className={"px-2 py-1 rounded " + (density === "compact" ? "bg-slate-200 font-semibold" : "hover:bg-slate-100")}
          >
            Compact
          </button>
          <button
            onClick={() => setDensity("cozy")}
            className={"px-2 py-1 rounded " + (density === "cozy" ? "bg-slate-200 font-semibold" : "hover:bg-slate-100")}
          >
            Cozy
          </button>
          <button
            onClick={() => setDensity("comfy")}
            className={"px-2 py-1 rounded " + (density === "comfy" ? "bg-slate-200 font-semibold" : "hover:bg-slate-100")}
          >
            Comfy
          </button>
          <div className="flex-1" />
          <button
            onClick={() => setTheme(theme === "light" ? "dark" : "light")}
            className="p-1.5 rounded hover:bg-slate-100"
            title="Toggle theme"
          >
            {theme === "light" ? <Moon size={14} /> : <Sun size={14} />}
          </button>
        </div>
      </aside>

      {/* ───── MAIN TABLE ───── */}
      <main className="flex-1 min-w-0 flex flex-col bg-white">
        <div className="flex items-center gap-2 px-4 py-2.5 border-b border-slate-200">
          <div className="relative flex-1 max-w-[420px]">
            <Search
              size={14}
              className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
            />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Szukaj po nazwie, NIP, mieście…"
              className="w-full h-8 pl-8 pr-16 text-[13px] bg-slate-50 border border-transparent rounded-md outline-none focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            />
            <kbd className="absolute right-2 top-1.5 text-[10px] font-mono font-semibold text-slate-400 bg-white border border-slate-200 px-1.5 rounded">
              /
            </kbd>
          </div>

          <div className="flex-1" />

          <span className="text-[12px] text-slate-600">
            <b className="text-slate-900 font-semibold">{filtered.length}</b> wyników
            <span className="text-slate-400"> z {leads.length}</span>
          </span>

          <button className="inline-flex items-center gap-1.5 h-8 px-2.5 rounded-md border border-slate-200 bg-white text-[12px] font-medium text-slate-700 hover:bg-slate-50">
            <LayoutGrid size={13} /> Kolumny
          </button>
          <button className="inline-flex items-center gap-1.5 h-8 px-2.5 rounded-md bg-indigo-600 text-white text-[12px] font-medium hover:bg-indigo-700">
            <Download size={13} /> Eksport
          </button>
        </div>

        {/* Active filter pills */}
        {Object.entries(activeFilters).flatMap(([k, vs]) => vs.map((v) => ({ k, v }))).length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 px-4 py-2 border-b border-slate-200 bg-slate-50">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Aktywne:
            </span>
            {Object.entries(activeFilters).flatMap(([k, vs]) =>
              vs.map((v) => (
                <span
                  key={k + v}
                  className="inline-flex items-center gap-1 h-6 px-2 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-full text-[11.5px] font-medium"
                >
                  <span className="opacity-60">{k}:</span>
                  <span className="font-semibold">{v}</span>
                  <button
                    onClick={() => toggleFilter(k, v)}
                    className="ml-0.5 w-4 h-4 rounded-full grid place-items-center hover:bg-indigo-200"
                  >
                    <X size={9} />
                  </button>
                </span>
              ))
            )}
            <button
              onClick={clearAll}
              className="text-[11px] text-rose-600 hover:underline ml-1.5"
            >
              Resetuj
            </button>
          </div>
        )}

        {/* Table */}
        <div className="flex-1 overflow-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-[10.5px] uppercase tracking-wider text-slate-500 font-bold">
                <th className="sticky left-0 z-20 bg-slate-50 w-11 h-9 px-3 border-r border-slate-200 text-center">
                  <input type="checkbox" className="w-3.5 h-3.5 rounded border-slate-300" />
                </th>
                <th className="sticky left-11 z-20 bg-slate-50 min-w-[296px] h-9 px-3.5 text-left border-r border-slate-200">
                  Firma
                </th>
                <th className="h-9 px-3.5 text-left min-w-[140px]">Miasto</th>
                <th className="h-9 px-3.5 text-left min-w-[110px]">Kraj</th>
                <th className="h-9 px-3.5 text-left min-w-[140px]">Wolumen</th>
                <th className="h-9 px-3.5 text-left min-w-[110px]">Tier</th>
                <th className="h-9 px-3.5 text-left min-w-[200px]">Marki</th>
                <th className="h-9 px-3.5 text-left min-w-[150px]">Kontakt</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-16 text-slate-400">
                    Brak wyników dla wybranych filtrów
                  </td>
                </tr>
              ) : (
                filtered.map((r) => {
                  const init = (r.nazwa_firmy || "?").trim().charAt(0).toUpperCase();
                  return (
                    <tr
                      key={r.id_unikalne}
                      style={{ height: rowH }}
                      className="border-b border-slate-100 hover:bg-slate-50"
                    >
                      <td className="sticky left-0 z-10 bg-white group-hover:bg-slate-50 w-11 px-3 text-center border-r border-slate-200">
                        <input
                          type="checkbox"
                          className="w-3.5 h-3.5 rounded border-slate-300 text-indigo-600 opacity-0 group-hover:opacity-100"
                        />
                      </td>
                      <td className="sticky left-11 z-10 bg-white group-hover:bg-slate-50 px-3.5 border-r border-slate-200">
                        <div className="flex items-center gap-2.5 min-w-0">
                          <div className="w-7 h-7 rounded-md bg-gradient-to-br from-indigo-500 to-violet-500 text-white grid place-items-center text-[10.5px] font-bold flex-none">
                            {init}
                          </div>
                          <div className="min-w-0">
                            <div className="font-semibold text-slate-900 text-[13px] truncate">
                              {r.nazwa_firmy}
                            </div>
                            <div className="text-[11px] font-mono text-slate-400 truncate">
                              {r.id_unikalne} · {r.www?.replace(/^https?:\/\//, "")}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-3.5 text-slate-700">{r.miasto}</td>
                      <td className="px-3.5">
                        <span className="inline-flex items-center h-5 px-1.5 rounded bg-slate-100 text-slate-700 text-[11px] font-semibold">
                          {r.kraj}
                        </span>
                      </td>
                      <td className="px-3.5">
                        <div className="inline-flex items-center gap-1.5">
                          <span className="inline-flex gap-0.5">
                            {[1, 2, 3, 4, 5].map((i) => {
                              const filled =
                                r.wolumen === "duży" ? i <= 4 : r.wolumen === "średni" ? i <= 2 : i <= 1;
                              return (
                                <span
                                  key={i}
                                  className={
                                    "w-[5px] h-3 rounded-sm " +
                                    (filled ? "bg-emerald-500" : "bg-slate-200")
                                  }
                                />
                              );
                            })}
                          </span>
                          <span className="text-[12px] font-medium text-slate-700">{r.wolumen}</span>
                        </div>
                      </td>
                      <td className="px-3.5">
                        <span className="inline-flex items-center h-5 px-1.5 rounded bg-violet-50 text-violet-700 border border-violet-200 text-[11px] font-semibold">
                          {r.tier}
                        </span>
                      </td>
                      <td className="px-3.5">
                        <div className="flex flex-wrap gap-1">
                          {splitBrands(r.marki_nabijarki).map((b, i) => (
                            <span
                              key={i}
                              className="inline-flex items-center h-5 px-1.5 rounded bg-slate-100 text-slate-700 text-[11px] font-medium"
                            >
                              {b}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-3.5 text-slate-700">
                        <div className="text-[12px]">{r.decydent}</div>
                        <div className="text-[11px] font-mono text-slate-400 truncate">{r.email_decydent}</div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        <div className="px-4 py-2 border-t border-slate-200 text-[11px] text-slate-500 flex items-center gap-3">
          <Sparkles size={12} className="text-indigo-500" />
          <span>
            <b className="text-slate-700">v3 experiment</b> · 11 domyślnych kolumn · density {density} · theme {theme} · faceted counts
          </span>
          <div className="flex-1" />
          <span className="font-mono">↑↓ navigate · / search · x clear</span>
        </div>
      </main>
    </div>
  );
}

export default ExperimentViewV3;
