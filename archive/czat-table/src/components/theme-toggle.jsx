import * as React from "react"
import { Moon, Sun, Monitor } from "lucide-react"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const OPTIONS = [
  { value: "light", label: "Light", Icon: Sun },
  { value: "dark", label: "Dark", Icon: Moon },
  { value: "system", label: "System", Icon: Monitor },
]

/** Theme toggle: 3 options via popover, applies `light` | `dark` | `system`. */
export function ThemeToggle({ theme, onChange }) {
  const [open, setOpen] = React.useState(false)
  const current = OPTIONS.find((o) => o.value === theme) || OPTIONS[2]
  const Icon = current.Icon
  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button type="button" variant="ghost" size="icon" className="size-8" aria-label="Theme">
          <Icon className="size-4" />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-40 p-1">
        {OPTIONS.map(({ value, label, Icon: I }) => (
          <button
            key={value}
            type="button"
            onClick={() => {
              onChange(value)
              setOpen(false)
            }}
            className={cn(
              "flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground",
              theme === value && "bg-accent text-accent-foreground",
            )}
          >
            <I className="size-4 text-muted-foreground" />
            <span>{label}</span>
          </button>
        ))}
      </PopoverContent>
    </Popover>
  )
}

/** Apply theme class to <html> based on preference. */
export function applyTheme(theme) {
  if (typeof document === "undefined") return
  const root = document.documentElement
  const dark = theme === "dark" || (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches)
  root.classList.toggle("dark", dark)
}
