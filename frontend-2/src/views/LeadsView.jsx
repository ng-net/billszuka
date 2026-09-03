import React, { useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { Loader2, Building2, Flame, ShieldCheck, Globe } from "lucide-react";
import { useCsv } from "@/hooks/useCsv";
import { ModernLeadsTableV2 } from "./ModernLeadsTableV2";
import { Card, CardContent } from "@/components/ui/card";

const MASTER_URL = "/api/master.csv";
const withCacheBuster = (url) => `${url}?v=${Date.now()}`;

export function LeadsView() {
  const csv = useCsv();

  useEffect(() => {
    if (csv.status === "idle") {
      csv.loadUrl(withCacheBuster(MASTER_URL), "master.csv", 0);
    } else if (csv.status === "error") {
      // Standalone web hosting fallback (Vercel / GitHub Pages without Python FastAPI backend)
      csv.loadUrl(withCacheBuster("/master.csv"), "master.csv", 0);
    }
  }, [csv]);

  const leads = useMemo(() => {
    if (csv.rows && csv.rows.length > 0) {
      return csv.rows;
    }
    return undefined; // triggers demo data fallback in ModernLeadsTableV2 if empty
  }, [csv.rows]);

  // Compute live KPI metrics
  const kpis = useMemo(() => {
    const list = csv.rows || [];
    const total = list.length;
    let pmCount = 0;
    let verifiedCount = 0;
    let webOkCount = 0;

    for (const r of list) {
      const brands = (r.marki_nabijarki || "").toLowerCase();
      if (brands.includes("powermatic") || brands.includes("hawk")) {
        pmCount++;
      }
      const flagi = String(r.flagi || "");
      if (flagi.includes("FROZEN") || flagi.includes("Verified") || (r.nip_vat && r.nip_vat.length > 6)) {
        verifiedCount++;
      }
      const st = (r.www_status || "").toLowerCase();
      if (st.includes("green") || st.includes("200")) {
        webOkCount++;
      }
    }

    return {
      total,
      pmCount,
      verifiedCount,
      webOkCount,
      pmPct: total > 0 ? Math.round((pmCount / total) * 100) : 0,
      verifiedPct: total > 0 ? Math.round((verifiedCount / total) * 100) : 0,
    };
  }, [csv.rows]);

  if (csv.status === "loading") {
    return (
      <div className="flex h-[80vh] flex-col items-center justify-center gap-3 text-muted-foreground">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="text-sm font-medium">Ładowanie katalogu leadów B2B...</p>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="space-y-4 p-4 md:p-6"
    >
      {/* Top KPI Metric Cards */}
      <div className="max-w-[1600px] mx-auto grid grid-cols-2 sm:grid-cols-4 gap-3.5">
        <div className="relative overflow-hidden rounded-2xl bg-white/70 dark:bg-zinc-900/70 p-4 backdrop-blur-xl border border-slate-200/80 dark:border-zinc-800/80 shadow-[0_2px_8px_rgba(0,0,0,0.03)] hover:shadow-md hover:border-indigo-300/60 dark:hover:border-indigo-700/60 transition-all group">
          <div className="flex items-center gap-3.5">
            <div className="h-11 w-11 rounded-xl bg-indigo-50 dark:bg-indigo-950/70 text-indigo-600 dark:text-indigo-400 flex items-center justify-center shrink-0 border border-indigo-100 dark:border-indigo-900/50 group-hover:scale-105 transition-transform">
              <Building2 className="h-5 w-5" />
            </div>
            <div>
              <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Wszystkie Leady</div>
              <div className="text-2xl font-bold tracking-tight text-foreground mt-0.5">
                {kpis.total > 0 ? kpis.total : "50 (Demo)"}
              </div>
            </div>
          </div>
        </div>

        <div className="relative overflow-hidden rounded-2xl bg-white/70 dark:bg-zinc-900/70 p-4 backdrop-blur-xl border border-slate-200/80 dark:border-zinc-800/80 shadow-[0_2px_8px_rgba(0,0,0,0.03)] hover:shadow-md hover:border-amber-300/60 dark:hover:border-amber-700/60 transition-all group">
          <div className="flex items-center gap-3.5">
            <div className="h-11 w-11 rounded-xl bg-amber-50 dark:bg-amber-950/70 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0 border border-amber-100 dark:border-amber-900/50 group-hover:scale-105 transition-transform">
              <Flame className="h-5 w-5" />
            </div>
            <div>
              <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">PowerMatic / Hawk</div>
              <div className="text-2xl font-bold tracking-tight text-foreground mt-0.5">
                {kpis.total > 0 ? `${kpis.pmCount} ` : "24 "}
                <span className="text-xs font-medium text-amber-600 dark:text-amber-400 font-mono">
                  ({kpis.total > 0 ? kpis.pmPct : 48}%)
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="relative overflow-hidden rounded-2xl bg-white/70 dark:bg-zinc-900/70 p-4 backdrop-blur-xl border border-slate-200/80 dark:border-zinc-800/80 shadow-[0_2px_8px_rgba(0,0,0,0.03)] hover:shadow-md hover:border-emerald-300/60 dark:hover:border-emerald-700/60 transition-all group">
          <div className="flex items-center gap-3.5">
            <div className="h-11 w-11 rounded-xl bg-emerald-50 dark:bg-emerald-950/70 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0 border border-emerald-100 dark:border-emerald-900/50 group-hover:scale-105 transition-transform">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Zweryfikowane Rejestry</div>
              <div className="text-2xl font-bold tracking-tight text-foreground mt-0.5">
                {kpis.total > 0 ? `${kpis.verifiedCount} ` : "42 "}
                <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400 font-mono">
                  ({kpis.total > 0 ? kpis.verifiedPct : 84}%)
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="relative overflow-hidden rounded-2xl bg-white/70 dark:bg-zinc-900/70 p-4 backdrop-blur-xl border border-slate-200/80 dark:border-zinc-800/80 shadow-[0_2px_8px_rgba(0,0,0,0.03)] hover:shadow-md hover:border-blue-300/60 dark:hover:border-blue-700/60 transition-all group">
          <div className="flex items-center gap-3.5">
            <div className="h-11 w-11 rounded-xl bg-blue-50 dark:bg-blue-950/70 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0 border border-blue-100 dark:border-blue-900/50 group-hover:scale-105 transition-transform">
              <Globe className="h-5 w-5" />
            </div>
            <div>
              <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wider">Działające Strony</div>
              <div className="text-2xl font-bold tracking-tight text-foreground mt-0.5">
                {kpis.total > 0 ? kpis.webOkCount : "38"}
                <span className="text-xs font-medium text-blue-600 dark:text-blue-400 ml-1.5 text-[11px] font-mono">
                  200 OK
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main CRM Leads Table */}
      <ModernLeadsTableV2 leads={leads} />
    </motion.div>
  );
}
