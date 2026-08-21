import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Command, CommandInput, CommandList, CommandEmpty, CommandGroup, CommandItem, CommandSeparator } from "@/components/ui/command"
import { ArrowUp, ArrowDown, EyeOff, Eye, X, ListOrdered, Sliders } from "lucide-react"

export function CommandPalette({
  open,
  onOpenChange,
  data,
  prefs,
  onPrefsChange,
  onShowShortcuts,
}) {
  const inputRef = React.useRef(null)
  React.useEffect(() => {
    if (open) {
      const id = setTimeout(() => inputRef.current?.focus(), 20)
      return () => clearTimeout(id)
    }
  }, [open])

  function close() {
    onOpenChange(false)
  }

  function setSort(next) {
    onPrefsChange({ ...prefs, sort: next })
    close()
  }
  function setFilters(next) {
    onPrefsChange({ ...prefs, filters: next })
    close()
  }
  function setColumn(id, patch) {
    onPrefsChange({ ...prefs, columns: { ...(prefs.columns || {}), [id]: { ...(prefs.columns?.[id] || {}), ...patch } } })
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          key="palette"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.12 }}
          className="fixed inset-0 z-50 bg-black/30 backdrop-blur-[2px]"
          onClick={close}
        >
          <motion.div
            initial={{ y: -16, opacity: 0, scale: 0.98 }}
            animate={{ y: 0, opacity: 1, scale: 1 }}
            exit={{ y: -8, opacity: 0, scale: 0.98 }}
            transition={{ duration: 0.16, ease: "easeOut" }}
            className="mx-auto mt-20 w-full max-w-lg overflow-hidden rounded-lg border bg-popover shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <Command shouldFilter>
              <CommandInput ref={inputRef} placeholder="Type a command, column, or action…" />
              <CommandList>
                <CommandEmpty>No results.</CommandEmpty>

                <CommandGroup heading="Sort">
                  <CommandItem
                    value="clear sort"
                    onSelect={() => setSort([])}
                    onClick={() => setSort([])}
                  >
                    <X className="size-4" />
                    <span>Clear sort</span>
                  </CommandItem>
                  {data.columns.slice(0, 8).map((c) => (
                    <React.Fragment key={c.id}>
                      <CommandItem
                        value={`sort ascending ${c.name}`}
                        onSelect={() => setSort([{ colId: c.id, dir: "asc" }])}
                        onClick={() => setSort([{ colId: c.id, dir: "asc" }])}
                      >
                        <ArrowUp className="size-4" />
                        <span>Sort by {c.name} (asc)</span>
                      </CommandItem>
                      <CommandItem
                        value={`sort descending ${c.name}`}
                        onSelect={() => setSort([{ colId: c.id, dir: "desc" }])}
                        onClick={() => setSort([{ colId: c.id, dir: "desc" }])}
                      >
                        <ArrowDown className="size-4" />
                        <span>Sort by {c.name} (desc)</span>
                      </CommandItem>
                    </React.Fragment>
                  ))}
                </CommandGroup>

                <CommandSeparator />

                <CommandGroup heading="Filter">
                  <CommandItem
                    value="clear all filters"
                    onSelect={() => setFilters({})}
                    onClick={() => setFilters({})}
                  >
                    <X className="size-4" />
                    <span>Clear all filters</span>
                  </CommandItem>
                  {data.columns
                    .filter((c) => c.type === "enum" && c.enumValues)
                    .slice(0, 6)
                    .map((c) => (
                      <CommandItem
                        key={c.id}
                        value={`filter ${c.name}`}
                        onSelect={() => setFilters({ [c.id]: c.enumValues })}
                        onClick={() => setFilters({ [c.id]: c.enumValues })}
                      >
                        <Sliders className="size-4" />
                        <span>Filter {c.name} to all values</span>
                      </CommandItem>
                    ))}
                </CommandGroup>

                <CommandSeparator />

                <CommandGroup heading="Columns">
                  <CommandItem
                    value="show all columns"
                    onSelect={() => {
                      const cols = {}
                      for (const c of data.columns) cols[c.id] = { ...(prefs.columns?.[c.id] || {}), visible: true }
                      onPrefsChange({ ...prefs, columns: cols })
                      close()
                    }}
                    onClick={() => {
                      const cols = {}
                      for (const c of data.columns) cols[c.id] = { ...(prefs.columns?.[c.id] || {}), visible: true }
                      onPrefsChange({ ...prefs, columns: cols })
                      close()
                    }}
                  >
                    <Eye className="size-4" />
                    <span>Show all columns</span>
                  </CommandItem>
                  {data.columns.map((c) => {
                    const visible = prefs.columns?.[c.id]?.visible !== false
                    return (
                      <CommandItem
                        key={c.id}
                        value={`${visible ? "hide" : "show"} ${c.name}`}
                        onSelect={() => {
                          setColumn(c.id, { visible: !visible })
                          close()
                        }}
                        onClick={() => {
                          setColumn(c.id, { visible: !visible })
                          close()
                        }}
                      >
                        {visible ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                        <span>
                          {visible ? "Hide" : "Show"} {c.name}
                        </span>
                      </CommandItem>
                    )
                  })}
                </CommandGroup>

                <CommandSeparator />

                <CommandGroup heading="View">
                  <CommandItem
                    value="shortcuts help"
                    onSelect={() => {
                      close()
                      onShowShortcuts?.()
                    }}
                    onClick={() => {
                      close()
                      onShowShortcuts?.()
                    }}
                  >
                    <ListOrdered className="size-4" />
                    <span>Keyboard shortcuts</span>
                  </CommandItem>
                </CommandGroup>
              </CommandList>
            </Command>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
