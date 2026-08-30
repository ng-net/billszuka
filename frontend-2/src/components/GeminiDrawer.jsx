import { useState, useRef, useEffect, useMemo, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Sparkles,
  Send,
  X,
  Copy,
  Trash2,
  Settings as SettingsIcon,
  Loader2,
  Bird,
  BookOpen,
  Download,
} from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { apiUrl } from "@/lib/api";
import { resolveAttachedFilenames } from "@/lib/knowledgeFiles";

/**
 * GeminiDrawer — floating-action-button chat panel for "Gills — twój skowronek".
 * Triggered from any header that passes an onOpenSettings prop.
 *
 * Backend: POST /api/chat { query, active_dataset, knowledge_ids }
 *   Response: { response, provider }   (provider: openrouter | gemini | mock | mock-fallback | faq | save | ...)
 *
 * Conversation is in-memory only (no persistence — by design per plan).
 *
 * UX additions vs the original (all four ship together — they're a coherent
 * batch aimed at "Gills feels less like a black box"):
 *   1. KnowledgeFilesChip in the header — shows which knowledge files are
 *      attached to the next call (click to open the picker). Without this
 *      the user has to guess whether their PDF is in scope.
 *   2. SessionFooter — running totals: questions / FAQ-hits (0 tok.) /
 *      LLM-calls / saves. Surfaces the cost-saving behaviour of FAQ so
 *      the user learns to ask FAQ-shaped questions.
 *   3. Keyboard shortcuts inside the panel: ⌘L clears, ↑ when input is
 *      empty re-loads the last user message for editing.
 *   4. DynamicQuickPrompts — pulls top countries from the active dataset
 *      so the prompt bar matches whatever the user has loaded.
 */

// Curated prompts that don't depend on the dataset shape (used as the
// fallback when the dataset fetch fails or returns no `kraj` column).
const STATIC_PROMPTS = [
  {
    group: "Szukaj danych",
    icon: "🔍",
    items: [
      "Ile firm jest FROZEN?",
      "Top 5 firm z tier=wyłączność",
      "Status weryfikacji (FROZEN / DO-WERYFIKACJI)",
    ],
  },
  {
    group: "Przygotuj widok",
    icon: "📋",
    items: [
      "Rozkład firm wg kraju",
      "Tier × kraj",
      "Wolumen × kraj (mały/średni/duży)",
    ],
  },
  {
    group: "Baza wiedzy",
    icon: "📚",
    items: [
      "Streść załączone dokumenty w 5 punktach",
      "Jakie firmy wymienia załączony raport?",
      "Wymień kluczowe wnioski z dokumentu PDF",
    ],
  },
];

const PROVIDER_FREE = new Set(["faq", "save"]);
const PROVIDER_LLM = new Set([
  "openrouter",
  "gemini",
  "gemini-3.6-flash",
  "gemini-2.5-flash",
  "openrouter-fallback",
  "gemini-fallback",
]);

