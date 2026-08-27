import { useState, useEffect } from "react";
import { getSnapshots, saveCustomDataset, setActiveDatasetType } from "@/lib/datasetStorage";
import { savePrefs } from "@/lib/prefs";
import { getActiveProfile } from "@/lib/auth";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Clock, DownloadCloud } from "lucide-react";
import { toast } from "sonner";

export function SnapshotsDialog({ open, onOpenChange, onRestore }) {
  const [snapshots, setSnapshots] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      const profileId = getActiveProfile();
      if (profileId) {
        setLoading(true);
        getSnapshots(profileId).then(data => {
          setSnapshots(data || []);
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
        parseTimeMs: snap.parseTimeMs || 0
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
          <DialogTitle>Historia sesji (Zrzuty)</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          {loading ? (
             <p className="text-sm text-muted-foreground text-center py-4">Ładowanie zrzutów...</p>
          ) : snapshots.length === 0 ? (
             <p className="text-sm text-muted-foreground text-center py-4">Brak zapisanych zrzutów dla tego profilu.</p>
          ) : (
            <div className="grid gap-3">
              {[...snapshots].reverse().map(snap => (
                <div key={snap.id} className="flex items-center justify-between p-3 border rounded-lg bg-card text-card-foreground shadow-sm">
                   <div>
                     <p className="font-medium text-sm flex items-center gap-2">
                       <Clock className="w-4 h-4 text-muted-foreground" />
                       {new Date(snap.timestamp).toLocaleString("pl-PL")}
                     </p>
                     <p className="text-xs text-muted-foreground mt-1">
                       {snap.name} ({Math.round(snap.size / 1024)} KB) - {snap.rows?.length || 0} wierszy
                     </p>
                   </div>
                   <Button variant="outline" size="sm" onClick={() => handleRestore(snap)}>
                      Przywróć
                   </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
