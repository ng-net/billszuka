# frontend-2 (canonical BILLSzuka viewer)

Minimal, raw, mobile-first CSV viewer for BILLSzuka catalogs. Canonical
frontend as of 2026-08-21 — `frontend/` is DEPRECATED, `archive/czat-table/`
is the historical predecessor (do not resurrect).

## Stack

- **Vite + React 19 + Tailwind v4**
- **shadcn/ui** (new-york style, neutral palette)
- **TanStack Table v8** (headless sort/filter/visibility)
- **TanStack Virtual** (row virtualization, mobile)
- **@dnd-kit** (column drag-to-reorder)
- **framer-motion** (FLIP row reflow on sort, spring chips)
- **PapaParse** (worker thread CSV parse)
- **cmdk** (⌘K command palette)
- **sonner** (toast notifications)
- **lucide-react** (icons)

## Run

```bash
cd frontend-2
npm install
npm run dev    # → http://localhost:3001
npm run build  # production build
```

Backend (`tools/api_server.py`) runs on `http://127.0.0.1:8000` and the
Vite dev server proxies `/api/*` to it. See AGENTS.md for the full
startup sequence.

## Views

The app shell (`src/App.jsx`) renders 2 main views and 2 drawers:

| Component | Path / Trigger | Purpose |
|---|---|---|
| `views/TableView.jsx` | `/` (default) | Full CSV grid with sort / filter / visibility |
| `views/AnalyticsView.jsx` | analytics tab | Country + tier breakdowns (KPI cards) |
| `components/SettingsDrawer.jsx` | gear icon (top-right) | Theme, density, LLM API keys (vault) |
| `components/GeminiDrawer.jsx` | chat icon (top-right) | Direct chat against the LLM fallback chain (OpenRouter → Gemini → mock) |

## Table interactions

- **Upload CSV** (file picker or drag-drop) → parse in worker → render
- **Click header** → sort (asc/desc/none, nulls last)
- **Shift-click header** → multi-column sort
- **Right-click header** → context menu (sort / hide / pin left)
- **Drag header** → reorder columns (desktop)
- **Type in filter row** → type-aware filter (text / number range / date range / enum multi-select)
- **Type in global search** → filter all visible columns
- **Click ⚙ Kolumny** → toggle column visibility (hidden-by-default: tiktok, kanal_zamiennik, linkedin, related_to, instagram, marka_wlasna_oem, facebook — see `src/lib/schema.js`)
- **⌘K** → command palette (sort by, hide, density, theme)
- **?** → shortcuts overlay
- **D** → toggle density
- **R** → reset filters + sort
- **↑ ↓** → keyboard row nav
- **Enter** → copy focused cell
- **Esc** → clear focus / close palette

## Persistence (localStorage `czat-table.prefs.v1`)

> The localStorage key is a legacy from the predecessor `czat-table/`
> subproject. Renaming would invalidate existing user settings — keep as-is.

- column order, visibility, widths
- sort stack
- per-column filters
- density (compact / comfortable)
- theme (light / dark / system)
- last focused column

**CSV content is NEVER persisted** — refresh = blank slate by design.

## Hidden columns (2026-08-23)

Seven columns are hidden by default because they are sparsely populated
(<10% fill rate in `data/master.csv`): tiktok, kanal_zamiennik, linkedin,
related_to, instagram, marka_wlasna_oem, facebook. Data is kept on disk —
users can re-enable any column via the column toggle. Configuration lives
in `src/lib/schema.js` (frontend) and `tools/config.py:HIDDEN_COLUMNS`
(backend). Keep them in sync.

## File layout

```
frontend-2/
├── public/
│   └── sample.csv          # copy of data/master.csv for one-click demo
├── src/
│   ├── App.jsx             # 3-tab shell (Table / Analytics / Settings)
│   ├── index.css           # shadcn theme + Inter font
│   ├── main.jsx
│   ├── components/
│   │   ├── ui/             # shadcn-generated
│   │   ├── SettingsDrawer.jsx
│   │   └── GeminiDrawer.jsx
│   ├── hooks/useCsv.js     # parse + progress + cancel + hidden-column filter
│   ├── lib/
│   │   ├── csv.js          # PapaParse + type inference
│   │   ├── schema.js       # HIDDEN_COLUMNS list (mirrors tools/config.py)
│   │   ├── prefs.js        # localStorage v1 schema
│   │   ├── analytics.js
│   │   ├── secretsApi.js   # OpenRouter / Gemini vault proxy
│   │   └── utils.js        # cn(), formatters
│   ├── views/
│   │   ├── TableView.jsx
│   │   └── AnalyticsView.jsx
│   └── raw-table/
│       ├── RawTable.jsx    # top-level shell
│       └── components/
│           ├── DataTable.jsx
│           ├── SortableHeader.jsx
│           ├── FilterInput.jsx
│           ├── CellRenderer.jsx
│           ├── ColumnToggle.jsx
│           ├── StatusBar.jsx
│           ├── CommandPalette.jsx
│           ├── UploadButton.jsx
│           └── EmptyState.jsx
└── package.json
```

## Notes

- 5,000 rows × 35 columns: parse ~100-300ms, virtualized render, sort/filter <50ms
- Default visible columns: 28 (7 hidden by default, see above)
- First 2 columns (`id`, `nazwa_firmy`) are pinned left on mobile
- Type inference: text / number / date / url / email / phone / enum (≤10 unique values)
- Cells: URL → clickable link, email → mailto, phone → tel, date → Polish locale, enum/tier → colored badge
- Click any cell → copy to clipboard (toast)
- Empty cells show `—` (em-dash) in muted color
- Inter font + JetBrains Mono for IDs