export function GeminiDrawer({ onOpenSettings, activeDataset, knowledgeIds = [] }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  // Per-message provider lets the SessionFooter aggregate without re-parsing
  // the bubble list.
  const [stats, setStats] = useState({ total: 0, free: 0, llm: 0 });
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  // Knowledge base index — fetched lazily on first open so the chip can
  // show filenames. KnowledgeDrawer owns the canonical selection, but
  // re-fetching here is cheap and avoids a parent-API contract change.
  const [knowledgeIndex, setKnowledgeIndex] = useState([]);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  const knowledgeIdsRef = useRef(knowledgeIds);
  useEffect(() => {
    knowledgeIdsRef.current = knowledgeIds;
  }, [knowledgeIds]);

  // Fetch knowledge index once when the drawer first opens, then refresh
  // whenever the user toggles selection (so deletions propagate). The
  // chip only needs the id→filename map.
  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    fetch(apiUrl("/api/knowledge"))
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then((body) => {
        if (!cancelled && Array.isArray(body?.items)) setKnowledgeIndex(body.items);
      })
      .catch(() => {
        /* offline / no KB yet — chip just shows count without filenames */
      });
    return () => {
      cancelled = true;
    };
  }, [open, knowledgeIds.length]);

  useEffect(() => {
    if (!scrollRef.current) return;
    const viewport = scrollRef.current.querySelector(
      '[data-slot="scroll-area-viewport"]',
    );
    if (viewport) viewport.scrollTop = viewport.scrollHeight;
  }, [messages, busy]);

  async function sendQuery(q) {
    const text = (q ?? input).trim();
    if (!text || busy) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setBusy(true);
    try {
      const res = await fetch(apiUrl("/api/chat"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: text,
          active_dataset: activeDataset || "master.csv",
          knowledge_ids: knowledgeIdsRef.current,
        }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body?.detail || res.statusText);
      const provider = body.provider || "unknown";
      setMessages((m) => [
        ...m,
        { role: "assistant", text: body.response || "(brak odpowiedzi)", provider },
      ]);
      setStats((s) => ({
        total: s.total + 1,
        free: s.free + (PROVIDER_FREE.has(provider) ? 1 : 0),
        llm: s.llm + (PROVIDER_LLM.has(provider) ? 1 : 0),
      }));
    } catch (e) {
      const errMsg = e.message?.includes("Failed to fetch") || e.message?.includes("NetworkError")
        ? "Brak połączenia z serwerem API (127.0.0.1:8000). Upewnij się, że backend jest uruchomiony (`python tools/api_server.py`)."
        : (e.message || String(e));
      setMessages((m) => [
        ...m,
        { role: "assistant", text: `❌ ${errMsg}`, provider: "error" },
      ]);
      toast.error("Błąd czatu", { description: errMsg });
    } finally {
      setBusy(false);
    }
  }

  const clearThread = useCallback(() => {
    setMessages([]);
    setStats({ total: 0, free: 0, llm: 0 });
    toast.success("Wątek wyczyszczony");
  }, []);

  // Send a follow-up question to the admin proposal queue
  // (data/proposals/queue.jsonl). Backend route /api/chat/propose
  // rejects anything not rooted in master.csv.
  async function proposeQuestion(q) {
    const text = (q || "").trim();
    if (!text) return;
    try {
      const res = await fetch(apiUrl("/api/chat/propose"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question: text,
          source_dataset: activeDataset || "master.csv",
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok || body.ok === false) {
        toast.error("Nie dodano do kolejki", {
          description: body.detail || body.msg || res.statusText,
        });
        return;
      }
      toast.success(body.msg || "Dodano do kolejki propozycji");
    } catch (e) {
      toast.error("Błąd sieci", { description: e.message || String(e) });
    }
  }

  // Edit-last-message: when the input is empty and the user hits ArrowUp,
  // copy the most recent user message into the input for re-editing.
  // Standard chat-UX convention (terminal, Slack, every LLM client).
  const recallLastUser = useCallback(() => {
    if (busy) return;
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i].role === "user") {
        setInput(messages[i].text);
        requestAnimationFrame(() => inputRef.current?.focus());
        return;
      }
    }
  }, [messages, busy]);

  useEffect(() => {
    if (!open) return;
    const handler = (e) => {
      const isMeta = e.metaKey || e.ctrlKey;
      if (isMeta && e.key.toLowerCase() === "l") {
        e.preventDefault();
        if (messages.length > 0) clearThread();
      } else if (
        !isMeta &&
        e.key === "ArrowUp" &&
        input === "" &&
        document.activeElement === inputRef.current
      ) {
        e.preventDefault();
        recallLastUser();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, messages, input, clearThread, recallLastUser]);

  function copyMsg(text) {
    navigator.clipboard?.writeText(text);
    toast.success("Skopiowano", { duration: 800 });
  }

  // Export the whole thread as a Markdown transcript. Useful for pasting
  // into INTEL.md / an email — keeps provider tags so the recipient
  // knows which answers were zero-token FAQ hits vs paid Gemini calls.
  function exportTranscript() {
    if (messages.length === 0) return;
    const lines = [
      `# Wątek Gills — ${new Date().toLocaleString("pl-PL")}`,
      ``,
      `> Dataset: \`${activeDataset || "master.csv"}\``,
      `> Pliki wiedzy: ${knowledgeIds.length}`,
      ``,
    ];
    messages.forEach((m, i) => {
      const role = m.role === "user" ? "Ty" : `Gills${m.provider ? ` (${m.provider})` : ""}`;
      lines.push(`## ${i + 1}. ${role}`);
      lines.push("");
      lines.push(m.text.trim());
      lines.push("");
    });
    const md = lines.join("\n");
    navigator.clipboard?.writeText(md);
    toast.success("Transkrypt skopiowany do schowka", {
      description: `${messages.length} wiadomości · Markdown`,
    });
  }

  return (
    <>
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger asChild>
          <motion.button
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.4, type: "spring", stiffness: 260, damping: 22 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="fixed right-6 bottom-[max(1.5rem,env(safe-area-inset-bottom))] z-40 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 text-white shadow-lg hover:shadow-xl transition-shadow"
            aria-label="Otwórz Gills — twój skowronek"
            title="Gills — twój skowronek"
          >
            <Bird className="h-6 w-6" />
          </motion.button>
        </SheetTrigger>
        <SheetContent
          side="right"
          showCloseButton={false}
          className="w-full sm:max-w-md p-0 flex flex-col gap-0"
        >
          <SheetHeader className="px-5 pt-5 pb-3 border-b">
            <div className="flex items-center justify-between gap-2">
              <SheetTitle className="flex items-center gap-2 min-w-0">
                <Bird className="h-5 w-5 text-violet-500 shrink-0" />
                <span className="truncate">
                  Gills <span className="text-muted-foreground font-normal text-sm">— twój skowronek</span>
                </span>
              </SheetTitle>
              <div className="flex items-center gap-1 shrink-0">
                {messages.length > 0 && (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={exportTranscript}
                    aria-label="Eksportuj transkrypt"
                    title="Eksportuj transkrypt (do schowka, Markdown)"
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => {
                    setOpen(false);
                    onOpenSettings?.();
                  }}
                  aria-label="Ustawienia"
                  title="Ustawienia"
                >
                  <SettingsIcon className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setOpen(false)}
                  aria-label="Zamknij"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>
            <SheetDescription>
              Pytaj o dane w <span className="font-mono text-[11px]">{activeDataset || "master.csv"}</span>
              {knowledgeIds.length > 0 && (
                <> · baza wiedzy aktywna ({knowledgeIds.length})</>
              )}.
            </SheetDescription>
          </SheetHeader>

          {/* Thread */}
          <ScrollArea className="flex-1 px-5 py-3" ref={scrollRef}>
            {messages.length === 0 ? (
              <EmptyState onPick={sendQuery} activeDataset={activeDataset} />
            ) : (
              <div className="space-y-3">
                {messages.map((m, i) => (
                  <Bubble
                    key={i}
                    msg={m}
                    onCopy={copyMsg}
                    onFill={(q) => {
                      setInput(q);
                      requestAnimationFrame(() => inputRef.current?.focus());
                    }}
                    onPropose={(q) => proposeQuestion(q)}
                  />
                ))}
                {busy && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground pl-1">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    Gills ćwierka…
                  </div>
                )}
              </div>
            )}
          </ScrollArea>

          <QuickPrompts onPick={sendQuery} disabled={busy} />

          {/* Input */}
          <div className="border-t p-3 flex gap-2 items-end">
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendQuery();
                }
              }}
              placeholder="Albo wpisz własne pytanie… (↑ ostatnie)"
              className="flex-1"
              disabled={busy}
            />
            <Button
              onClick={() => sendQuery()}
              size="icon"
              disabled={busy || !input.trim()}
              aria-label="Wyślij"
            >
              <Send className="h-4 w-4" />
            </Button>
            {messages.length > 0 && (
              <Button
                onClick={clearThread}
                size="icon"
                variant="ghost"
                aria-label="Wyczyść wątek (⌘L)"
                title="Wyczyść wątek (⌘L)"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>

          <SessionFooter stats={stats} knowledgeCount={knowledgeIds.length} knowledgeIndex={knowledgeIndex} parentsSelected={knowledgeIds} />
        </SheetContent>
      </Sheet>
    </>
  );
}

