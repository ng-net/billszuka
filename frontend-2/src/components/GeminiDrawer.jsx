import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  Send,
  X,
  Copy,
  Trash2,
  Settings as SettingsIcon,
  Loader2,
  ChevronDown,
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
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";

/**
 * GeminiDrawer — floating-action-button chat panel.
 * Triggered from any header that passes an onOpenSettings prop.
 *
 * Backend: POST /api/chat { query, active_dataset }
 *   Response: { response, provider }   (provider: openrouter | gemini | mock | mock-fallback | ...)
 *
 * Conversation is in-memory only (no persistence — by design per plan).
 */
export function GeminiDrawer({ onOpenSettings, activeDataset }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]); // [{role: "user"|"assistant", text, provider?}]
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef(null);

  // Autoscroll on new messages — Radix ScrollArea's Viewport is the actual
  // scrollable node, so we locate it by data-slot after each render.
  useEffect(() => {
    if (!scrollRef.current) return;
    const viewport = scrollRef.current.querySelector(
      '[data-slot="scroll-area-viewport"]',
    );
    if (viewport) viewport.scrollTop = viewport.scrollHeight;
  }, [messages, busy]);

  async function send() {
    const q = input.trim();
    if (!q || busy) return;
    setMessages((m) => [...m, { role: "user", text: q }]);
    setInput("");
    setBusy(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: q,
          active_dataset: activeDataset || "master.csv",
        }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body?.detail || res.statusText);
      setMessages((m) => [
        ...m,
        { role: "assistant", text: body.response || "(brak odpowiedzi)", provider: body.provider },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: `❌ ${e.message || e}`, provider: "error" },
      ]);
      toast.error("Błąd czatu", { description: e.message });
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
            className="fixed bottom-6 right-6 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-violet-500 to-fuchsia-500 text-white shadow-lg hover:shadow-xl transition-shadow"
            aria-label="Otwórz AI Assistant"
          >
            <Sparkles className="h-6 w-6" />
          </motion.button>
        </SheetTrigger>
        <SheetContent
          side="right"
          className="w-full sm:max-w-md p-0 flex flex-col gap-0"
        >
          <SheetHeader className="px-5 pt-5 pb-3 border-b">
            <div className="flex items-center justify-between">
              <SheetTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-violet-500" />
                AI Assistant
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
              Zadaj pytania o dane w master.csv. Backend używa łańcucha awaryjnego
              OpenRouter → Gemini → mock.
            </SheetDescription>
          </SheetHeader>

          {/* Thread */}
          <ScrollArea className="flex-1 px-5 py-3" ref={scrollRef}>
            {messages.length === 0 ? (
              <EmptyState />
            ) : (
              <div className="space-y-3">
                {messages.map((m, i) => (
                  <Bubble key={i} msg={m} onCopy={copyMsg} />
                ))}
                {busy && (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground pl-1">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    Myślę…
                  </div>
                )}
              </div>
            )}
          </ScrollArea>

          {/* Input */}
          <div className="border-t p-3 flex gap-2 items-end">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              placeholder="Np. ile firm jest FROZEN w PL?"
              className="flex-1"
              disabled={busy}
            />
            <Button
              onClick={send}
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

function EmptyState() {
  const examples = [
    "ile firm jest FROZEN w PL?",
    "rozkład firm wg kraju",
    "pokaż top 5 firm z tier=wyłączność",
  ];
  return (
    <div className="text-center py-8 space-y-3">
      <Sparkles className="h-10 w-10 mx-auto text-violet-400 opacity-50" />
      <div>
        <p className="text-sm text-muted-foreground">Zacznij od pytania o dane.</p>
        <p className="text-xs text-muted-foreground mt-1">
          Przykłady:
        </p>
      </div>
      <div className="space-y-1.5 text-left">
        {examples.map((e) => (
          <div
            key={e}
            className="rounded-md border px-3 py-1.5 text-xs text-muted-foreground bg-muted/30 font-mono"
          >
            {e}
          </div>
        ))}
      </div>
    </div>
  );
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
        className={`group relative max-w-[85%] rounded-lg px-3 py-2 text-sm ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-foreground"
        }`}
      >
        <div className="whitespace-pre-wrap break-words">{msg.text}</div>
        {!isUser && (
          <Button
            onClick={() => onCopy(msg.text)}
            size="icon"
            variant="ghost"
            className="absolute -top-2 -right-2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity bg-background border"
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
    openrouter: { label: "OpenRouter", color: "bg-blue-100 text-blue-700 border-blue-300" },
    gemini: { label: "Gemini", color: "bg-purple-100 text-purple-700 border-purple-300" },
    "gemini-2.5-flash": { label: "Gemini 2.5 Flash", color: "bg-purple-100 text-purple-700 border-purple-300" },
    mock: { label: "Mock", color: "bg-gray-100 text-gray-700 border-gray-300" },
    "mock-fallback": { label: "Mock (fallback)", color: "bg-gray-100 text-gray-700 border-gray-300" },
    "openrouter-fallback": { label: "OpenRouter (fallback)", color: "bg-blue-100 text-blue-700 border-blue-300" },
    "gemini-fallback": { label: "Gemini (fallback)", color: "bg-purple-100 text-purple-700 border-purple-300" },
    error: { label: "Error", color: "bg-red-100 text-red-700 border-red-300" },
  };
  const p = palette[provider] || { label: provider, color: "bg-gray-100 text-gray-700 border-gray-300" };
  return (
    <Badge variant="outline" className={`text-[10px] h-5 px-1.5 ${p.color}`}>
      {p.label}
    </Badge>
  );
}