import * as React from "react"
import { Upload } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

/**
 * The "compact" upload button used in the toolbar once data is loaded.
 * For the full empty-state experience, see <Dropzone />.
 */
export const UploadButton = React.forwardRef(function UploadButton(
  { onFile, accept = ".csv,text/csv", className, disabled, children = "Upload CSV", ...props },
  ref,
) {
  const inputRef = React.useRef(null)
  return (
    <>
      <Button
        ref={ref}
        type="button"
        variant="outline"
        size="sm"
        className={cn("gap-2", className)}
        disabled={disabled}
        onClick={() => inputRef.current?.click()}
        {...props}
      >
        <Upload className="size-4" />
        {children}
      </Button>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0]
          if (f) onFile?.(f)
          e.target.value = "" // allow re-selecting the same file
        }}
      />
    </>
  )
})
