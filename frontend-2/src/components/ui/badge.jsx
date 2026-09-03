import * as React from "react"
import { cva } from "class-variance-authority";
import { Slot } from "radix-ui"

import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex w-fit shrink-0 items-center justify-center gap-1 overflow-hidden rounded-full border border-transparent px-2 py-0.5 text-[11px] font-medium whitespace-nowrap transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 aria-invalid:border-destructive aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 [&>svg]:pointer-events-none [&>svg]:size-3 sm:text-xs sm:px-2.5",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground [a&]:hover:bg-primary/90",
        secondary:
          "bg-secondary text-secondary-foreground border-border/40 [a&]:hover:bg-secondary/90",
        destructive:
          "bg-error text-error-foreground focus-visible:ring-error/20 dark:bg-error/60 dark:focus-visible:ring-error/40 [a&]:hover:bg-error/90",
        outline:
          "border-border text-foreground bg-background [a&]:hover:bg-accent [a&]:hover:text-accent-foreground",
        ghost: "bg-transparent [a&]:hover:bg-accent [a&]:hover:text-accent-foreground",
        link: "text-primary underline-offset-4 [a&]:hover:underline",
        success:
          "bg-success-muted text-success-muted-foreground border-success-muted-foreground/20",
        warning:
          "bg-warning-muted text-warning-muted-foreground border-warning-muted-foreground/20",
        error:
          "bg-error-muted text-error-muted-foreground border-error-muted-foreground/20",
        brand:
          "bg-brand-muted text-brand-muted-foreground border-brand-muted-foreground/20",
      },
      size: {
        sm: "px-1.5 py-px text-[10px] [&>svg]:size-2.5",
        default: "",
        lg: "px-2.5 py-1 text-xs [&>svg]:size-3.5",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Badge({
  className,
  variant = "default",
  size = "default",
  asChild = false,
  ...props
}) {
  const Comp = asChild ? Slot.Root : "span"

  return (
    <Comp
      data-slot="badge"
      data-variant={variant}
      className={cn(badgeVariants({ variant, size }), className)}
      {...props} />
  );
}

export { Badge }