/**
 * SessionFooter — compact running tally of this thread.
 * "0 tok." badge is the call-to-action: when free > 0 the user learns
 * that FAQ-shaped questions don't burn Gemini quota.
 */
export function SessionFooter({ stats, knowledgeCount, knowledgeIndex }) {
  return (
    <TooltipProvider delayDuration={200}>
      <div className="border-t bg-muted/30 px-5 py-2 flex items-center justify-between text-[11px] text-muted-foreground">
        <div className="flex items-center gap-3">
          <span title="Pytań w tym wątku">
            💬 <strong className="text-foreground tabular-nums">{stats.total}</strong>
          </span>
          {stats.free > 0 && (
            <span title="Obsłużone przez FAQ lub 'zapisz' (0 tokenów)">
              ✨ <strong className="text-emerald-600 dark:text-emerald-400 tabular-nums">{stats.free}</strong> 0 tok.
            </span>
          )}
          {stats.llm > 0 && (
            <span title="Wysłane do modelu (Gemini / OpenRouter)">
              🧠 <strong className="text-violet-600 dark:text-violet-400 tabular-nums">{stats.llm}</strong> LLM
            </span>
          )}
        </div>
        <KnowledgeFilesChip count={knowledgeCount} index={knowledgeIndex} />
      </div>
    </TooltipProvider>
  );
}

