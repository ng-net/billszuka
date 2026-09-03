import { Component } from "react";
import { AlertCircle, RefreshCw, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";

// Detect the transient dynamic-import failure that happens when Vite
// re-optimizes dependencies mid-session. The browser keeps a cached chunk
// URL (?v=...) but the server is mid-bundle, so the fetch fails. Retry
// once after a short delay — Vite finishes re-optimizing in <1s in
// practice, so 1.5s is comfortably safe.
const isTransientChunkError = (error) => {
  const msg = error?.message || String(error);
  return (
    msg.includes("Failed to fetch dynamically imported module") ||
    msg.includes("Importing a module script failed")
  );
};

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this._reloadTimer = null;
    this._countdownInterval = null;
    this.state = { hasError: false, error: null, copied: false, retried: false, countdownMs: 0 };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);

    // Auto-recover from a transient chunk-load failure (Vite reoptimize).
    // One retry only — keeps the user on the broken UI long enough to
    // read the error if the real cause is something else.
    if (
      !this.state.retried &&
      isTransientChunkError(error) &&
      typeof window !== "undefined"
    ) {
      this.setState({ retried: true });
      setTimeout(() => window.location.reload(), 1500);
    }
  }

  handleCopy = () => {
    const errorText = `${this.state.error?.name || "Error"}: ${this.state.error?.message || "Unknown"}\n\nStack:\n${this.state.error?.stack || "No stack trace available"}`;
    navigator.clipboard?.writeText(errorText);
    this.setState({ copied: true });
    setTimeout(() => this.setState({ copied: false }), 2000);
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const autoRecovering = this.state.retried && isTransientChunkError(this.state.error);
      const secs = (this.state.countdownMs / 1000).toFixed(1);
      return (
        <div className="flex h-full w-full items-center justify-center p-6 bg-background text-foreground">
          <div className="max-w-md w-full rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-center shadow-lg space-y-4">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10 text-destructive">
              <AlertCircle className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-foreground">
                {autoRecovering ? "Vite przeładowuje zależności…" : "Wystąpił nieoczekiwany błąd widoku"}
              </h2>
              <p className="mt-1 text-xs text-muted-foreground">
                {autoRecovering
                  ? `Strona odświeży się automatycznie za ${secs}s. To normalne przy pierwszym załadowaniu po zmianie konfiguracji.`
                  : "Aplikacja napotkała problem podczas renderowania. Dane nie zostały utracone."}
              </p>
            </div>
            {this.state.error && (
              <div className="rounded-md bg-muted/60 p-3 text-left font-mono text-[11px] text-destructive overflow-auto max-h-28 whitespace-pre-wrap break-all border border-border/50">
                {this.state.error.toString()}
              </div>
            )}
            <div className="flex items-center justify-center gap-3 pt-2">
              <Button size="sm" variant="outline" onClick={this.handleCopy} className="text-xs h-8">
                {this.state.copied ? <Check className="mr-1.5 h-3.5 w-3.5 text-green-600" /> : <Copy className="mr-1.5 h-3.5 w-3.5" />}
                {this.state.copied ? "Skopiowano" : "Kopiuj błąd"}
              </Button>
              <Button size="sm" onClick={this.handleReload} className="text-xs h-8">
                <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
                Odśwież stronę
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
