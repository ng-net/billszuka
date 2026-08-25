# LOGIN-RULES.md — BILLSzuka access gate (MVP)

Status: approved 2026-08-25. Frontend-only gate. OAuth + backend
enforcement are LATER (see Security section).

## Access rules

### Names (only these six; case-insensitive, trimmed)
marceli · karol · jarek · jarosław · jaro · jaroslaw

Each variant is its own hash ("jarosław" ≠ "jaroslaw" — both accepted).

### Companies (case-insensitive, any formatting)
bills · smoks
("BILLS", "Bills", "BiLLs", "SMOKS" — all accepted after normalize.)

## Storage & hashing convention
- `frontend-2/public/access.json` — SHA-256 hex hashes ONLY, no plaintext.
  Shape: `{ "names": ["<hex>", ...], "companies": ["<hex>", ...] }`
- Names hashed from `input.trim().toLowerCase()`; companies from the
  same normalization. The gate compares hash(input) against the lists.
- Rationale: a typical user opening DevTools sees only hex — no names.
  A determined attacker can still bypass the check itself (browser must
  be able to pass). That is accepted for the MVP; backend gate later.

## Adding a name (procedure)
1. `python3 tools/hash_name.py <name>` → prints SHA-256 hex
2. Paste hex into `access.json` → `names` array
3. Commit + push (Netlify redeploys automatically). No code rebuild.

## Flow
1. Screen 1 (full page): "Jak masz na imię?" → hash → compare `names`.
   Wrong → error, stay.
2. Screen 2 (full page): "Dla jakiej firmy pracujesz?" → hash →
   compare `companies`. Wrong → error, stay.
3. Grant → main app (Tabela / Analityka).

## Data load after grant
- First page load: auto-load FULL master.csv from backend
  (`/api/master.csv`, raw CSV — endpoint to be added to api_server.py).
- If backend unreachable: auto-fallback to bundled `/sample.csv`.
- If that also fails (or after a refresh with backend still down):
  EmptyState shows the manual "Załaduj master.csv" button.
- Full master.csv must NEVER ship in `public/` — the gate protects
  nothing if the data is a public static file.

## Session
- `localStorage["billszuka.access.v1"] = "granted"` after passing.
- Remembered until explicit logout; logout = small fixed chip rendered
  by the gate component (no header changes).

## Style
- Default shadcn components, no customization ("don't customise shadcn").
- Relaxed intro layout: ample whitespace on both gate screens.
- Strapline stays exactly: "Katalog leadów B2B/B2C".

## Files touched
| File | Change |
|---|---|
| `frontend-2/public/access.json` | NEW — hashed lists |
| `frontend-2/src/lib/access.js` | NEW — fetch + WebCrypto SHA-256 verify |
| `frontend-2/src/components/AccessGate.jsx` | NEW — 2 screens + session + logout chip |
| `frontend-2/src/main.jsx` | EDIT — wrap `<App/>` in `<AccessGate/>` |
| `frontend-2/src/raw-table/RawTable.jsx` | EDIT — boot loader (master → sample → manual) |
| `tools/hash_name.py` | NEW — stdlib SHA-256 printer |
| `design/LOGIN-RULES.md` | NEW — this file |

`App.jsx` intentionally NOT touched (knowledge-agent safety).

## MVP access points (final list)
① Name screen → ② Company screen → ③ master.csv view

## Deferred (later phases)
- `GET /api/master.csv` endpoint consumes no auth today; real protection
  arrives with the backend gate (token/OAuth) + CORS for the Netlify
  domain — see production prep notes.
- OAuth, backend enforcement, per-user roles.
