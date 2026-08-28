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
 * enum → multi-select checkbox list (≤50 values, matches the cap used
 *        by getEnumValues() in lib/csv.js). Columns whose unique set
 *        exceeds 50 fall back to a contains text filter (otherwise the
 *        type label says ENUM but the UI offers no enum UX, which is
 *        confusing).
 * url/email/phone → contains input
 *
 * Local-input state: every input keeps a local string for instant typing
 * and debounces a single onChange upward. We track the last value we
 * emitted so the parent's debounced echo doesn't bounce back into a
 * second setState (which would trigger cascading renders and trip the
 * react(set-state-in-effect) rule).
 */
const ENUM_FILTER_MAX = 50;

const ENUM_DESCRIPTIONS = {
  kategoria: {
    A1: "Tylko PowerMatic (autoryzowani / sub-dystr.)",
    A2: "Tylko Hawk (potencjał dla marki Hawk)",
    A3: "PowerMatic + Hawk (najcenniejsi partnerzy)",
    A4: "Multi-brand z PM/Hawk (resellerzy wielu marek)",
    A5: "Własna marka / OEM z Chin (konkurencja cenowa)",
    A6: "Multi-brand bez PM/Hawk (kandydaci do pozyskania)",
    B1: "Tytoń liście / do skręcania (wysoki cross-sell)",
    B2: "Bibułki papierosowe (palacze skręcający)",
    B3: "Filtry / gilzy (wysokie powinowactwo)",
    B4: "Akcesoria tytoniowe (zapalniczki, fajki)",
    B5: "Shisha / hookah (wspólny kanał retail)",
    B6: "E-papierosy / vape (shared channel)",
    B7: "Saszetki nikotynowe / snus",
    B8: "Pełne hurtownie tytoniowe (najwyższy priorytet)",
    B9: "CBD / konopie / susz (jointy z suszu)",
  },
  kraj: {
    PL: "Polska",
    CZ: "Czechy",
    SK: "Słowacja",
    RO: "Rumunia",
    LT: "Litwa",
    LV: "Łotwa",
    EE: "Estonia",
    FR: "Francja",
    MD: "Mołdawia",
    BG: "Bułgaria",
    SI: "Słowenia",
    HR: "Chorwacja",
    RS: "Serbia (out-of-scope intel)",
  },
  tier: {
    dystrybutor: "Główny importer / dystrybutor",
    hurtownik: "Hurtownia B2B",
    reseller: "Sub-dystrybutor / reseller",
    detalista: "Sklepy detaliczne / stacjonarne",
    sieć: "Sieć salonów / punktów sprzedaży",
  },
  sourcing: {
    "Chiny (import)": "Bezpośredni import z Chin",
    "Polska": "Krajowa dystrybucja",
    "UE": "Dystrybucja unijna",
  },
  wolumen: {
    duży: "Duży wolumen obrotu",
    średni: "Średni wolumen obrotu",
    mały: "Mniejsza skala / detal",
  },
  confidence_wolumen: {
    "🟢": "Wysoka pewność (zweryfikowane)",
    "🟡": "Średnia pewność (szacunki)",
    "🔴": "Niska pewność (do weryfikacji)",
  },
  rynek_skala: {
    duży: "Duży rynek (PL, CZ, FR)",
    średni: "Średni rynek (RO, BG, HR, SI, SK, RS)",
    mały: "Mniejszy rynek (LT, LV, EE, MD)",
  },
};