/**
 * KnowledgeFilesChip — shows how many KB files are attached and lists them
 * on hover. Without this, the user has to open KnowledgeDrawer to confirm
 * which files are flying in /api/chat.
 *
 * The pure resolver `resolveAttachedFilenames` lives in
 * `lib/knowledgeFiles.js` — keeping it out of this file means React Fast
 * Refresh doesn't get confused by a non-component export, and unit tests
 * don't have to import the whole drawer (which pulls framer-motion).
 */
export function KnowledgeFilesChip({ count, index, parentsSelected = [] }) {
  // Hooks first — never after a conditional return (rules-of-hooks).
  const names = useMemo(
    () => (count ? resolveAttachedFilenames(index, parentsSelected) : []),
    [count, index, parentsSelected],
  );
  if (!count) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="inline-flex items-center gap-1 opacity-60 cursor-help">
            <BookOpen className="h-3 w-3" /> brak plików
          </span>
        </TooltipTrigger>
        <TooltipContent side="top" className="text-xs max-w-xs">
          Żaden plik bazy wiedzy nie jest dołączany do następnej odpowiedzi.
          Otwórz 📚 w headerze, żeby wybrać pliki PDF/CSV/MD.
        </TooltipContent>
      </Tooltip>
    );
  }
  // Look up filenames by id (knowledgeIndex is [{id, filename, ...}])
  // Note: the parent's selection set is the source of truth — the chip
  // just renders whichever filenames it can resolve. Unknown ids are
  // filtered out (e.g. expired files removed by KnowledgeDrawer).
  const plural = count === 1 ? "" : count < 5 ? "i" : "ów";
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="inline-flex items-center gap-1 text-emerald-600 dark:text-emerald-400 cursor-help">
          <BookOpen className="h-3 w-3" />
          <strong className="tabular-nums">{count}</strong> plik{plural}
        </span>
      </TooltipTrigger>
      <TooltipContent side="top" className="text-xs max-w-xs">
        {names.length > 0 ? (
          <ul className="space-y-0.5">
            {names.map((n) => (
              <li key={n} className="truncate">📎 {n}</li>
            ))}
          </ul>
        ) : (
          "Pliki z bazy wiedzy dołączone do czatu."
        )}
      </TooltipContent>
    </Tooltip>
  );
}

