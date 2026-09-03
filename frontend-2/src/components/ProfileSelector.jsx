import { useState } from "react";
import { User, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { getAvailableProfiles } from "@/lib/auth";

export function ProfileSelector({ onSelect }) {
  const [profiles] = useState(() => getAvailableProfiles());
  const [customName, setCustomName] = useState("");
  const [isAdding, setIsAdding] = useState(false);

  const handleCustomSubmit = (e) => {
    e.preventDefault();
    if (customName.trim()) {
      onSelect(customName.trim());
    }
  };

  return (
    <div className="flex min-h-dvh items-center justify-center bg-background p-4 sm:p-6 text-foreground safe-y">
      <div className="w-full max-w-md space-y-6 sm:space-y-8 rounded-2xl border border-border bg-card p-5 sm:p-8 shadow-sm">
        <div className="text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-brand-muted">
            <User className="h-6 w-6 text-brand-muted-foreground" />
          </div>
          <h2 className="mt-4 text-xl sm:text-2xl font-bold tracking-tight">Kto teraz korzysta?</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Wybierz swój profil, aby załadować własne ustawienia i filtry.
          </p>
        </div>

        <div className="grid gap-3">
          {profiles.map((p) => (
            <Button
              key={p}
              variant="outline"
              size="lg"
              className="justify-start text-base min-h-[48px] sm:h-14"
              onClick={() => onSelect(p)}
            >
              <User className="mr-3 h-5 w-5 text-muted-foreground" />
              {p}
            </Button>
          ))}

          {!isAdding ? (
            <Button
              variant="ghost"
              size="lg"
              className="justify-start text-base text-muted-foreground min-h-[48px] sm:h-14"
              onClick={() => setIsAdding(true)}
            >
              <Plus className="mr-3 h-5 w-5" />
              Dodaj inny profil...
            </Button>
          ) : (
            <form onSubmit={handleCustomSubmit} className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
              <Input
                autoFocus
                type="text"
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                placeholder="Wpisz imię..."
                className="flex-1"
              />
              <Button type="submit" size="lg" className="sm:h-9">
                Zaloguj
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
