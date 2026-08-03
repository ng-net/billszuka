# BILLSzuka - Pen.dev Design & Workspace Guide

## 🎨 Pen.dev Integration

BILLSzuka integrates **Pen.dev** (`@pen.dev/cli` / `.pen` format) for repository-native UI visual specifications and AI-driven UI design.

### Design Artifacts
- **Primary Design Canvas**: [UI-BILLSzuka-01.pen](file:///Users/apple/Documents/Dev/BILLSzuka/design/UI-BILLSzuka-01.pen)

### Pen.dev CLI Commands
```bash
# 1. Login to Pen.dev / Pencil
pen login  # or set PENCIL_CLI_KEY in .env

# 2. View/Edit design file via CLI
pen --in design/UI-BILLSzuka-01.pen

# 3. Modify UI design using AI prompts
pen --in design/UI-BILLSzuka-01.pen --out design/UI-BILLSzuka-01.pen --prompt "Add dark mode toggle and export buttons"

# 4. Export UI design to image asset
pen --in design/UI-BILLSzuka-01.pen --export public/dashboard_preview.png
```

---

## 🚀 Environment Setup Summary

| Component | Status | Details |
|---|---|---|
| **System OS** | Primary: macOS 13 | Primary machine is macOS 13 (cannot upgrade). Secondary machine available with macOS 15 if needed. |
| **Python Virtual Env** | `venv` Active | `Python 3.14`, `google-genai 2.16.0`, `fastapi`, `duckdb`, `pandas` |
| **FastAPI Backend** | Online on Port 8000 | `/api/health`, `/api/datasets`, `/api/dataset/{filename}`, `/api/chat`, `/api/upload`, `/api/sync` |
| **React Frontend** | Built & Verified | `Vite 5.4`, `Tailwind CSS 4.3`, `Recharts`, `Lucide React` |
| **Gemini AI Integration** | `gemini-2.5-flash` | Operating via `google.genai` SDK with DuckDB fallback |
| **Pen.dev Canvas** | Operational | [UI-BILLSzuka-01.pen](file:///Users/apple/Documents/Dev/BILLSzuka/design/UI-BILLSzuka-01.pen) updated with standard layout components |

---

## 🛠 Next Steps
1. **Develop additional React components** (e.g. detailed charts, filtering options) based on `UI-BILLSzuka-01.pen`.
2. **Expand External Data Sync** (Google Drive folder watcher, Airtable API base connector).
3. **Execute Pen.dev workflows** (`pen --prompt ...`) for rapid UI iteration.