function EmptyState({ onPick, activeDataset }) {
  return (
    <div className="py-6 space-y-5">
      <div className="text-center space-y-1.5">
        <Bird className="h-10 w-10 mx-auto text-violet-400" />
        <p className="text-sm font-medium">Cześć! Jestem Gills.</p>
        <p className="text-xs text-muted-foreground">
          Pytaj o firmy w katalogu albo o załączone dokumenty.
        </p>
      </div>
      <DynamicQuickPrompts onPick={onPick} activeDataset={activeDataset} />
    </div>
  );
}

/**
 * QuickPrompts — a slim horizontal strip that stays visible while the
 * thread has messages. Falls back to four curated questions that are
 * useful regardless of dataset shape.
 */
function QuickPrompts({ onPick, disabled }) {
  const featured = useMemo(
    () => ["Rozkład firm wg kraju", "Top 5 firm z tier=wyłączność", "Streść dokumenty"],
    [],
  );
  return (
    <div className="px-3 pt-2 pb-1 border-t bg-muted/20">
      <div className="flex flex-wrap gap-1.5">
        {featured.map((q) => (
          <PromptPill key={q} q={q} onPick={onPick} disabled={disabled} compact />
        ))}
      </div>
    </div>
  );
}

/**
 * DynamicQuickPrompts — three groups:
 *   1. "Szukaj" — generic + top-3 countries pulled from the active dataset
 *      (replaces the old hard-coded "Ile firm jest FROZEN w PL?" so the
 *      bar matches the data the user actually has loaded).
 *   2. "Widok" — pivot-style prompts that work with any dataset.
 *   3. "Wiedza" — knowledge-base prompts (only shown when files are
 *      attached, otherwise they'd be misleading).
 *
 * The dataset fetch is fire-and-forget; if it fails we render STATIC_PROMPTS.
 */
