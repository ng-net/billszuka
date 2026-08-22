# DEPRECATED — `frontend/`

This subdirectory is **archived**. It was the first React/Vite prototype for the
BILLSzuka Dashboard and was superseded on **2026-08-22** by `frontend-2/`.

## Why archived

- `frontend-2/` adds: 3-view shell (Tabela | Analityka), AnalyticsView with
  recharts, GeminiDrawer (multi-provider chat), SettingsDrawer (API key
  management), proper vite proxy to the backend, and shadcn/ui primitives.
- `frontend/` is a single-page CSV dropzone with no analytics, no chat, no
  settings. Its features are a strict subset of `frontend-2/`.

## Where to go instead

- **All development**: use `frontend-2/`
  ```sh
  cd frontend-2 && npm run dev    # http://localhost:3001
  ```
- **Backend**: `tools/api_server.py` (already wired for both frontends via
  CORS for ports 3000/3001).

## If you need to resurrect something from here

- All assets (components, styles, package.json) are still on disk.
- Don't resurrect the *project structure* — port any needed component to
  `frontend-2/` instead.

## Do not run

- `cd frontend && npm run dev` — it will conflict with `frontend-2/` on
  port 3001 (or take port 3000 silently).