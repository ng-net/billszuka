import * as React from "react"
import { Toaster, toast } from "sonner"
import { parseCsvFile } from "@/lib/csv"
import { loadSample, SAMPLE_NAME, SAMPLE_SIZE } from "@/lib/sample"
import { loadPrefs, savePrefs, resetPrefs } from "@/lib/persist"
import { applyTheme } from "@/components/theme-toggle"
import { Dropzone } from "@/components/dropzone"
import { Toolbar } from "@/components/toolbar"
import { DataTable } from "@/components/data-table"
import { StatusBar } from "@/components/status-bar"
import { CommandPalette } from "@/components/command-palette"
import { ShortcutsOverlay } from "@/components/shortcuts-overlay"
import { TooltipProvider } from "@/components/ui/tooltip"

export default function App() {
  // Dataset state
  const [data, setData] = React.useState(null)
  // Prefs (theme, density, columns, sort, filters)
  const [prefs, setPrefs] = React.useState(() => loadPrefs())
  // UX state
  const [progress, setProgress] = React.useState(null)
  const [error, setError] = React.useState(null)
  const [busy, setBusy] = React.useState(false)
  const [paletteOpen, setPaletteOpen] = React.useState(false)
  const [shortcutsOpen, setShortcutsOpen] = React.useState(false)
  const [paginationInfo, setPaginationInfo] = React.useState({
    page: 1,
    perPage: 100,
    totalPages: 1,
    totalRows: 0,
    pageStart: 0,
    pageEnd: 0,
  })
  // Refs to data-table scroll for toolbar auto-hide
  const scrollRef = React.useRef(null)

  // Persist prefs whenever they change (only the persisted slice)
  React.useEffect(() => {
    savePrefs(prefs)
  }, [prefs])

  // Apply theme
  React.useEffect(() => {
    applyTheme(prefs.theme)
    if (prefs.theme !== "system") return
    const mq = window.matchMedia("(prefers-color-scheme: dark)")
    const cb = () => applyTheme("system")
    mq.addEventListener("change", cb)
    return () => mq.removeEventListener("change", cb)
  }, [prefs.theme])

  // File handling
  async function handleFile(file) {
    setError(null)
    setBusy(true)
    setProgress(0)
    try {
      const out = await parseCsvFile(file, { onProgress: setProgress })
      setData(out)
      toast.success(`Loaded ${out.rows.length.toLocaleString()} rows · ${out.columns.length} columns`, {
        description: file.name,
      })
      for (const w of out.warnings || []) {
        toast.warning("Possible data issue", { description: w, duration: 8000 })
      }
    } catch (e) {
      const msg = e?.message || "Failed to parse CSV"
      setError(msg)
      toast.error("Could not load CSV", { description: msg })
    } finally {
      setBusy(false)
      setTimeout(() => setProgress(null), 400)
    }
  }

  async function handleSample() {
    setError(null)
    setBusy(true)
    setProgress(0)
    try {
      const out = await loadSample({ onProgress: setProgress })
      setData(out)
      toast.success(`Loaded ${out.rows.length.toLocaleString()} rows · ${out.columns.length} columns`, {
        description: SAMPLE_NAME,
      })
      for (const w of out.warnings || []) {
        toast.warning("Possible data issue", { description: w, duration: 8000 })
      }
    } catch (e) {
      const msg = e?.message || "Failed to load sample"
      setError(msg)
      toast.error("Could not load sample", { description: msg })
    } finally {
      setBusy(false)
      setTimeout(() => setProgress(null), 400)
    }
  }

  // Global keyboard shortcuts
  React.useEffect(() => {
    function onKey(e) {
      const isMod = e.metaKey || e.ctrlKey
      // Cmd+K → command palette
      if (isMod && e.key.toLowerCase() === "k") {
        if (!data) return
        e.preventDefault()
        setPaletteOpen((v) => !v)
        return
      }
      // ? → shortcuts (when not typing in an input)
      if (e.key === "?" && !isMod && !isTyping(e.target)) {
        e.preventDefault()
        setShortcutsOpen(true)
        return
      }
      // Esc → close dialogs or clear focused filter
      if (e.key === "Escape") {
        if (shortcutsOpen) {
          setShortcutsOpen(false)
          e.preventDefault()
          return
        }
        if (paletteOpen) {
          setPaletteOpen(false)
          e.preventDefault()
          return
        }
        // Clear focused filter input
        if (e.target instanceof HTMLInputElement) {
          e.target.value = ""
          e.target.dispatchEvent(new Event("input", { bubbles: true }))
        }
      }
    }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [data, paletteOpen, shortcutsOpen])

  // Cell-copy toast
  function onCopy({ value, colId, rowIndex }) {
    const colName = data?.columns.find((c) => c.id === colId)?.name ?? colId
    toast.success("Copied", { description: `${colName}: ${value.length > 60 ? value.slice(0, 60) + "…" : value}` })
  }

  // Empty state vs data state
  return (
    <TooltipProvider delayDuration={300}>
      <div className="flex h-full w-full flex-col bg-background text-foreground">
      {data ? (
        <>
          <Toolbar
            data={data}
            prefs={prefs}
            onFile={handleFile}
            onPrefsChange={setPrefs}
            onShowShortcuts={() => setShortcutsOpen(true)}
            onShowSampleInfo={() =>
              toast(`${data.rows.length.toLocaleString()} rows in current view`, {
                description: `${data.columns.length} columns · parsed in ${(data.parseMs / 1000).toFixed(2)}s`,
              })
            }
          />
          <main className="min-h-0 flex-1">
            <DataTable
              ref={scrollRef}
              data={data}
              prefs={prefs}
              onPrefsChange={setPrefs}
              onCopy={onCopy}
              onPaginationChange={setPaginationInfo}
            />
          </main>
          <StatusBar
            parseMs={data.parseMs}
            columnCount={data.columns.length}
            density={prefs.density}
            onToggleDensity={() => setPrefs({ ...prefs, density: prefs.density === "compact" ? "comfortable" : "compact" })}
            pagination={paginationInfo}
            onChangePage={(page) => setPrefs({ ...prefs, pagination: { ...(prefs.pagination || {}), page } })}
            onChangePerPage={(perPage) => setPrefs({ ...prefs, pagination: { ...(prefs.pagination || {}), perPage, page: 1 } })}
          />
        </>
      ) : (
        <main className="flex h-full w-full items-center justify-center p-6">
          <div className="w-full max-w-xl">
            <Dropzone
              onFile={handleFile}
              onTrySample={handleSample}
              progress={progress}
              error={error}
              busy={busy}
            />
            <p className="mt-3 text-center text-xs text-muted-foreground">
              {SAMPLE_NAME} · {(SAMPLE_SIZE / 1024).toFixed(0)} KB bundled · all processing happens locally in your browser
            </p>
          </div>
        </main>
      )}

      {data && (
        <CommandPalette
          open={paletteOpen}
          onOpenChange={setPaletteOpen}
          data={data}
          prefs={prefs}
          onPrefsChange={setPrefs}
          onShowShortcuts={() => setShortcutsOpen(true)}
        />
      )}

      <ShortcutsOverlay open={shortcutsOpen} onClose={() => setShortcutsOpen(false)} />
      <Toaster position="bottom-right" richColors closeButton theme="system" />
      </div>
    </TooltipProvider>
  )
}

function isTyping(el) {
  if (!el) return false
  const tag = (el.tagName || "").toLowerCase()
  return tag === "input" || tag === "textarea" || el.isContentEditable
}