function DynamicQuickPrompts({ onPick, activeDataset }) {
  const [topCountries, setTopCountries] = useState([]);
  const [datasetFailed, setDatasetFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const ds = activeDataset || "master.csv";
    setDatasetFailed(false);
    fetch(apiUrl(`/api/dataset/${encodeURIComponent(ds)}?limit=2000`))
      .then((r) => (r.ok ? r.json() : Promise.reject(r.statusText)))
      .then((body) => {
        if (cancelled) return;
        const cols = body?.columns || [];
        const rows = body?.data || [];
        const idx = cols.findIndex((c) => c && c.toLowerCase() === "kraj");
        if (idx < 0 || rows.length === 0) return;
        const counts = new Map();
        for (const row of rows) {
          const v = (row[idx] || "").trim();
          if (!v) continue;
          counts.set(v, (counts.get(v) || 0) + 1);
        }
        const top = [...counts.entries()]
          .sort((a, b) => b[1] - a[1])
          .slice(0, 3)
          .map(([k]) => k);
        setTopCountries(top);
      })
      .catch(() => {
        if (!cancelled) setDatasetFailed(true);
      });
    return () => {
      cancelled = true;
    };
  }, [activeDataset]);

  const groups = useMemo(() => {
    if (datasetFailed || topCountries.length === 0) return STATIC_PROMPTS;
    return STATIC_PROMPTS.map((g) => {
      if (g.group !== "Szukaj danych") return g;
      const countryPrompts = topCountries.flatMap((c) => [
        `Ile firm jest w ${c}?`,
        `Top firmy w ${c}`,
      ]);
      // Keep the generic questions + add the country ones; cap at 6 to
      // keep the panel scannable.
      return { ...g, items: [...g.items.slice(0, 1), ...countryPrompts].slice(0, 6) };
    });
  }, [topCountries, datasetFailed]);

  return (
    <div className="space-y-3">
      {groups.map((group) => (
        <div key={group.group}>
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1.5 px-1">
            {group.icon} {group.group}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {group.items.map((q) => (
              <PromptPill key={q} q={q} onPick={onPick} />
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function PromptPill({ q, onPick, disabled = false, compact = false }) {
  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            onClick={() => !disabled && onPick(q)}
            disabled={disabled}
            className={cn(
              "inline-flex min-w-0 items-center gap-1 rounded-full border bg-background text-left",
              "hover:bg-accent hover:border-violet-300 hover:text-foreground",
              "disabled:opacity-50 disabled:cursor-not-allowed transition-colors",
              compact ? "px-2.5 py-0.5 text-[11px]" : "px-3 py-1.5 text-xs",
            )}
          >
            {compact && <Sparkles className="h-2.5 w-2.5 text-violet-500 shrink-0" />}
            <span className="truncate max-w-[28ch]">{q}</span>
          </button>
        </TooltipTrigger>
        <TooltipContent side="top" className="text-xs max-w-xs">
          {q}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export function MarkdownText({ content }) {
  if (!content) return null;

  const lines = content.split("\n");
  const elements = [];
  let inCodeBlock = false;
  let codeBlockType = "";
  let codeBlockLines = [];
  // Pulled out of the bubble — shown as clickable pills below it.
  // The model emits them in a ```followup … ``` block at the end of its
  // answer (one question per line). Keeping them outside the bubble keeps
  // the prose tight and makes the chips easier to scan.
  const followups = [];

  const formatInline = (text) => {
    const parts = [];
    let lastIndex = 0;
    const regex = /(\*\*[^*]+\*\*|\[[^\]]+\]\(https?:\/\/[^\s)]+\))/g;
    let match;

    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push(text.slice(lastIndex, match.index));
      }
      const raw = match[0];
      if (raw.startsWith("**") && raw.endsWith("**")) {
        parts.push(
          <strong key={match.index} className="font-semibold text-foreground">
            {raw.slice(2, -2)}
          </strong>
        );
      } else if (raw.startsWith("[") && raw.includes("](")) {
        const titleMatch = raw.match(/^\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)$/);
        if (titleMatch) {
          parts.push(
            <a
              key={match.index}
              href={titleMatch[2]}
              target="_blank"
              rel="noreferrer"
              className="text-violet-600 underline underline-offset-2 hover:text-violet-800"
            >
              {titleMatch[1]}
            </a>
          );
        } else {
          parts.push(raw);
        }
      }
      lastIndex = regex.lastIndex;
    }
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }
    return parts.length > 0 ? parts : text;
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();

    if (trimmed.startsWith("```")) {
      if (inCodeBlock) {
        const blockContent = codeBlockLines.join("\n");
        const type = codeBlockType;
        if (type === "followup") {
          // Each non-empty line is a suggested next question.
          for (const line of blockContent.split("\n")) {
            const q = line.replace(/^[-*\d.\s]+/, "").trim();
            if (q) followups.push(q);
          }
          inCodeBlock = false;
          codeBlockType = "";
          codeBlockLines = [];
          return;
        }
        if (type === "fakt") {
          elements.push(
            <div key={`block-${idx}`} className="my-2 rounded-md border border-emerald-300 bg-emerald-50 dark:bg-emerald-950/40 p-2.5 text-xs text-emerald-900 dark:text-emerald-100">
              <span className="font-semibold block mb-0.5">📌 Kluczowy fakt:</span>
              <div className="whitespace-pre-wrap">{blockContent}</div>
            </div>
          );
        } else if (type === "errata") {
          elements.push(
            <div key={`block-${idx}`} className="my-2 rounded-md border border-amber-300 bg-amber-50 dark:bg-amber-950/40 p-2.5 text-xs text-amber-900 dark:text-amber-100">
              <span className="font-semibold block mb-0.5">⚠️ Errata / Uwaga:</span>
              <div className="whitespace-pre-wrap">{blockContent}</div>
            </div>
          );
        } else {
          elements.push(
            <pre key={`block-${idx}`} className="my-2 rounded-md bg-zinc-900 text-zinc-100 p-2 text-xs overflow-x-auto">
              <code>{blockContent}</code>
            </pre>
          );
        }
        inCodeBlock = false;
        codeBlockType = "";
        codeBlockLines = [];
      } else {
        inCodeBlock = true;
        codeBlockType = trimmed.slice(3).trim().toLowerCase();
        codeBlockLines = [];
      }
      return;
    }

    if (inCodeBlock) {
      codeBlockLines.push(line);
      return;
    }

    if (trimmed.startsWith("## ")) {
      elements.push(
        <h4 key={idx} className="font-semibold text-sm mt-2.5 mb-1 text-foreground">
          {formatInline(trimmed.slice(3))}
        </h4>
      );
      return;
    }
    if (trimmed.startsWith("### ")) {
      elements.push(
        <h5 key={idx} className="font-medium text-xs mt-2 mb-0.5 text-foreground">
          {formatInline(trimmed.slice(4))}
        </h5>
      );
      return;
    }

    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      elements.push(
        <div key={idx} className="flex items-start gap-1.5 ml-1 my-0.5 text-xs leading-relaxed">
          <span className="text-violet-500 font-bold select-none">•</span>
          <div className="flex-1">{formatInline(trimmed.slice(2))}</div>
        </div>
      );
      return;
    }

    const numMatch = trimmed.match(/^(\d+)\.\s+(.*)$/);
    if (numMatch) {
      elements.push(
        <div key={idx} className="flex items-start gap-1.5 ml-1 my-0.5 text-xs leading-relaxed">
          <span className="text-violet-600 font-medium select-none">{numMatch[1]}.</span>
          <div className="flex-1">{formatInline(numMatch[2])}</div>
        </div>
      );
      return;
    }

    if (!trimmed) {
      elements.push(<div key={idx} className="h-1.5" />);
      return;
    }

    elements.push(
      <p key={idx} className="my-0.5 text-xs leading-relaxed">
        {formatInline(line)}
      </p>
    );
  });

  return <div className="space-y-0.5">{elements}</div>;
}