export function FilterInput({ type, value, onChange, enumValues, placeholder, columnId }) {
  if (type === "enum" && enumValues && enumValues.length > 0 && enumValues.length <= ENUM_FILTER_MAX) {
    return <EnumFilter value={value} onChange={onChange} enumValues={enumValues} columnId={columnId} />;
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
 *
 * `onChange` is captured in a ref so the debounce survives re-renders.
 * Previously `onChange` was a useEffect dep — TextFilter/Number/Date
 * callers pass an inline arrow, which is a new ref every render, so
 * the effect cleanup ran on every keystroke and cancelled the timer
 * before the 150ms elapsed. Filters never fired (prefs.filters stayed
 * `{}`). Now the effect only depends on `ms`, and the ref always holds
 * the latest onChange so the trailing call still reaches the parent.
 */
function useDebouncedEmit(onChange, ms) {
  const debouncedRef = useRef();
  const onChangeRef = useRef(onChange);
  useEffect(() => {
    onChangeRef.current = onChange;
  }, [onChange]);
  const lastEmittedRef = useRef(undefined);
  useEffect(() => {
    debouncedRef.current = debounce((...args) => {
      lastEmittedRef.current = args[0];
      onChangeRef.current(...args);
    }, ms);
    return () => debouncedRef.current?.cancel();
  }, [ms]);
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

function EnumFilter({ value, onChange, enumValues, columnId }) {
  const [selected, setSelected] = useState(() => new Set(value || []));
  const [search, setSearch] = useState("");
  const debouncedRef = useRef();

  useEffect(() => {
    if (!value || value.length === 0) {
      if (selected.size === 0) return;
      setSelected(new Set());
      return;
    }
    const incoming = new Set(value);
    if (incoming.size === selected.size && [...incoming].every((v) => selected.has(v))) return;
    setSelected(incoming);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  useEffect(() => {
    debouncedRef.current = debounce((arr) => onChange(arr.length > 0 ? arr : undefined), 80);
    return () => debouncedRef.current?.cancel();
  }, [onChange]);

  const toggle = (v) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(v)) next.delete(v);
      else next.add(v);
      debouncedRef.current?.([...next]);
      return next;
    });
  };

  const selectAll = () => {
    const all = new Set(enumValues);
    setSelected(all);
    debouncedRef.current?.([...all]);
  };

  const clear = () => {
    setSelected(new Set());
    debouncedRef.current?.([]);
  };

  const count = selected.size;
  const [open, setOpen] = useState(false);
  const descriptions = columnId ? ENUM_DESCRIPTIONS[columnId] : null;

  const filteredEnums = useMemo(() => {
    if (!search.trim()) return enumValues;
    const q = search.trim().toLowerCase();
    return enumValues.filter((v) => {
      const desc = descriptions?.[v] || descriptions?.[String(v).toLowerCase()] || "";
      return String(v).toLowerCase().includes(q) || String(desc).toLowerCase().includes(q);
    });
  }, [enumValues, search, descriptions]);

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          className={cn(
            "h-7 w-full px-2 text-xs rounded-md border border-input bg-background hover:bg-muted/50 flex items-center justify-between gap-1 transition-colors",
            count > 0 && "border-primary/50 bg-primary/10 font-medium text-foreground"
          )}
        >
          <span className="truncate flex items-center gap-1.5">
            <FilterIcon className={cn("h-3 w-3", count > 0 ? "text-primary" : "opacity-50")} />
            {count > 0 ? `${count} / ${enumValues.length}` : "Wszystkie"}
          </span>
          <ChevronDown className="h-3 w-3 opacity-50 shrink-0" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-72 sm:w-80 p-2" align="start">
        {enumValues.length > 6 && (
          <div className="relative mb-2">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3 w-3 text-muted-foreground/50" />
            <Input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Szukaj opcji…"
              className="h-7 pl-7 pr-6 text-xs"
            />
            {search && (
              <button
                onClick={() => setSearch("")}
                className="absolute right-1.5 top-1/2 -translate-y-1/2 text-muted-foreground/50 hover:text-foreground"
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>
        )}
        <div className="space-y-1 max-h-72 overflow-y-auto pr-0.5">
          {filteredEnums.map((v) => {
            const desc = descriptions?.[v] || descriptions?.[String(v).toLowerCase()];
            return (
              <label
                key={v}
                className="flex items-start gap-2.5 px-2 py-1.5 rounded-md hover:bg-muted/60 cursor-pointer text-xs group transition-colors"
              >
                <Checkbox
                  checked={selected.has(v)}
                  onCheckedChange={() => toggle(v)}
                  className="mt-0.5"
                />
                <div className="flex flex-col min-w-0 flex-1 leading-tight">
                  <span className="font-semibold text-foreground">{v}</span>
                  {desc && (
                    <span className="text-[11px] text-muted-foreground/80 mt-0.5 leading-snug">
                      {desc}
                    </span>
                  )}
                </div>
              </label>
            );
          })}
          {filteredEnums.length === 0 && (
            <div className="text-xs text-muted-foreground text-center py-4">
              Brak pasujących opcji
            </div>
          )}
        </div>
        <div className="border-t pt-2 mt-2 flex items-center justify-between gap-2">
          <Button
            variant="ghost"
            size="sm"
            className="h-6 text-[11px] px-2"
            onClick={selectAll}
          >
            Zaznacz wszystkie
          </Button>
          {count > 0 && (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 text-[11px] px-2 text-destructive hover:text-destructive"
              onClick={clear}
            >
              Wyczyść ({count})
            </Button>
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
