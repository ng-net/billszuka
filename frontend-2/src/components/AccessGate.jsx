import { useState } from "react";
import { Loader2, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { verifyName, verifyCompany, isGranted, grant, revoke } from "@/lib/access";

/**
 * AccessGate — two full-page questions (name → company) before the app.
 * Session lives in localStorage (billszuka.access.v1); logout = the small
 * fixed chip bottom-left. Styling: default shadcn, relaxed layout.
 */
export function AccessGate({ children }) {
  const [granted, setGranted] = useState(() => isGranted());
  const [step, setStep] = useState("name");
  const [value, setValue] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    const v = value.trim();
    if (!v || busy) return;
    setBusy(true);
    setError(null);
    try {
      if (step === "name") {
        const ok = await verifyName(v);
        if (!ok) {
          setError("Nie znamy tego imienia. Spróbuj ponownie.");
          return;
        }
        setStep("company");
        setValue("");
      } else {
        const ok = await verifyCompany(v);
        if (!ok) {
          setError("Nie znamy tej firmy. Spróbuj ponownie.");
          return;
        }
        grant();
        setGranted(true);
      }
    } catch (err) {
      setError(err?.message || String(err));
    } finally {
      setBusy(false);
    }
  }

  function handleLogout() {
    revoke();
    setGranted(false);
    setStep("name");
    setValue("");
    setError(null);
  }

  if (granted) {
    return (
      <>
        {children}
        <button
          onClick={handleLogout}
          className="fixed bottom-4 left-4 z-50 flex items-center gap-2 rounded-full border bg-background/80 px-3 py-1.5 text-xs text-muted-foreground backdrop-blur hover:text-foreground"
          title="Wyloguj"
        >
          <LogOut className="h-3.5 w-3.5" />
          Wyloguj
        </button>
      </>
    );
  }

  const isName = step === "name";
  return (
    <div className="flex min-h-dvh flex-col items-center justify-center bg-background text-foreground px-6">
      <div className="w-full max-w-sm space-y-10 text-center">
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">BILLSzuka</h1>
          <p className="text-[10px] text-muted-foreground">Katalog leadów B2B/B2C</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          <div className="space-y-3">
            <p className="text-sm text-muted-foreground">
              {isName ? "Jak masz na imię?" : "Dla jakiej firmy pracujesz?"}
            </p>
            <Input
              autoFocus
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder={isName ? "Imię" : "Nazwa firmy"}
              disabled={busy}
              className="h-11 text-center"
            />
            {error && <p className="text-xs text-red-600">{error}</p>}
          </div>

          <Button type="submit" disabled={busy || !value.trim()} className="w-full">
            {busy && <Loader2 className="h-4 w-4 animate-spin" />}
            {busy ? "Sprawdzam…" : "Dalej"}
          </Button>
        </form>

        <p className="text-[10px] text-muted-foreground">{isName ? "Krok 1 z 2" : "Krok 2 z 2"}</p>
      </div>
    </div>
  );
}
