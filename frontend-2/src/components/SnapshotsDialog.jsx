import { useState, useEffect } from "react";
import { getSnapshots, saveCustomDataset, setActiveDatasetType } from "@/lib/datasetStorage";
import { savePrefs } from "@/lib/prefs";
import { getActiveProfile } from "@/lib/auth";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Clock, UserCheck, History } from "lucide-react";
import { toast } from "sonner";
import { apiUrl, getAuthHeader } from "@/lib/api";

export function SnapshotsDialog({ open, onOpenChange, onRestore }) {
  const [tab, setTab] = useState("snapshots"); // 'snapshots' | 'logins'
  const [snapshots, setSnapshots] = useState([]);
  const [logins, setLogins] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      const profileId = getActiveProfile();
      if (profileId) {
        setLoading(true);
        Promise.all([
          getSnapshots(profileId),
          fetch(apiUrl("/api/auth/logins"), { headers: getAuthHeader() })
            .then((r) => (r.ok ? r.json() : []))
            .catch(() => []),
        ]).then(([snaps, logs]) => {
          setSnapshots(snaps || []);
          setLogins(logs || []);
          setLoading(false);
        });
      }
    }
  }, [open]);

  const handleRestore = async (snap) => {
    try {
      const profileId = getActiveProfile();
      // Restore prefs
      if (snap.prefs) {
        savePrefs(snap.prefs, profileId);
      }

      // Restore dataset as a custom dataset
      await saveCustomDataset(profileId, {
        name: snap.name,
        size: snap.size,
        rows: snap.rows,
        columns: snap.columns,
        schema: snap.schema,
        parseTimeMs: snap.parseTimeMs || 0,
      });

      // Set active dataset to custom
      await setActiveDatasetType(profileId, "custom", { name: snap.name, size: snap.size });

      toast.success("Przywrócono zrzut tabeli. Odświeżanie...");

      onOpenChange(false);

      // Trigger reload in RawTable
      if (onRestore) onRestore();
      else window.location.reload();
    } catch (e) {
      toast.error("Błąd podczas przywracania zrzutu: " + String(e));
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Historia sesji i logowań</DialogTitle>
        </DialogHeader>

        <div className="flex border-b mb-3 gap-2">
          <button
            onClick={() => setTab("snapshots")}
            className={`pb-2 px-1 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
              tab === "snapshots"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <History className="h-3.5 w-3.5" />
            Zrzuty tabeli ({snapshots.length})
          </button>
          <button
            onClick={() => setTab("logins")}
            className={`pb-2 px-1 text-xs font-medium border-b-2 transition-colors flex items-center gap-1.5 ${
              tab === "logins"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <UserCheck className="h-3.5 w-3.5" />
            Historia logowań ({logins.length})
          </button>
        </div>

        <div className="space-y-4 max-h-[60vh] overflow-y-auto pr-1">
          {loading ? (
            <p className="text-sm text-muted-foreground text-center py-4">Ładowanie...</p>
          ) : tab === "snapshots" ? (
            snapshots.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                Brak zapisanych zrzutów dla tego profilu.
              </p>
            ) : (
              <div className="grid gap-2.5">
                {[...snapshots].reverse().map((snap) => (
                  <div
                    key={snap.id}
                    className="flex items-center justify-between p-3 border rounded-lg bg-card text-card-foreground shadow-sm"
                  >
                    <div>
                      <p className="font-medium text-sm flex items-center gap-2">
                        <Clock className="w-3.5 h-3.5 text-muted-foreground" />
                        {new Date(snap.timestamp).toLocaleString("pl-PL")}
                      </p>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {snap.name} ({Math.round(snap.size / 1024)} KB) · {snap.rows?.length || 0} wierszy
                      </p>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => handleRestore(snap)}>
                      Przywróć
                    </Button>
                  </div>
                ))}
              </div>
            )
          ) : (
            logins.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-4">
                Brak zarejestrowanych logowań w bazie.
              </p>
            ) : (
              <div className="grid gap-2">
                {logins.map((log) => (
                  <div
                    key={log.id}
                    className="flex items-center justify-between p-2.5 border rounded-lg bg-card text-card-foreground shadow-sm text-xs"
                  >
                    <div>
                      <span className="font-semibold capitalize text-foreground">{log.user}</span>
                      {log.company && (
                        <span className="text-muted-foreground ml-1.5 font-normal">({log.company})</span>
                      )}
                    </div>
                    <span className="text-muted-foreground">
                      {new Date(log.login_at).toLocaleString("pl-PL")}
                    </span>
                  </div>
                ))}
              </div>
            )
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