function Bubble({ msg, onCopy, onFill, onPropose }) {
  const isUser = msg.role === "user";
  const rendered = !isUser ? <MarkdownText content={msg.text} /> : null;
  const followups = !isUser && rendered && typeof rendered === "object" ? rendered.followups : null;
  const body = !isUser && rendered && typeof rendered === "object" ? rendered.elements : rendered;
  return (
    <motion.div
      initial={{ opacity: 0, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.12 }}
      className={`flex flex-col gap-1 ${isUser ? "items-end" : "items-start"}`}
    >
      <div
        className={`group relative max-w-[88%] rounded-lg px-3 py-2 text-sm shadow-sm ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted/90 text-foreground border border-border/50"
        }`}
      >
        {isUser ? (
          <div className="whitespace-pre-wrap break-words text-xs">{msg.text}</div>
        ) : (
          <div className="space-y-0.5">{body}</div>
        )}
        {!isUser && (
          <Button
            onClick={() => onCopy(msg.text)}
            size="icon"
            variant="ghost"
            className="absolute -top-2 -right-2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity bg-background border shadow-xs"
            aria-label="Kopiuj"
          >
            <Copy className="h-3 w-3" />
          </Button>
        )}
      </div>
      {!isUser && followups && followups.length > 0 && (
        <FollowupPills items={followups} onFill={onFill} onPropose={onPropose} />
      )}
      {!isUser && msg.provider && <ProviderTag provider={msg.provider} />}
    </motion.div>
  );
}

