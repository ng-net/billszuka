import { useState } from "react";
import { User, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
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
    <div className="flex min-h-screen items-center justify-center bg-background p-4 text-foreground">
      <div className="w-full max-w-md space-y-8 rounded-2xl border bg-card p-8 shadow-sm">
        <div className="text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
            <User className="h-6 w-6 text-primary" />
          </div>
          <h2 className="mt-4 text-2xl font-bold tracking-tight">Kto teraz korzysta?</h2>
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
              className="h-14 justify-start text-base"
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
              className="h-14 justify-start text-base text-muted-foreground"
              onClick={() => setIsAdding(true)}
            >
              <Plus className="mr-3 h-5 w-5" />
              Dodaj inny profil...
            </Button>
          ) : (
            <form onSubmit={handleCustomSubmit} className="flex items-center gap-2">
              <input
                autoFocus
                type="text"
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                placeholder="Wpisz imię..."
                className="flex h-12 w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
              />
              <Button type="submit" size="lg" className="h-12">
                Zaloguj
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
