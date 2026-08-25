# Phase 2 — Gills FAQ & Knowledge: frontend drawer

**Spec:** `docs/superpowers/specs/2026-08-25-gills-faq-knowledge-design.md` (approved)
**Depends on:** Phase 1 (`docs/superpowers/plans/2026-08-25-gills-faq-phase1-backend.md`) executed, tested, and approved at its REST POINT. Phase 2 must NOT start before that.

**Goal:** FAQ view inside the Gills drawer (view switch, search/group/expand, badges, hits, staleness banner, 409-safe Generuj, session polling, per-entry delete), hardened answer-markup renderer with security tests, "Zapisz do wiedzy" save button, knowledge uploader markings + doc-scoped extraction offer + pending badge, and name persistence for the verified user header.

**Architecture (keep it simple):**
- No new npm dependencies. Tests stay `node --test` (pure JS files only).
- The parser lives in plain JS (`src/lib/answerMarkup.js`, AST-only, no React) so node can security-test it directly; `AnswerMarkup.jsx` is a dumb AST→React mapper that only ever uses AST values (link `href` is already http(s)-only at the AST level).
- The save button reuses `POST /api/chat` with the command phrase `"zapisz ten fakt"` — Phase 1 checks save-commands before FAQ lookup and before any LLM call, so it costs zero tokens and needs no extra endpoint.
- FaqView is self-contained (fetches its own data), so App.jsx only wires one badge counter and one callback.

**Scope simplifications (vs spec):**
1. No save-fact endpoint or dedicated save API — the button sends the save command through `/api/chat` (zero tokens, one code path).
2. No `Accordion`/`Collapsible` components — expand/collapse is a `Set` of open ids + chevron.
3. Pending inbox count lives in App.jsx as one `fetch("/api/knowledge")` on mount + refresh after saves/drawer-close. No polling.
4. Rejects list is a toggle inside FaqView (no separate drawer/page).
5. Column count in `cols` blocks is decided by the renderer from item count (cap 4) — no per-block configuration.

**Backend contract (from Phase 1 — do not re-derive):**
- `POST /api/chat {query, active_dataset, knowledge_ids}` → `{response, provider}`; provider ∈ `faq | save | gemini | openrouter | mock | …`. Save-command replies `provider:"save"`. FAQ hits `provider:"faq"`.
- `GET /api/faq` → `{items: [{id, q, a, category, sources (JSON string), verified_kind, hits, stale}], categories: [..], rejects: N}`
- `POST /api/faq/generate {mode, doc_id?}` → **verified header required** (403); 409 when a session runs; else `{ok, mode, state:"running"}`
- `GET /api/faq/session` → `{state, mode, progress, report, …}` or `{state:"idle"}`
- `DELETE /api/faq/{entry_id}` → verified header required (403); `{ok, deleted}`
- `GET /api/faq/rejects` → `{items: [{q, reason, rejected_at, …}]}`
- `GET /api/knowledge` → `{items (with uploaded_by), count, inbox, inbox_pending}`
- `POST /api/knowledge/upload`, `DELETE /api/knowledge/{id}`, `POST /api/knowledge/{id}/refresh` → verified header required (403)
- Verified header: `X-Billszuka-User: <name>` — server checks `sha256(trim+lower(name))` against `frontend-2/public/access.json`.

**File map:**
| File | Change |
|---|---|
| `frontend-2/src/lib/answerMarkup.js` | NEW — parser, AST only, plain JS (node-testable) |
| `frontend-2/src/components/AnswerMarkup.jsx` | NEW — AST→React mapper (XSS boundary) |
| `frontend-2/src/lib/answerMarkup.test.js` | NEW — security tests (node --test) |
| `frontend-2/src/lib/access.js` | MODIFY — name persistence + `authHeaders()` |
| `frontend-2/src/components/AccessGate.jsx` | MODIFY — persist name after verification |
| `frontend-2/src/lib/access.test.js` | MODIFY — name-persistence tests |
| `frontend-2/src/components/FaqView.jsx` | NEW — FAQ catalog view |
| `frontend-2/src/components/GeminiDrawer.jsx` | REWRITE — view switch, save button, markup, header |
| `frontend-2/src/components/KnowledgeDrawer.jsx` | MODIFY — auth headers, uploaded_by badge, extraction offer |
| `frontend-2/src/App.jsx` | MODIFY — pending badge + wiring |
| `frontend-2/package.json` | MODIFY — test script |

**Work hygiene — rest between work (anti-hallucination protocol):**
1. Never trust memory of file contents — re-read a file or its diff before every edit.
2. Every task ends with a green check (test run / lint / build) + a git commit.
3. REST POINT after Task 2 (frontend groundwork, backend-independent) and after Task 4 (view switch done).
4. REST POINT at the end of Phase 2: full check + live smoke test, then STOP for Marceli's review.

**Pre-flight (before any edit):** `cd frontend-2 && npm install` (deps already in package.json), `git status` clean except planned files, and confirm Phase 1 REST POINT was approved.

---

## Task 1 — Answer markup parser + renderer + security tests

Files: `frontend-2/src/lib/answerMarkup.js` (new), `frontend-2/src/components/AnswerMarkup.jsx` (new), `frontend-2/src/lib/answerMarkup.test.js` (new), `frontend-2/package.json` (modify).

### Step 1: Create `frontend-2/src/lib/answerMarkup.js`

```js
/**
 * answerMarkup.js — light-markup parser for Gills answers (spec §9).
 * Pure data: text → AST blocks, no React. Node runs the security tests
 * directly (node --test), so all safety guarantees live here.
 * AnswerMarkup.jsx is a dumb mapper — it must only ever use AST values.
 *
 * Markup contract:
 *   ## Title            heading (1–3 hashes)
 *   **text**            bold (pairs only — odd `**` degrades to text)
 *   - item              bullet list (two-space indent nests, capped)
 *   1. item             numbered list
 *   [text](https://…)   link — only http(s) after trim+decode; anything
 *                       else (javascript:, data:, vbscript:, encoded
 *                       variants) renders as plain text
 *   ```fakt / ```errata / ```cols fences — unclosed fences degrade to text
 *
 * Parser limits (never crash, never loop): MAX_BLOCKS blocks per answer,
 * nesting capped at MAX_NESTING, cols capped at 4 columns in the renderer.
 */