export function FollowupPills({ items, onFill, onPropose }) {
  // Each pill has TWO actions:
  //   - Click the question text → fills the input box (so the user can
  //     review/edit before sending). This is the safer default — never
  //     auto-fires an LLM call.
  //   - Click the small 📥 button → adds the question to the admin
  //     proposal queue (data/proposals/queue.jsonl) for future inclusion
  //     in the FAQ / knowledge corpus. Admin of BILLSzuka reviews and
  //     approves manually.
  return (
    <div className="flex flex-wrap gap-1.5 max-w-[88%] pl-1">
      {items.slice(0, 4).map((q, i) => (
        <div
          key={i}
          className="inline-flex items-center rounded-full border bg-background hover:border-violet-300 transition-colors"
          title={q}
        >
          <button
            onClick={() => onFill(q)}
            className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] text-left rounded-l-full hover:bg-accent transition-colors"
            aria-label={`Wstaw pytanie: ${q}`}
          >
            <Sparkles className="h-2.5 w-2.5 text-violet-500 shrink-0" />
            <span className="truncate max-w-[36ch]">{q}</span>
          </button>
          <button
            onClick={() => onPropose(q)}
            className="px-1.5 py-1 text-[11px] border-l text-muted-foreground hover:bg-emerald-50 hover:text-emerald-700 dark:hover:bg-emerald-950/40 dark:hover:text-emerald-300 rounded-r-full transition-colors"
            aria-label={`Zaproponuj pytanie do bazy wiedzy: ${q}`}
            title="Zaproponuj pytanie adminowi BILLSzuka"
          >
            📥
          </button>
        </div>
      ))}
    </div>
  );
}

function ProviderTag({ provider }) {
  const palette = {
    openrouter: { label: "OpenRouter", color: "bg-blue-100 text-blue-700 border-blue-300 dark:bg-blue-950 dark:text-blue-200" },
    gemini: { label: "Gemini 3.6 Flash", color: "bg-purple-100 text-purple-700 border-purple-300 dark:bg-purple-950 dark:text-purple-200" },
    "gemini-3.6-flash": { label: "Gemini 3.6 Flash", color: "bg-purple-100 text-purple-700 border-purple-300 dark:bg-purple-950 dark:text-purple-200" },
    "gemini-2.5-flash": { label: "Gemini 2.5 Flash", color: "bg-purple-100 text-purple-700 border-purple-300 dark:bg-purple-950 dark:text-purple-200" },
    faq: { label: "FAQ Cache (0 tokenów)", color: "bg-emerald-100 text-emerald-700 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-200" },
    save: { label: "Zapisano fakt", color: "bg-emerald-100 text-emerald-700 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-200" },
    mock: { label: "Mock", color: "bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-800 dark:text-gray-200" },
    "mock-gemini-quota": { label: "Mock (limit Gemini)", color: "bg-amber-100 text-amber-700 border-amber-300 dark:bg-amber-950 dark:text-amber-200" },
    "mock-fallback": { label: "Mock (fallback)", color: "bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-800 dark:text-gray-200" },
    "openrouter-fallback": { label: "OpenRouter (fallback)", color: "bg-blue-100 text-blue-700 border-blue-300 dark:bg-blue-950 dark:text-blue-200" },
    "gemini-fallback": { label: "Gemini (fallback)", color: "bg-purple-100 text-purple-700 border-purple-300 dark:bg-purple-950 dark:text-purple-200" },
    error: { label: "Błąd", color: "bg-red-100 text-red-700 border-red-300 dark:bg-red-950 dark:text-red-200" },
  };
  const base = String(provider).split(" ")[0].replace("(+1file)", "").replace("(+1 file)", "");
  const p = palette[base] || palette[provider] || { label: provider, color: "bg-gray-100 text-gray-700 border-gray-300" };
  return (
    <Badge variant="outline" className={`text-[10px] h-4.5 px-1.5 ${p.color}`}>
      {p.label}
    </Badge>
  );
}
