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
 * enum → multi-select checkbox list (≤15 values, matches the inference
 *        threshold in lib/csv.js — columns with more values fall back
 *        to a contains text filter, otherwise the type label says ENUM
 *        but the UI offers no enum UX, which is confusing)
 * url/email/phone → contains input
 *
 * Local-input state: every input keeps a local string for instant typing
 * and debounces a single onChange upward. We track the last value we
 * emitted so the parent's debounced echo doesn't bounce back into a
 * second setState (which would trigger cascading renders and trip the
 * react(set-state-in-effect) rule).
 */
const ENUM_FILTER_MAX = 15;

export function FilterInput({ type, value, onChange, enumValues, placeholder }) {
  if (type === "enum" && enumValues && enumValues.length > 0 && enumValues.length <= ENUM_FILTER_MAX) {
    return <EnumFilter value={value} onChange={onChange} enumValues={enumValues} />;
  }
  if (type === "number") {
    return <NumberRangeFilter value={value} onChange={onChange} />;
  }
  if (type === "date") {
    return <DateRangeFilter value={value} onChange={onChange} />;
  }
  return <TextFilter value={value} onChange={onChange} placeholder={placeholder} />;
}

/**
 * Helper: emit a value upward through a debounce, recording it so
 * the parent's echo is recognised and ignored.
 */
function useDebouncedEmit(onChange, ms) {
  const debouncedRef = useRef();
  const lastEmittedRef = useRef(undefined);
  useEffect(() => {
    debouncedRef.current = debounce((...args) => {
      lastEmittedRef.current = args[0];
      onChange(...args);
    }, ms);
    return () => debouncedRef.current?.cancel();
  }, [onChange, ms]);
  return { emit: (...args) => debouncedRef.current?.(...args), lastEmitted: lastEmittedRef };
}

function isIncomingEcho(incoming, lastEmitted) {
  if (incoming == null) return false;
  if (typeof incoming === "string") return incoming === lastEmitted;
  // For {min,max} and {from,to} — deep-compare the relevant fields
  return JSON.stringify(incoming) === JSON.stringify(lastEmitted);
}

function TextFilter({ value, onChange, placeholder }) {
  const [local, setLocal] = useState(value || "");
  const { emit, lastEmitted } = useDebouncedEmit(
    (v) => onChange(v || undefined),
    150
  );

  // Sync from parent only when the incoming value isn't the echo of
  // our own emit. Skipping the echo avoids a redundant re-render.
  useEffect(() => {
    if (!isIncomingEcho(value, lastEmitted.current)) {
      setLocal(value || "");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <div className="relative">
      <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground/50" />
      <Input
        value={local}
        onChange={(e) => {
          setLocal(e.target.value);
          emit(e.target.value);
        }}
        placeholder={placeholder || "Filtruj…"}
        className="h-7 pl-7 pr-7 text-xs"
      />
      {local && (
        <button
          onClick={() => {
            setLocal("");
            emit("");
          }}
          className="absolute right-1.5 top-1/2 -translate-y-1/2 text-muted-foreground/50 hover:text-foreground"
        >
          <X className="h-3 w-3" />
        </button>
      )}
    </div>
  );
}

function NumberRangeFilter({ value, onChange }) {
  const [min, setMin] = useState(value?.min ?? "");
  const [max, setMax] = useState(value?.max ?? "");
  const { emit, lastEmitted } = useDebouncedEmit(
    (mn, mx) => {
      const v = {};
      if (mn !== "" && !isNaN(Number(mn))) v.min = Number(mn);
      if (mx !== "" && !isNaN(Number(mx))) v.max = Number(mx);
      onChange(Object.keys(v).length > 0 ? v : undefined);
    },
    150
  );

  useEffect(() => {
    if (!isIncomingEcho(value, lastEmitted.current)) {
      setMin(value?.min ?? "");
      setMax(value?.max ?? "");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <div className="flex items-center gap-1">
      <Input
        type="number"
        value={min}
        onChange={(e) => {
          setMin(e.target.value);
          emit(e.target.value, max);
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
          emit(min, e.target.value);
        }}
        placeholder="max"
        className="h-7 text-xs tabular-nums px-1.5"
      />
    </div>
  );
}

function DateRangeFilter({ value, onChange }) {
  const [from, setFrom] = useState(value?.from ?? "");
  const [to, setTo] = useState(value?.to ?? "");
  const { emit, lastEmitted } = useDebouncedEmit(
    (f, t) => {
      const v = {};
      if (f) v.from = f;
      if (t) v.to = t;
      onChange(Object.keys(v).length > 0 ? v : undefined);
    },
    200
  );

  useEffect(() => {
    if (!isIncomingEcho(value, lastEmitted.current)) {
      setFrom(value?.from ?? "");
      setTo(value?.to ?? "");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <div className="flex items-center gap-1">
      <Input
        type="date"
        value={from}
        onChange={(e) => {
          setFrom(e.target.value);
          emit(e.target.value, to);
        }}
        className="h-7 text-xs px-1.5"
      />
      <span className="text-muted-foreground/50 text-xs">–</span>
      <Input
        type="date"
        value={to}
        onChange={(e) => {
          setTo(e.target.value);
          emit(from, e.target.value);
        }}
        className="h-7 text-xs px-1.5"
      />
    </div>
  );
}

function EnumFilter({ value, onChange, enumValues }) {
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