export const MAX_BLOCKS = 500;
export const MAX_NESTING = 6;

const LINK_RE = /\[([^\]]*)\]\(([^)\s]+)\)/g;
const FENCE_RE = /^\s*```\s*(fakt|errata|cols)\s*$/;
const CLOSE_RE = /^\s*```\s*$/;

/** http(s) after trim + decode only — the XSS boundary for links. */
export function safeHref(raw) {
  try {
    const decoded = decodeURIComponent(String(raw).trim());
    return /^https?:\/\//i.test(decoded) ? decoded : null;
  } catch {
    return null;
  }
}

function pushBold(out, segment) {
  const parts = segment.split("**");
  if (parts.length < 3) {
    if (segment) out.push({ t: "text", v: segment });
    return;
  }
  const pairs = parts.length % 2 === 0 ? parts.length : parts.length - 1;
  for (let i = 0; i < pairs; i++) {
    if (!parts[i]) continue;
    out.push(i % 2 === 1 ? { t: "strong", v: parts[i] } : { t: "text", v: parts[i] });
  }
  if (parts.length > pairs) out.push({ t: "text", v: parts.slice(pairs).join("**") });
}

/** Inline → [{t:"text"|"strong",v} | {t:"link",label,href}]. */
export function renderInline(text) {
  const out = [];
  LINK_RE.lastIndex = 0;
  let last = 0;
  for (let m; (m = LINK_RE.exec(text)) !== null; ) {
    if (m.index > last) pushBold(out, text.slice(last, m.index));
    const href = safeHref(m[2]);
    if (href) out.push({ t: "link", label: m[1], href });
    else pushBold(out, m[0]); // non-http destination → plain text, never a link
    last = m.index + m[0].length;
  }
  if (last < text.length) pushBold(out, text.slice(last));
  return out;
}

