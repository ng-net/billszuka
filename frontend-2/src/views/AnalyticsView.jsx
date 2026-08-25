import { motion } from "framer-motion";
import { Bird, Sparkles, BarChart3, FileDown, Wand2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";

/**
 * AnalyticsView — "W przygotowaniu…" hero (placeholder for the real dashboard).
 *
 * Background context: while the real analytics are being built, the view shows
 * a prominent hero with a Polish joke about Gil czerwony (red bullfinch — the
 * classic Polish B2B wingman who always shows up first to meetings). The joke
 * does double duty: it's a status message AND a tiny bit of in-product charm.
 *
 * The previous version had live charts; those will return when the dashboard
 * is rebuilt. The data endpoint is still wired (it just isn't called from here
 * anymore — TableView loads the same data on demand).
 */

const COMING_FEATURES = [
  { icon: BarChart3, label: "Rozkłady per kraj i tier" },
  { icon: FileDown, label: "Eksport wykresów do PDF" },
  { icon: Wand2, label: "Insights z Gemini na Twoich danych" },
];

export function AnalyticsView() {
  return (
    <div className="relative h-full overflow-auto">
      {/* Subtle gradient backdrop — keeps the page from feeling empty */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-gradient-to-br from-background via-background to-rose-50/40 dark:to-rose-950/20"
      />

      <div className="relative flex min-h-full items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, ease: "easeOut" }}
          className="max-w-2xl w-full text-center"
        >
          {/* Bird avatar — bobs gently */}
          <motion.div
            initial={{ scale: 0.85, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.08, ease: "easeOut" }}
            className="relative inline-flex mb-6"
          >
            <div className="flex h-24 w-24 items-center justify-center rounded-3xl bg-gradient-to-br from-rose-100 via-rose-50 to-amber-100 dark:from-rose-950 dark:via-rose-900/40 dark:to-amber-950 shadow-sm ring-1 ring-rose-200/40 dark:ring-rose-800/30">
              <motion.div
                animate={{ y: [0, -3, 0], rotate: [0, -2, 2, 0] }}
                transition={{ duration: 3.2, repeat: Infinity, ease: "easeInOut" }}
              >
                <Bird className="h-12 w-12 text-rose-600" strokeWidth={1.6} />
              </motion.div>
            </div>
            {/* Tiny "..." trail to suggest motion */}
            <span className="absolute -right-3 top-1/2 -translate-y-1/2 text-rose-400/60 text-xs tracking-widest">
              ···
            </span>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.18 }}
          >
            <Badge variant="outline" className="mb-5 text-xs font-normal">
              <Sparkles className="h-3 w-3 mr-1" />
              Wkrótce
            </Badge>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.24 }}
            className="text-4xl sm:text-5xl font-bold tracking-tight mb-3"
          >
            W przygotowaniu…
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.3 }}
            className="text-base text-muted-foreground max-w-md mx-auto mb-8"
          >
            Pełny dashboard z metrykami, eksportem do PDF i insights od Gemini.
          </motion.p>

          {/* The joke card — Gil czerwony is a Polish B2B in-joke */}
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.38 }}
            className="rounded-2xl border bg-card/70 backdrop-blur p-5 text-left shadow-sm"
          >
            <div className="flex items-start gap-3">
              <div className="h-9 w-9 rounded-full bg-rose-100 dark:bg-rose-950 flex items-center justify-center shrink-0 ring-1 ring-rose-200/50 dark:ring-rose-800/40">
                <Bird className="h-4 w-4 text-rose-600" strokeWidth={2} />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-semibold mb-1">
                  Gil czerwony właśnie ostrzy dziób
                </p>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Nowe analityki lądują wkrótce — z pełnym feedem danych, eksportem
                  do PDF i prawdopodobnie z pajdą chleba dla reszty ptactwa, które
                  znowu przyleci na 9:30.
                </p>
              </div>
            </div>
          </motion.div>

          {/* What's coming — small teaser so the user knows what to expect */}
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.46 }}
            className="mt-8 flex flex-wrap items-center justify-center gap-2"
          >
            {COMING_FEATURES.map((f) => {
              const Icon = f.icon;
              return (
                <div
                  key={f.label}
                  className="inline-flex items-center gap-2 rounded-full border bg-background/60 px-3 py-1.5 text-xs text-muted-foreground"
                >
                  <Icon className="h-3.5 w-3.5" />
                  {f.label}
                </div>
              );
            })}
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}
