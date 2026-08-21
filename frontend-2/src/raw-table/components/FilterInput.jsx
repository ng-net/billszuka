import { useState, useEffect, useRef } from "react";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Search, X, ChevronDown, Filter as FilterIcon } from "lucide-react";
import { cn, debounce } from "@/lib/utils";
import { Button } from "@/components/ui/button";

/**
 * Type-aware per-column filter.
 * text  → contains input
 * number → two-input range [min, max]
 * date → two date inputs
 * enum → multi-select checkbox list (≤10 values)
 * url/email/phone → contains input
 */
export function FilterInput({ columnId, type, value, onChange, enumValues, placeholder }) {
  if (type === "enum" && enumValues && enumValues.length > 0 && enumValues.length <= 10) {
    return <EnumFilter columnId={columnId} value={value} onChange={onChange} enumValues={enumValues} />;
  }
  if (type === "number") {
    return <NumberRangeFilter columnId={columnId} value={value} onChange={onChange} />;
  }
  if (type === "date") {
    return <DateRangeFilter columnId={columnId} value={value} onChange={onChange} />;
  }
  // default: text contains
  return <TextFilter columnId={columnId} value={value} onChange={onChange} placeholder={placeholder} />;
}

function TextFilter({ columnId, value, onChange, placeholder }) {
  const [local, setLocal] = useState(value || "");
  const debouncedRef = useRef();

  useEffect(() => {
    setLocal(value || "");
  }, [value]);

  useEffect(() => {
    debouncedRef.current = debounce((v) => onChange(v || undefined), 150);
    return () => clearTimeout(debouncedRef.current?.timer);
  }, [onChange]);

  return (
    <div className="relative">
      <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground/50" />
      <Input
        value={local}
        onChange={(e) => {
          setLocal(e.target.value);
          debouncedRef.current?.(e.target.value);
        }}
        placeholder={placeholder || "Filtruj…"}
        className="h-7 pl-7 pr-7 text-xs"
      />
      {local && (
        <button
          onClick={() => {
            setLocal("");
            onChange(undefined);
          }}
          className="absolute right-1.5 top-1/2 -translate-y-1/2 text-muted-foreground/50 hover:text-foreground"
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </div>
  );
}

function NumberRangeFilter({ columnId, value, onChange }) {
  const [min, setMin] = useState(value?.min ?? "");
  const [max, setMax] = useState(value?.max ?? "");
  const debouncedRef = useRef();

  useEffect(() => {
    setMin(value?.min ?? "");
    setMax(value?.max ?? "");
  }, [value]);

  useEffect(() => {
    debouncedRef.current = debounce((mn, mx) => {
      const v = {};
      if (mn !== "" && !isNaN(Number(mn))) v.min = Number(mn);
      if (mx !== "" && !isNaN(Number(mx))) v.max = Number(mx);
      onChange(Object.keys(v).length > 0 ? v : undefined);
    }, 150);
    return () => clearTimeout(debouncedRef.current?.timer);
  }, [onChange]);

  return (
    <div className="flex items-center gap-1">
      <Input
        type="number"
        value={min}
        onChange={(e) => {
          setMin(e.target.value);
          debouncedRef.current?.(e.target.value, max);
        }}
        placeholder="min"
        className="h-7 text-xs tabular-nums px-1.5"
      />
      <span className="text-muted-foreground/50 text-xs">–</span>
      <Input
        type="number"
        value={max}
        onChange={(e) => {
          setMax(e.target.value);
          debouncedRef.current?.(min, e.target.value);
        }}
        placeholder="max"
        className="h-7 text-xs tabular-nums px-1.5"
      />
    </div>
  );
}

function DateRangeFilter({ columnId, value, onChange }) {
  const [from, setFrom] = useState(value?.from ?? "");
  const [to, setTo] = useState(value?.to ?? "");
  const debouncedRef = useRef();

  useEffect(() => {
    setFrom(value?.from ?? "");
    setTo(value?.to ?? "");
  }, [value]);

  useEffect(() => {
    debouncedRef.current = debounce((f, t) => {
      const v = {};
      if (f) v.from = f;
      if (t) v.to = t;
      onChange(Object.keys(v).length > 0 ? v : undefined);
    }, 200);
    return () => clearTimeout(debouncedRef.current?.timer);
  }, [onChange]);

  return (
    <div className="flex items-center gap-1">
      <Input
        type="date"
        value={from}
        onChange={(e) => {
          setFrom(e.target.value);
          debouncedRef.current?.(e.target.value, to);
        }}
        className="h-7 text-xs px-1.5"
      />
      <span className="text-muted-foreground/50 text-xs">–</span>
      <Input
        type="date"
        value={to}
        onChange={(e) => {
          setTo(e.target.value);
          debouncedRef.current?.(from, e.target.value);
        }}
        className="h-7 text-xs px-1.5"
      />
    </div>
  );
}

function EnumFilter({ columnId, value, onChange, enumValues }) {
  const selected = new Set(value || []);
  const [open, setOpen] = useState(false);
  const count = selected.size;

  const toggle = (v) => {
    const next = new Set(selected);
    if (next.has(v)) next.delete(v);
    else next.add(v);
    onChange(next.size > 0 ? Array.from(next) : undefined);
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          className={cn(
            "h-7 w-full px-2 text-xs rounded-md border border-input bg-background hover:bg-muted/50 flex items-center justify-between gap-1 transition-colors",
            count > 0 && "border-primary/50 bg-primary/5"
          )}
        >
          <span className="truncate flex items-center gap-1.5">
            <FilterIcon className="h-3 w-3 opacity-50" />
            {count > 0 ? `${count} / ${enumValues.length}` : "Wszystkie"}
          </span>
          <ChevronDown className="h-3 w-3 opacity-50" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-56 p-2" align="start">
        <div className="space-y-1 max-h-72 overflow-y-auto scrollbar-thin">
          {enumValues.map((v) => (
            <label
              key={v}
              className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-muted/50 cursor-pointer text-xs"
            >
              <Checkbox
                checked={selected.has(v)}
                onCheckedChange={() => toggle(v)}
              />
              <span className="truncate flex-1">{v}</span>
            </label>
          ))}
        </div>
        {count > 0 && (
          <div className="border-t pt-2 mt-2">
            <Button
              variant="ghost"
              size="sm"
              className="w-full h-7 text-xs"
              onClick={() => onChange(undefined)}
            >
              Wyczyść
            </Button>
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}