/** Text → block AST. Malformed input degrades to text — never throws. */
export function parseAnswer(text) {
  const lines = String(text ?? "").split(/\r?\n/);
  const blocks = [];
  let para = [];
  let fence = null;
  let list = null;
  const flushPara = () => {
    if (para.length) blocks.push({ t: "para", inline: renderInline(para.join(" ")) });
    para = [];
  };
  const flushList = () => {
    if (list) blocks.push(list);
    list = null;
  };
  for (const raw of lines) {
    if (blocks.length >= MAX_BLOCKS) break;
    if (fence) {
      if (CLOSE_RE.test(raw)) {
        if (fence.kind === "cols") {
          blocks.push({
            t: "cols",
            items: fence.lines.filter((l) => l.trim()).map((l) => renderInline(l.trim())),
          });
        } else {
          blocks.push({ t: fence.kind, inline: renderInline(fence.lines.join(" ")) });
        }
        fence = null;
      } else {
        fence.lines.push(raw);
      }
      continue;
    }
    const fm = raw.match(FENCE_RE);
    if (fm) {
      flushPara();
      flushList();
      fence = { kind: fm[1], lines: [] };
      continue;
    }
    const h = raw.match(/^(#{1,3})\s+(.+)$/);
    if (h) {
      flushPara();
      flushList();
      blocks.push({ t: "heading", level: h[1].length, inline: renderInline(h[2]) });
      continue;
    }
    const bullet = raw.match(/^(\s*)-\s+(.+)$/);
    if (bullet) {
      flushPara();
      const depth = Math.min(Math.floor(bullet[1].replace(/\t/g, "  ").length / 2), MAX_NESTING);
      if (!list || list.t !== "bullet" || list.depth !== depth) {
        flushList();
        list = { t: "bullet", depth, items: [] };
      }
      list.items.push(renderInline(bullet[2]));
      continue;
    }
    const num = raw.match(/^(\s*)\d+\.\s+(.+)$/);
    if (num) {
      flushPara();
      const depth = Math.min(Math.floor(num[1].replace(/\t/g, "  ").length / 2), MAX_NESTING);
      if (!list || list.t !== "number" || list.depth !== depth) {
        flushList();
        list = { t: "number", depth, items: [] };
      }
      list.items.push(renderInline(num[2]));
      continue;
    }
    if (raw.trim() === "") {
      flushPara();
      flushList();
      continue;
    }
    flushList();
    para.push(raw.trim());
  }
  flushPara();
  flushList();
  if (fence) blocks.push({ t: "para", inline: renderInline(fence.lines.join(" ")) });
  return blocks;
}
```

### Step 2: Create `frontend-2/src/components/AnswerMarkup.jsx`

```jsx
import { AlertTriangle, Lightbulb } from "lucide-react";
import { parseAnswer } from "@/lib/answerMarkup";
import { cn } from "@/lib/utils";

/**
 * AnswerMarkup — renders Gills' light markup (spec §9). XSS boundary for
 * untrusted LLM output: builds React elements only, never
 * dangerouslySetInnerHTML. Links come from the AST where the href is
 * already http(s)-only (see lib/answerMarkup.js + its security tests).
 */

const COLS = {
  1: "grid-cols-1",
  2: "grid-cols-2",
  3: "grid-cols-2 sm:grid-cols-3",
  4: "grid-cols-2 sm:grid-cols-3 lg:grid-cols-4",
};

function Inline({ nodes }) {
  return nodes.map((n, i) => {
    if (n.t === "strong") {
      return <strong key={i} className="font-semibold">{n.v}</strong>;
    }
    if (n.t === "link") {
      return (
        <a
          key={i}
          href={n.href}
          target="_blank"
          rel="noopener noreferrer"
          className="text-violet-600 underline underline-offset-2 hover:text-violet-800 break-all"
        >
          {n.label || n.href}
        </a>
      );
    }
    return <span key={i}>{n.v}</span>;
  });
}

function Block({ b }) {
  switch (b.t) {
    case "heading": {
      const cls = b.level === 1
        ? "text-base font-semibold"
        : b.level === 2 ? "text-sm font-semibold" : "text-sm font-medium";
      const Tag = b.level === 1 ? "h3" : "h4";
      return <Tag className={cls}><Inline nodes={b.inline} /></Tag>;
    }
    case "para":
      return <p className="leading-relaxed"><Inline nodes={b.inline} /></p>;
    case "bullet":
      return (
        <ul className={cn("list-disc space-y-0.5", b.depth ? "ml-6" : "ml-4")}>
          {b.items.map((it, i) => <li key={i}><Inline nodes={it} /></li>)}
        </ul>
      );
    case "number":
      return (
        <ol className={cn("list-decimal space-y-0.5", b.depth ? "ml-6" : "ml-4")}>
          {b.items.map((it, i) => <li key={i}><Inline nodes={it} /></li>)}
        </ol>
      );
    case "fakt":
      return (
        <div className="rounded-lg border border-emerald-300 bg-emerald-50/60 dark:bg-emerald-950/30 px-3 py-2 flex gap-2">
          <Lightbulb className="h-4 w-4 shrink-0 mt-0.5 text-emerald-600" />
          <div className="text-sm min-w-0">
            <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700">Fakt</span>
            <p className="leading-relaxed"><Inline nodes={b.inline} /></p>
          </div>
        </div>
      );
    case "errata":
      return (
        <div className="rounded-lg border border-amber-300 bg-amber-50/60 dark:bg-amber-950/30 px-3 py-2 flex gap-2">
          <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-amber-600" />
          <div className="text-sm min-w-0">
            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700">Errata</span>
            <p className="leading-relaxed"><Inline nodes={b.inline} /></p>
          </div>
        </div>
      );
    case "cols": {
      const n = Math.min(Math.max(b.items.length, 1), 4);
      return (
        <div className={cn("grid gap-2", COLS[n])}>
          {b.items.map((it, i) => (
            <div key={i} className="rounded-md border bg-muted/40 px-2.5 py-2 text-sm">
              <Inline nodes={it} />
            </div>
          ))}
        </div>
      );
    }
    default:
      return null;
  }
}

export function AnswerMarkup({ text }) {
  const blocks = parseAnswer(text);
  return (
    <div className="space-y-2.5 text-sm">
      {blocks.map((b, i) => <Block key={i} b={b} />)}
    </div>
  );
}
```

### Step 3: Create `frontend-2/src/lib/answerMarkup.test.js`

```js
import { test } from "node:test";
import assert from "node:assert/strict";
import { parseAnswer, renderInline, safeHref, MAX_BLOCKS, MAX_NESTING } from "./answerMarkup.js";

test("safeHref allows http/https only", () => {
  assert.equal(safeHref("https://example.com/a?b=1"), "https://example.com/a?b=1");
  assert.equal(safeHref(" http://x.pl/pad "), "http://x.pl/pad");
  for (const evil of [
    "javascript:alert(1)",
    "JAVASCRIPT:alert(1)",
    "java\nscript:alert(1)",
    "javascript%3Aalert(1)",
    "data:text/html;base64,xxx",
    "vbscript:x",
    "&#106;avascript:alert(1)",
  ]) {
    assert.equal(safeHref(evil), null, evil);
  }
});

test("non-http link destinations render as plain text, never a link node", () => {
  const blocks = parseAnswer("zobacz [x](javascript:alert(1)) i [y](data:text/html)");
  const inline = blocks[0].inline;
  assert.ok(inline.every((n) => n.t !== "link"));
  assert.ok(inline.some((n) => n.t === "text" && n.v.includes("javascript:alert(1)")));
});

test("http link becomes a link node with its label", () => {
  const blocks = parseAnswer("zobacz [tutaj](https://example.com)");
  assert.deepEqual(blocks[0].inline.at(-1), {
    t: "link",
    label: "tutaj",
    href: "https://example.com",
  });
});

test("bold pairs become strong; odd `**` degrades to plain text", () => {
  const inline = renderInline("**ważne** ok");
  assert.equal(inline[0].t, "strong");
  assert.ok(renderInline("a ** b").every((n) => n.t === "text"));
});

test("headings, bullets, numbered lists and paragraphs parse", () => {
  const blocks = parseAnswer("## Tytuł\n\n- jeden\n- dwa\n\n1. raz\n2. dwa\n\nTreść akapitu.");
  assert.equal(blocks[0].t, "heading");
  assert.equal(blocks[0].level, 2);
  assert.equal(blocks[1].t, "bullet");
  assert.equal(blocks[1].items.length, 2);
  assert.equal(blocks[2].t, "number");
  assert.equal(blocks[3].t, "para");
});

test("fakt / errata / cols fences parse; unclosed fence degrades to text", () => {
  const b = parseAnswer("```fakt\ncena rośnie\n```\n```cols\nA\nB\nC\n```\n```errata\nstary katalog\n```");
  assert.equal(b[0].t, "fakt");
  assert.equal(b[1].t, "cols");
  assert.equal(b[1].items.length, 3);
  assert.equal(b[2].t, "errata");
  const unclosed = parseAnswer("```fakt\nbez zamknięcia");
  assert.equal(unclosed[0].t, "para");
});

test("nesting depth is capped at MAX_NESTING", () => {
  const b = parseAnswer(" ".repeat(40) + "- x");
  assert.ok(b[0].depth <= MAX_NESTING);
});

test("block count is capped — adversarial input never loops", () => {
  const many = Array.from({ length: MAX_BLOCKS * 4 }, (_, i) => `linia ${i}`).join("\n");
  assert.ok(parseAnswer(many).length <= MAX_BLOCKS);
});
```

### Step 4: `frontend-2/package.json` — test script

Replace:

```json
    "test": "node --test src/lib/access.test.js",
```

with:

```json
    "test": "node --test src/lib/access.test.js src/lib/answerMarkup.test.js",
```

### Step 5: Verify + commit

```bash
cd frontend-2
npm test                 # all tests green (access + answerMarkup)
npm run lint             # oxlint clean
npx vite build           # build passes (unused component is fine — it compiles)
git add src/lib/answerMarkup.js src/lib/answerMarkup.test.js src/components/AnswerMarkup.jsx package.json
git commit -m "feat: hardened answer-markup parser + renderer with security tests"
```

---

## Task 2 — Verified-user name persistence + authHeaders

Files: `frontend-2/src/lib/access.js` (modify), `frontend-2/src/components/AccessGate.jsx` (modify), `frontend-2/src/lib/access.test.js` (modify).

### Step 1: `access.js` — three edits

Edit 1 — after the `GRANT_KEY` line:

```js
const GRANT_KEY = "billszuka.access.v1";
```

add:

```js
const NAME_KEY = "billszuka.access.name.v1";
```

Edit 2 — after `verifyCompany`:

```js
export async function verifyCompany(input) {
  const lists = await loadLists();
  return verify(input, lists.companies);
}
```

add:

```js
export function getName() {
  try { return localStorage.getItem(NAME_KEY) || null; } catch { return null; }
}

export function setName(value) {
  try { localStorage.setItem(NAME_KEY, normalize(value)); } catch { /* private mode */ }
}

/** Header for mutating API calls — the server re-verifies it (spec §6). */
export function authHeaders() {
  const name = getName();
  return name ? { "X-Billszuka-User": name } : {};
}
```

Edit 3 — `revoke()`:

```js
export function revoke() {
  try { localStorage.removeItem(GRANT_KEY); } catch { /* private mode */ }
}
```

becomes:

```js
export function revoke() {
  try {
    localStorage.removeItem(GRANT_KEY);
    localStorage.removeItem(NAME_KEY);
  } catch { /* private mode */ }
}
```

### Step 2: `AccessGate.jsx` — persist the name

Edit 1 — import:

```jsx
import { verifyName, verifyCompany, isGranted, grant, revoke } from "@/lib/access";
```

becomes:

```jsx
import { verifyName, verifyCompany, isGranted, grant, revoke, setName } from "@/lib/access";
```

Edit 2 — after the name passes verification:

```jsx
        setStep("company");
        setValue("");
```

becomes:

```jsx
        setName(v);
        setStep("company");
        setValue("");
```

### Step 3: `access.test.js` — name-persistence tests

Edit 1 — import line:

```js
import { normalize, sha256Hex, verify } from "./access.js";
```

becomes:

```js
import { normalize, sha256Hex, verify, getName, setName, authHeaders, revoke } from "./access.js";
```

Edit 2 — append at the end of the file:

```js
test("name persistence: setName/getName/authHeaders roundtrip, revoke clears", () => {
  globalThis.localStorage = {
    _m: new Map(),
    getItem(k) { return this._m.get(k) ?? null; },
    setItem(k, v) { this._m.set(k, String(v)); },
    removeItem(k) { this._m.delete(k); },
  };
  setName("  Marceli ");
  assert.equal(getName(), "marceli");
  assert.deepEqual(authHeaders(), { "X-Billszuka-User": "marceli" });
  revoke();
  assert.equal(getName(), null);
  assert.deepEqual(authHeaders(), {});
});
```

### Step 4: Verify + commit

```bash
cd frontend-2
npm test && npm run lint
git add src/lib/access.js src/lib/access.test.js src/components/AccessGate.jsx
git commit -m "feat: persist verified user name and send X-Billszuka-User header"
```

## REST POINT A — STOP after Task 2

Groundwork is done and backend-independent (both tasks are green without Phase 1 running). Re-read the diff (`git show HEAD`), take a break, then continue with Task 3. **Do not skip the break** — Tasks 3–4 are the big structural edits.

---

## Task 3 — FaqView.jsx (FAQ catalog inside the drawer)

File: `frontend-2/src/components/FaqView.jsx` (new). Self-contained: fetches `/api/faq`, `/api/faq/session`, `/api/faq/rejects`; calls generate/delete with `authHeaders()`.

### Step 1: Create `frontend-2/src/components/FaqView.jsx`

```jsx
import { useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  ChevronDown,
  Loader2,
  RefreshCw,
  Search,
  Trash2,
  Wand2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AnswerMarkup } from "@/components/AnswerMarkup";
import { authHeaders } from "@/lib/access";
import { toast } from "sonner";

const KIND_BADGE = {
  numeric: { label: "✓ dane", cls: "border-emerald-300 text-emerald-700" },
  judge: { label: "✓ sędzia", cls: "border-blue-300 text-blue-700" },
  manual: { label: "do przeglądu", cls: "border-amber-300 text-amber-700" },
};

function norm(s) {
  return String(s ?? "").toLowerCase().normalize("NFD").replace(/\p{Diacritic}/gu, "");
}

function fmtSources(sources) {
  try {
    const arr = JSON.parse(sources);
    return Array.isArray(arr) ? arr.join(", ") : String(sources);
  } catch {
    return String(sources || "—");
  }
}

export function FaqView() {
  const [data, setData] = useState({ items: [], categories: [], rejects: 0 });
  const [query, setQuery] = useState("");
  const [openIds, setOpenIds] = useState(() => new Set());
  const [loading, setLoading] = useState(true);
  const [session, setSession] = useState({ state: "idle" });
  const [showRejects, setShowRejects] = useState(false);
  const [rejectList, setRejectList] = useState([]);

  const load = async () => {
    try {
      const res = await fetch("/api/faq");
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      setData(await res.json());
    } catch (e) {
      toast.error("Nie udało się pobrać FAQ", { description: String(e.message || e) });
    } finally {
      setLoading(false);
    }
  };

  // Live session state: poll while running, refresh the list when it ends.
  useEffect(() => {
    let timer = null;
    let alive = true;
    const poll = async () => {
      try {
        const res = await fetch("/api/faq/session");
        const s = await res.json();
        if (!alive) return;
        setSession(s);
        if (s.state === "running") timer = setTimeout(poll, 2500);
        else load();
      } catch {
        if (alive) timer = setTimeout(poll, 5000);
      }
    };
    poll();
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, []);

  const generate = async () => {
    try {
      const res = await fetch("/api/faq/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ mode: "full" }),
      });
      const body = await res.json().catch(() => ({}));
      if (res.status === 403) throw new Error("Brak uprawnień — zaloguj się ponownie");
      if (res.status === 409) throw new Error("Sesja FAQ już trwa");
      if (!res.ok) throw new Error(body?.detail || res.statusText);
      toast.success("Sesja FAQ wystartowała. Generowanie w tle…");
      setSession({ state: "running" });
    } catch (e) {
      toast.error("Nie udało się uruchomić sesji", {
        description: String(e.message || e),
      });
    }
  };

  const remove = async (id) => {
    if (!window.confirm("Usunąć to pytanie z FAQ? Trafi na listę odrzuconych.")) return;
    try {
      const res = await fetch(`/api/faq/${encodeURIComponent(id)}`, {
        method: "DELETE",
        headers: authHeaders(),
      });
      const body = await res.json().catch(() => ({}));
      if (res.status === 403) throw new Error("Brak uprawnień");
      if (!res.ok) throw new Error(body?.detail || res.statusText);
      toast.success("Usunięto z FAQ");
      load();
    } catch (e) {
      toast.error("Nie udało się usunąć", { description: String(e.message || e) });
    }
  };

  const toggleRejects = async () => {
    const next = !showRejects;
    setShowRejects(next);
    if (next && rejectList.length === 0) {
      try {
        const res = await fetch("/api/faq/rejects");
        if (!res.ok) throw new Error(`${res.status}`);
        const body = await res.json();
        setRejectList(Array.isArray(body.items) ? body.items : []);
      } catch {
        setRejectList([]);
      }
    }
  };

  const filtered = useMemo(() => {
    const q = norm(query.trim());
    if (!q) return data.items;
    return data.items.filter((it) => norm(it.q).includes(q) || norm(it.a).includes(q));
  }, [data.items, query]);

  const grouped = useMemo(() => {
    const m = new Map();
    for (const it of filtered) {
      const cat = it.category || "inne";
      if (!m.has(cat)) m.set(cat, []);
      m.get(cat).push(it);
    }
    return [...m.entries()];
  }, [filtered]);

  const staleCount = data.items.filter((it) => it.stale).length;
  const running = session.state === "running";

  return (
    <div className="flex-1 min-h-0 flex flex-col">
      <div className="px-5 pt-4 pb-2 space-y-3">
        <div className="flex items-center gap-2">
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Szukaj w FAQ…"
            className="h-8 text-sm"
          />
          <Button variant="ghost" size="icon" className="h-8 w-8" onClick={load} title="Odśwież">
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
        </div>
        {staleCount > 0 && (
          <div className="rounded-md border border-amber-300 bg-amber-50/70 px-3 py-2 text-xs text-amber-800 dark:bg-amber-950/30 dark:text-amber-200">
            ⚠️ {staleCount} odpowiedzi może być nieaktualnych — odśwież sesję FAQ.
          </div>
        )}
        {session.state === "interrupted" && (
          <div className="rounded-md border border-red-300 bg-red-50/70 px-3 py-2 text-xs text-red-800 flex items-center justify-between gap-2 dark:bg-red-950/30 dark:text-red-200">
            <span>Sesja została przerwana.</span>
            <Button size="sm" variant="outline" className="h-7 text-xs" onClick={generate}>
              Wznów
            </Button>
          </div>
        )}
        <div className="flex items-center justify-between gap-2">
          <p className="text-xs text-muted-foreground">
            {data.items.length} pytań
            {data.rejects > 0 && (
              <button onClick={toggleRejects} className="underline ml-1.5 hover:text-foreground">
                {showRejects ? "ukryj odrzucone" : `${data.rejects} odrzuconych`}
              </button>
            )}
          </p>
          <div className="flex items-center gap-2">
            {running && (
              <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" />
                {session.progress || "trwa…"}
              </span>
            )}
            <Button size="sm" onClick={generate} disabled={running} className="h-7 text-xs gap-1">
              <Wand2 className="h-3 w-3" /> Generuj
            </Button>
          </div>
        </div>
      </div>

      <ScrollArea className="flex-1 min-h-0">
        <div className="px-5 pb-4 space-y-4">
          {loading ? (
            <div className="flex items-center justify-center gap-2 py-10 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" /> Ładowanie…
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-10 space-y-2">
              <BookOpen className="h-8 w-8 mx-auto text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground">Brak pytań w FAQ.</p>
              <Button size="sm" variant="outline" onClick={generate} disabled={running}>
                Wygeneruj pierwszą sesję
              </Button>
            </div>
          ) : (
            grouped.map(([cat, items]) => (
              <div key={cat}>
                <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1.5 px-1">
                  {cat}
                </p>
                <div className="space-y-1.5">
                  {items.map((it) => (
                    <FaqEntry
                      key={it.id}
                      item={it}
                      open={openIds.has(it.id)}
                      onToggle={() =>
                        setOpenIds((prev) => {
                          const next = new Set(prev);
                          if (next.has(it.id)) next.delete(it.id);
                          else next.add(it.id);
                          return next;
                        })
                      }
                      onRemove={() => remove(it.id)}
                    />
                  ))}
                </div>
              </div>
            ))
          )}
          {showRejects && (
            <div>
              <p className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1.5 px-1">
                Odrzucone
              </p>
              {rejectList.length === 0 ? (
                <p className="text-xs text-muted-foreground px-1">Brak odrzuconych pytań.</p>
              ) : (
                rejectList.map((r, i) => (
                  <p
                    key={i}
                    className="text-xs text-muted-foreground px-1 py-0.5 truncate"
                    title={r.reason}
                  >
                    {r.q}
                  </p>
                ))
              )}
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

function FaqEntry({ item, open, onToggle, onRemove }) {
  const badge = KIND_BADGE[item.verified_kind] || KIND_BADGE.manual;
  return (
    <div className="rounded-lg border bg-card">
      <button onClick={onToggle} className="w-full flex items-start gap-2 px-3 py-2.5 text-left">
        <ChevronDown
          className={`h-4 w-4 shrink-0 mt-0.5 text-muted-foreground transition-transform ${
            open ? "rotate-180" : ""
          }`}
        />
        <span className="flex-1 min-w-0">
          <span className="text-sm font-medium block">{item.q}</span>
          <span className="flex items-center gap-1.5 mt-1 flex-wrap">
            <Badge variant="outline" className={`text-[10px] h-5 px-1.5 ${badge.cls}`}>
              {badge.label}
            </Badge>
            {item.stale && (
              <Badge
                variant="outline"
                className="text-[10px] h-5 px-1.5 border-amber-300 text-amber-700"
              >
                nieaktualne
              </Badge>
            )}
            <span className="text-[10px] text-muted-foreground">{(item.hits || 0)} trafień</span>
          </span>
        </span>
      </button>
      {open && (
        <div className="px-3 pb-3 border-t">
          <div className="pt-2">
            <AnswerMarkup text={item.a} />
          </div>
          <div className="mt-2 flex items-center justify-between gap-2">
            <span className="text-[10px] text-muted-foreground">
              źródła: {fmtSources(item.sources)}
            </span>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-muted-foreground hover:text-destructive"
              onClick={onRemove}
              title="Usuń z FAQ"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
```

### Step 2: Verify + commit

```bash
cd frontend-2
npm run lint && npx vite build     # compiles; runtime behavior needs Phase 1 backend (smoke later)
git add src/components/FaqView.jsx
git commit -m "feat: FAQ catalog view with search, badges, session polling and delete"
```

---

## Task 4 — GeminiDrawer: view switch, save button, markup, auth header

File: `frontend-2/src/components/GeminiDrawer.jsx` — **full rewrite** (structural change; a diff-based edit would be ambiguous). Preserves all existing behavior (FAB, quick prompts, autoscroll, provider tags, copy, clear).

### Step 1: Overwrite `frontend-2/src/components/GeminiDrawer.jsx`

```jsx
import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
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
  BookmarkPlus,
  ArrowLeft,
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
import { FaqView } from "@/components/FaqView";
import { AnswerMarkup } from "@/components/AnswerMarkup";
import { authHeaders } from "@/lib/access";

/**
 * GeminiDrawer — floating-action-button chat panel for "Gills — twój skowronek".
 * Two views: `chat` (thread + quick prompts) and `faq` (zero-token catalog,
 * opened via the "100 pytań do…" button at the bottom).
 *
 * Backend: POST /api/chat { query, active_dataset, knowledge_ids }
 *   Response: { response, provider }   (provider: faq | save | openrouter | gemini | mock | …)
 *
 * Conversation is in-memory only. Answers render through AnswerMarkup
 * (the XSS-safe light-markup renderer). The "Zapisz do wiedzy" button
 * re-sends the last answer as the zero-token "zapisz ten fakt" command.
 */

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

export function GeminiDrawer({ onOpenSettings, activeDataset, knowledgeIds = [], onSaved }) {
  const [open, setOpen] = useState(false);
  const [view, setView] = useState("chat"); // "chat" | "faq"
  const [messages, setMessages] = useState([]); // [{role: "user"|"assistant", text, provider?}]
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef(null);

  // Mirror knowledgeIds into a ref so send always sees the latest selection.
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

  // Shared POST /api/chat. silent=true skips the user bubble (save command).
  async function postChat(query, { silent = false } = {}) {
    setBusy(true);
    if (!silent) setMessages((m) => [...m, { role: "user", text: query }]);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({
          query,
          active_dataset: activeDataset || "master.csv",
          knowledge_ids: knowledgeIdsRef.current,
        }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body?.detail || res.statusText);
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          text: body.response || "(brak odpowiedzi)",
          provider: body.provider,
        },
      ]);
      return body;
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: `❌ ${e.message || e}`, provider: "error" },
      ]);
      toast.error("Błąd czatu", { description: e.message });
      throw e;
    } finally {
      setBusy(false);
    }
  }

  function sendQuery(q) {
    const text = (q ?? input).trim();
    if (!text || busy) return;
    setInput("");
    postChat(text).catch(() => {});
  }

  // Zero-token save: the server matches "zapisz ten fakt" before any LLM call.
  function saveLastAnswer() {
    if (busy) return;
    postChat("zapisz ten fakt", { silent: true })
      .then(() => onSaved?.())
      .catch(() => {});
  }

  function clearThread() {
    setMessages([]);
    toast.success("Wątek wyczyszczony");
  }

  function copyMsg(text) {
    navigator.clipboard?.writeText(text);
    toast.success("Skopiowano", { duration: 800 });
  }

  const isChat = view === "chat";

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
            aria-label="Otwórz Gills — twój skowronek"
            title="Gills — twój skowronek"
          >
            <Bird className="h-6 w-6" />
          </motion.button>
        </SheetTrigger>
        <SheetContent
          side="right"
          className="w-full sm:max-w-md p-0 flex flex-col gap-0"
        >
          <SheetHeader className="px-5 pt-5 pb-3 border-b">
            <div className="flex items-center justify-between">
              <SheetTitle className="flex items-center gap-2">
                <Bird className="h-5 w-5 text-violet-500" />
                <span>
                  Gills{" "}
                  <span className="text-muted-foreground font-normal text-sm">
                    — twój skowronek
                  </span>
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
              {isChat
                ? "Pytaj o dane w master.csv albo załączone pliki. Gills ćwierka konkretami z bazy wiedzy."
                : "Katalog zweryfikowanych pytań — odpowiedzi bez wydawania tokenów."}
            </SheetDescription>
          </SheetHeader>

          <AnimatePresence mode="wait" initial={false}>
            {isChat ? (
              <motion.div
                key="chat"
                initial={{ x: 0, opacity: 1 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -48, opacity: 0 }}
                transition={{ duration: 0.15 }}
                className="flex-1 min-h-0 flex flex-col"
              >
                {/* Thread */}
                <ScrollArea className="flex-1 px-5 py-3" ref={scrollRef}>
                  {messages.length === 0 ? (
                    <EmptyState onPick={sendQuery} />
                  ) : (
                    <div className="space-y-3">
                      {messages.map((m, i) => (
                        <Bubble key={i} msg={m} onCopy={copyMsg} onSave={saveLastAnswer} />
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

                <ViewSwitch onSwitch={() => setView("faq")} />

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
              </motion.div>
            ) : (
              <motion.div
                key="faq"
                initial={{ x: 48, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: 0, opacity: 0 }}
                transition={{ duration: 0.15 }}
                className="flex-1 min-h-0 flex flex-col"
              >
                <FaqView />
                <ViewSwitch faq onSwitch={() => setView("chat")} />
              </motion.div>
            )}
          </AnimatePresence>
        </SheetContent>
      </Sheet>
    </>
  );
}

function ViewSwitch({ faq = false, onSwitch }) {
  return (
    <div className="border-t px-3 py-2 bg-muted/20 flex justify-center">
      <Button variant="ghost" size="sm" onClick={onSwitch} className="text-xs gap-1.5">
        {faq ? (
          <>
            <ArrowLeft className="h-3.5 w-3.5" /> Wróć do czatu
          </>
        ) : (
          <>
            <BookOpen className="h-3.5 w-3.5 text-violet-500" /> 100 pytań do…
          </>
        )}
      </Button>
    </div>
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
      className={
        "inline-flex items-center gap-1 rounded-full border bg-background text-left " +
        "hover:bg-accent hover:border-violet-300 hover:text-foreground " +
        "disabled:opacity-50 disabled:cursor-not-allowed transition-colors " +
        (compact ? "px-2.5 py-0.5 text-[11px]" : "px-3 py-1.5 text-xs")
      }
    >
      {compact && <Sparkles className="h-2.5 w-2.5 text-violet-500 shrink-0" />}
      <span className="truncate">{q}</span>
    </button>
  );
}

function Bubble({ msg, onCopy, onSave }) {
  const isUser = msg.role === "user";
  const isError = msg.provider === "error";
  const canSave = !isUser && !isError && msg.provider !== "save";
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
        {isUser || isError ? (
          <div className="whitespace-pre-wrap break-words">{msg.text}</div>
        ) : (
          <AnswerMarkup text={msg.text} />
        )}
        {canSave && (
          <Button
            onClick={onSave}
            size="icon"
            variant="ghost"
            className="absolute -top-2 -left-2 h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity bg-background border"
            aria-label="Zapisz do wiedzy"
            title="Zapisz do wiedzy"
          >
            <BookmarkPlus className="h-3 w-3" />
          </Button>
        )}
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
    "mock-gemini-quota": { label: "Mock (limit Gemini)", color: "bg-gray-100 text-gray-700 border-gray-300" },
    faq: { label: "FAQ · 0 tokenów", color: "bg-emerald-100 text-emerald-700 border-emerald-300" },
    save: { label: "Zapisane", color: "bg-teal-100 text-teal-700 border-teal-300" },
    error: { label: "Error", color: "bg-red-100 text-red-700 border-red-300" },
  };
  const base = String(provider).split(" ")[0].replace("(+1file)", "").replace("(+1 file)", "");
  const p = palette[base] || { label: provider, color: "bg-gray-100 text-gray-700 border-gray-300" };
  return (
    <Badge variant="outline" className={`text-[10px] h-5 px-1.5 ${p.color}`}>
      {p.label}
    </Badge>
  );
}
```

### Step 2: Verify + commit

```bash
cd frontend-2
npm run lint && npx vite build
git add src/components/GeminiDrawer.jsx
git commit -m "feat: FAQ view switch, save-to-knowledge button, markup rendering in chat"
```

## REST POINT B — STOP after Task 4

The drawer is now fully wired. Re-read `git diff HEAD~1..HEAD` (Task 4) once, check the animation works in the browser if Phase 1 is up (`npm run dev`, open the FAB, click "100 pytań do…", back to chat). Then a break. Tasks 5–6 are small, but do them in a fresh session.

---

## Task 5 — KnowledgeDrawer: auth headers, uploaded_by badge, extraction offer

File: `frontend-2/src/components/KnowledgeDrawer.jsx` (modify). Five precise edits — re-read the file first; anchors below are from the current version.

### Step 1: Edits

Edit 1 — imports: after the `import { toast } from "sonner";` line add:

```jsx
import { authHeaders } from "@/lib/access";
```

Edit 2 — upload: in `handleFiles`, the fetch:

```js
      const res = await fetch("/api/knowledge/upload", { method: "POST", body: form });
```

becomes:

```js
      const res = await fetch("/api/knowledge/upload", {
        method: "POST",
        headers: authHeaders(), // multipart — never set Content-Type manually
        body: form,
      });
```

and the success toast:

```js
        toast.success(`Wgrano: ${body.filename}`, {
          description: `${(body.size / 1024).toFixed(1)} KB`,
        });
```

becomes:

```js
        toast.success(`Wgrano: ${body.filename}`, {
          description: `${(body.size / 1024).toFixed(1)} KB`,
          action: {
            label: "Generuj pytania",
            onClick: () => generateDocFaq(body.id, body.filename),
          },
        });
```

Edit 3 — delete: in `remove`, the fetch:

```js
      const res = await fetch(`/api/knowledge/${id}`, { method: "DELETE" });
```

becomes:

```js
      const res = await fetch(`/api/knowledge/${id}`, { method: "DELETE", headers: authHeaders() });
```

Edit 4 — refresh: in `refresh`, the fetch:

```js
      const res = await fetch(`/api/knowledge/${id}/refresh`, { method: "POST" });
```

becomes:

```js
      const res = await fetch(`/api/knowledge/${id}/refresh`, {
        method: "POST",
        headers: authHeaders(),
      });
```

Edit 5 — add `generateDocFaq` (after `refresh`, before `toggleSelected`):

```js
  // Doc-scoped FAQ extraction offer — 409-safe against a running session.
  const generateDocFaq = async (docId, filename) => {
    try {
      const res = await fetch("/api/faq/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeaders() },
        body: JSON.stringify({ mode: "doc", doc_id: docId }),
      });
      const body = await res.json().catch(() => ({}));
      if (res.status === 403) throw new Error("Brak uprawnień");
      if (res.status === 409) throw new Error("Inna sesja FAQ już trwa");
      if (!res.ok) throw new Error(body?.detail || res.statusText);
      toast.success(`Generuję pytania z: ${filename}`, {
        description: "Wyniki pojawią się w widoku FAQ (100 pytań do…)",
      });
    } catch (e) {
      toast.error("Nie udało się wygenerować pytań", {
        description: String(e.message || e),
      });
    }
  };
```

Edit 6 — `uploaded_by` badge in `KnowledgeItem`: in the meta row `<p className="text-xs text-muted-foreground flex items-center gap-2 flex-wrap">`, right after the `<span>{formatBytes(item.size || 0)}</span>` add:

```jsx
          {item.uploaded_by && (
            <span className="text-muted-foreground/60">· {item.uploaded_by}</span>
          )}
```

### Step 2: Verify + commit

```bash
cd frontend-2
npm run lint && npx vite build
git add src/components/KnowledgeDrawer.jsx
git commit -m "feat: knowledge drawer auth headers, uploader marking, doc-scoped FAQ offer"
```

---

## Task 6 — App.jsx: pending-inbox badge + wiring

File: `frontend-2/src/App.jsx` (modify). Four precise edits.

### Step 1: Edits

Edit 1 — after the `knowledgeIds` state (line with `const [knowledgeIds, setKnowledgeIds] = useState([]);`) add:

```jsx
  // Pending inbox facts (chat-saved, awaiting review) — badge on the
  // Baza wiedzy button. Refreshed on mount, after saves and drawer close.
  const [pendingCount, setPendingCount] = useState(0);
  const refreshPending = useCallback(async () => {
    try {
      const res = await fetch("/api/knowledge");
      if (!res.ok) return;
      const body = await res.json();
      setPendingCount(body?.inbox_pending || 0);
    } catch {
      /* badge is cosmetic — stay silent */
    }
  }, []);
  useEffect(() => {
    refreshPending();
  }, [refreshPending]);
```

Edit 2 — the Baza wiedzy button: current block:

```jsx
            <BookOpen className="h-4 w-4" />
            {knowledgeIds.length > 0 && (
              <span className="absolute -top-0.5 -right-0.5 h-2 w-2 rounded-full bg-emerald-500 ring-2 ring-background" />
            )}
          </Button>
```

becomes:

```jsx
            <BookOpen className="h-4 w-4" />
            {knowledgeIds.length > 0 && (
              <span className="absolute -bottom-0.5 -right-0.5 h-2 w-2 rounded-full bg-emerald-500 ring-2 ring-background" />
            )}
            {pendingCount > 0 && (
              <span className="absolute -top-1 -right-1 min-w-4 h-4 px-0.5 rounded-full bg-amber-500 text-white text-[9px] font-semibold flex items-center justify-center ring-2 ring-background">
                {pendingCount}
              </span>
            )}
          </Button>
```

Also update the button `title` attribute to mention pending:

```jsx
            title={`Baza wiedzy${knowledgeIds.length ? ` (${knowledgeIds.length} aktywnych)` : ""}`}
```

becomes:

```jsx
            title={`Baza wiedzy${pendingCount ? ` (${pendingCount} do przeglądu)` : ""}${knowledgeIds.length ? ` (${knowledgeIds.length} aktywnych)` : ""}`}
```

Edit 3 — drawer wiring: current lines:

```jsx
      <GeminiDrawer
        onOpenSettings={() => setSettingsOpen(true)}
        activeDataset="master.csv"
        knowledgeIds={knowledgeIds}
      />
      <KnowledgeDrawer
        open={knowledgeOpen}
        onOpenChange={setKnowledgeOpen}
        onSelectionChange={setKnowledgeIds}
      />
```

become:

```jsx
      <GeminiDrawer
        onOpenSettings={() => setSettingsOpen(true)}
        activeDataset="master.csv"
        knowledgeIds={knowledgeIds}
        onSaved={refreshPending}
      />
      <KnowledgeDrawer
        open={knowledgeOpen}
        onOpenChange={(open) => {
          setKnowledgeOpen(open);
          if (!open) refreshPending();
        }}
        onSelectionChange={setKnowledgeIds}
      />
```

### Step 2: Verify + commit

```bash
cd frontend-2
npm run lint && npx vite build
git add src/App.jsx
git commit -m "feat: pending-knowledge badge and drawer refresh wiring"
```

---

## Task 7 — Final verification + smoke test + commit

### Step 1: Automated checks

```bash
cd frontend-2
npm test        # node --test: access + answerMarkup security tests
npm run lint    # oxlint
npx vite build  # production build
cd .. && python3 -m pytest tests/ -q   # backend suite still green (Phase 1)
```

### Step 2: Live smoke checklist (backend + frontend running)

1. Start backend `python3 tools/api_server.py` and frontend `cd frontend-2 && npm run dev`.
2. Log in through AccessGate with a name from `public/access.json` → localStorage has `billszuka.access.name.v1`.
3. Chat: ask `Ile firm jest FROZEN w PL?` → if FAQ has the entry: reply with `FAQ · 0 tokenów` tag. Ask something unmatched → LLM chain reply; hover the bubble → "Zapisz do wiedzy" button (BookmarkPlus, top-left).
   - **Mock-fallback check (regression):** with Gemini quota exhausted (or all keys removed), ask a non-FAQ question → ONE coherent note only — no "OPENROUTER_API_KEY not configured" next to a Gemini-quota note — tag `Mock (limit Gemini)`, and the text points to the FAQ view.
4. Save: click the button → `Zapisano fakt…` bubble with `Zapisane` tag; Baza wiedzy button in the header shows the amber count.
5. FAQ view: "100 pytań do…" button → view slides in; search filters; expand an entry → markup renders (lists, fakt box); `✓ dane`/`✓ sędzia` badges; hits counter; staleness banner if any entry is stale.
6. Generuj: click → session runs (`GET /api/faq/session` shows `running` + progress, button disabled); second click while running → error toast "Sesja FAQ już trwa" (409). After done: list refreshes.
7. Delete an entry → confirm → disappears; the "odrzuconych" counter grows.
8. Knowledge: upload a file → toast with "Generuj pytania" action → doc session starts (or 409 toast if busy); file shows `· marceli` marker.
9. Logout → name key cleared; upload/generate now fail with "Brak uprawnień" (403) until re-login.

### Step 3: Commit plan + wrap

```bash
git add docs/superpowers/plans/
git commit -m "docs: phase 2 frontend plan for Gills FAQ and knowledge drawer"
```

## PHASE 2 END — REST POINT (mandatory stop)

Both phases are now planned. STOP here and ask Marceli: review the smoke results, then decide whether to start executing **Phase 1** (`2026-08-25-gills-faq-phase1-backend.md`) — execution must be task-by-task with the REST POINTs in that plan, and Phase 2 waits for Phase 1's approval.
