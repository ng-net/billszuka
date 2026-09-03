import * as React from "react"
import { cva } from "class-variance-authority";
import { Slot } from "radix-ui"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-colors outline-none shadow-xs focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:pointer-events-none disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 active:scale-[0.98] [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm",
        destructive:
          "bg-destructive text-white hover:bg-destructive/90 focus-visible:ring-destructive/20 dark:bg-destructive/60 dark:focus-visible:ring-destructive/40 shadow-sm",
        outline:
          "border border-border bg-background hover:bg-accent hover:text-accent-foreground dark:border-input dark:bg-input/30 dark:hover:bg-input/50",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border/50",
        ghost:
          "shadow-none hover:bg-accent hover:text-accent-foreground dark:hover:bg-accent/50",
        link: "text-primary underline-offset-4 hover:underline shadow-none",
        success:
          "bg-success text-success-foreground hover:bg-success/90 shadow-sm",
        warning:
          "bg-warning text-warning-foreground hover:bg-warning/90 shadow-sm",
        brand:
          "bg-brand text-brand-foreground hover:bg-brand/90 shadow-sm",
      },
      size: {
        default: "h-9 px-4 py-2 has-[>svg]:px-3 sm:h-9",
        xs: "h-8 gap-1 rounded-md px-2 text-xs has-[>svg]:px-1.5 sm:h-6 [&_svg:not([class*='size-'])]:size-3",
        sm: "h-9 gap-1.5 rounded-md px-3 text-xs has-[>svg]:px-2.5 sm:h-8",
        lg: "h-11 rounded-md px-6 has-[>svg]:px-4 sm:h-10",
        xl: "h-12 rounded-lg px-7 text-base has-[>svg]:px-5",
        icon: "size-11 sm:size-9 rounded-md",
        "icon-xs": "size-9 rounded-md sm:size-6 [&_svg:not([class*='size-'])]:size-4 sm:[&_svg:not([class*='size-'])]:size-3",
        "icon-sm": "size-10 rounded-md sm:size-8",
        "icon-lg": "size-12 rounded-md sm:size-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

function Button({
  className,
  variant = "default",
  size = "default",
  asChild = false,
  ...props
}) {
  const Comp = asChild ? Slot.Root : "button"

  return (
    <Comp
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(buttonVariants({ variant, size, className }))}
      {...props} />
  );
}

export { Button }
