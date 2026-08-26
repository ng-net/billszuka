import { useState, useRef, useEffect } from "react";
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
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { apiUrl } from "@/lib/api";

/**
 * GeminiDrawer — floating-action-button chat panel for "Gills — twój skowronek".
 * Triggered from any header that passes an onOpenSettings prop.
 *
 * Backend: POST /api/chat { query, active_dataset, knowledge_ids }
 *   Response: { response, provider }   (provider: openrouter | gemini | mock | mock-fallback | ...)
 *
 * Conversation is in-memory only (no persistence — by design per plan).
 */

// Curated prompts the user can fire with one click. Grouped so the drawer
// can label them. Each prompt is a complete, natural-language question —
// the same thing the user would type themselves.
const QUICK_PROMPTS = [
  {
    group: "Szukaj danych",
    icon: "🔍",
    items: [
      "Ile firm jest FROZEN w PL?",
      "Pokaż firmy z CZ które sprzedają PowerMatic",
      "Top 5 firm w PL z tier=wyłączność",
      "Lista hurtowników w CZ z wolumen=duży",
      "Firmy z DE z kanałem online",
      "Ile firm jest DO-WERYFIKACJI w RO?",
    ],
  },
  {
    group: "Przygotuj widok",
    icon: "📋",
    items: [
      "Rozkład firm wg kraju",
      "Status weryfikacji (FROZEN / DO-WERYFIKACJI)",
      "Tier × kraj",
      "Wolumen × kraj (mały/średni/duży)",
      "Top 10 krajów wg liczby firm",
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

export function GeminiDrawer({ onOpenSettings, activeDataset, knowledgeIds = [] }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]); // [{role: "user"|"assistant", text, provider?}]
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef(null);

  // Mirror knowledgeIds into a ref so the send() callback always sees the
  // latest selection without re-binding on every change. (App.jsx is the
  // single source of truth — the drawer just consumes it.)
  const knowledgeIdsRef = useRef(knowledgeIds);
  useEffect(() => {
    knowledgeIdsRef.current = knowledgeIds;
  }, [knowledgeIds]);

  // Autoscroll on new messages — Radix ScrollArea's Viewport is the actual
  // scrollable node, so we locate it by data-slot after each render.
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
      setMessages((m) => [
        ...m,
        { role: "assistant", text: body.response || "(brak odpowiedzi)", provider: body.provider },
      ]);
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

  function clearThread() {
    setMessages([]);
    toast.success("Wątek wyczyszczony");
  }

  function copyMsg(text) {
    navigator.clipboard?.writeText(text);
    toast.success("Skopiowano", { duration: 800 });
  }

  return (
    <>
      {/* Floating Action Button */}
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
            <div className="flex items-center justify-between">
              <SheetTitle className="flex items-center gap-2">
                <Bird className="h-5 w-5 text-violet-500" />
                <span>
                  Gills <span className="text-muted-foreground font-normal text-sm">— twój skowronek</span>
                </span>
              </SheetTitle>
              <div className="flex items-center gap-1">
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
              Pytaj o dane w master.csv albo załączone pliki. Gills ćwierka
              konkretami z bazy wiedzy.
            </SheetDescription>
          </SheetHeader>

          {/* Thread */}
          <ScrollArea className="flex-1 px-5 py-3" ref={scrollRef}>
            {messages.length === 0 ? (
              <EmptyState onPick={sendQuery} />
            ) : (
              <div className="space-y-3">
                {messages.map((m, i) => (
                  <Bubble key={i} msg={m} onCopy={copyMsg} />
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

          {/* Quick-prompt pills — visible while thread is empty or after a
              reply so the user can keep firing one-click questions. */}
          <QuickPrompts onPick={sendQuery} disabled={busy} />

          {/* Input */}
          <div className="border-t p-3 flex gap-2 items-end">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  sendQuery();
                }
              }}
              placeholder="Albo wpisz własne pytanie…"
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
                aria-label="Wyczyść wątek"
                title="Wyczyść wątek"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}

function EmptyState({ onPick }) {
  return (
    <div className="py-6 space-y-5">
      <div className="text-center space-y-1.5">
        <Bird className="h-10 w-10 mx-auto text-violet-400" />
        <p className="text-sm font-medium">Cześć! Jestem Gills.</p>
        <p className="text-xs text-muted-foreground">
          Pytaj o firmy w katalogu albo o załączone dokumenty.
        </p>
      </div>
      <div className="space-y-3">
        {QUICK_PROMPTS.map((group) => (
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
    </div>
  );
}

function QuickPrompts({ onPick, disabled }) {
  // Show a single horizontal strip of the most useful prompts so the
  // user always has a shortcut, even mid-conversation.
  const featured = [
    "Ile firm jest FROZEN w PL?",
    "Rozkład firm wg kraju",
    "Top 5 firm z tier=wyłączność",
    "Streść dokumenty",
  ];
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

function PromptPill({ q, onPick, disabled = false, compact = false }) {
  return (
    <button
      onClick={() => !disabled && onPick(q)}
      disabled={disabled}
      className={cn(
        "inline-flex items-center gap-1 rounded-full border bg-background text-left",
        "hover:bg-accent hover:border-violet-300 hover:text-foreground",
        "disabled:opacity-50 disabled:cursor-not-allowed transition-colors",
        compact ? "px-2.5 py-0.5 text-[11px]" : "px-3 py-1.5 text-xs",
      )}
    >
      {compact && <Sparkles className="h-2.5 w-2.5 text-violet-500 shrink-0" />}
      <span className="truncate">{q}</span>
    </button>
  );
}

function MarkdownText({ content }) {
  if (!content) return null;

  // Split lines into blocks
  const lines = content.split("\n");
  const elements = [];
  let inCodeBlock = false;
  let codeBlockType = "";
  let codeBlockLines = [];

  const formatInline = (text) => {
    // Regex for bold **text** and links [text](url)
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

    // Code / Callout block toggle
    if (trimmed.startsWith("```")) {
      if (inCodeBlock) {
        // Close code block
        const blockContent = codeBlockLines.join("\n");
        const type = codeBlockType;
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

    // Headings
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

    // Bullet list
    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      elements.push(
        <div key={idx} className="flex items-start gap-1.5 ml-1 my-0.5 text-xs leading-relaxed">
          <span className="text-violet-500 font-bold select-none">•</span>
          <div className="flex-1">{formatInline(trimmed.slice(2))}</div>
        </div>
      );
      return;
    }

    // Numbered list
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

    // Empty line
    if (!trimmed) {
      elements.push(<div key={idx} className="h-1.5" />);
      return;
    }

    // Standard paragraph
    elements.push(
      <p key={idx} className="my-0.5 text-xs leading-relaxed">
        {formatInline(line)}
      </p>
    );
  });

  return <div className="space-y-0.5">{elements}</div>;
}

function Bubble({ msg, onCopy }) {
  const isUser = msg.role === "user";
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
          <MarkdownText content={msg.text} />
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
      {!isUser && msg.provider && <ProviderTag provider={msg.provider} />}
    </motion.div>
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

