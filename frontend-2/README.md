# czat-table

Minimal, raw, mobile-first CSV viewer for BILLSzuka catalogs.

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

## What it does

- **Upload CSV** (file picker or drag-drop) → parse in worker → render
- **Click header** → sort (asc/desc/none, nulls last)
- **Shift-click header** → multi-column sort
- **Right-click header** → context menu (sort / hide / pin left)
- **Drag header** → reorder columns (desktop)
- **Type in filter row** → type-aware filter (text / number range / date range / enum multi-select)
- **Type in global search** → filter all 35 columns
- **Click ⚙ Kolumny** → toggle column visibility
- **⌘K** → command palette (sort by, hide, density, theme)
- **?** → shortcuts overlay
- **D** → toggle density
- **R** → reset filters + sort
- **↑ ↓** → keyboard row nav
- **Enter** → copy focused cell
- **Esc** → clear focus / close palette

## Persistence (localStorage `czat-table.prefs.v1`)

- column order, visibility, widths
- sort stack
- per-column filters
- density (compact / comfortable)
- theme (light / dark / system)
- last focused column

**CSV content is NEVER persisted** — refresh = blank slate by design.

## File layout

```
frontend-2/
├── public/
│   └── sample.csv          # copy of data/master.csv for one-click demo
├── src/
│   ├── App.jsx             # → <RawTable />
│   ├── index.css           # shadcn theme + Inter font
│   ├── main.jsx
│   ├── components/ui/      # shadcn-generated
│   ├── hooks/useCsv.js     # parse + progress + cancel
│   ├── lib/
│   │   ├── csv.js          # PapaParse + type inference
│   │   ├── prefs.js        # localStorage v1 schema
│   │   └── utils.js        # cn(), formatters
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
- First 2 columns (`id_unikalne`, `nazwa_firmy`) are pinned left on mobile
- Type inference: text / number / date / url / email / phone / enum (≤10 unique values)
- Cells: URL → clickable link, email → mailto, phone → tel, date → Polish locale, enum/tier → colored badge
- Click any cell → copy to clipboard (toast)
- Empty cells show `—` (em-dash) in muted color
- Inter font + JetBrains Mono for IDs
