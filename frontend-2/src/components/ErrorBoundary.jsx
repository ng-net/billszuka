import { Component } from "react";
import { AlertCircle, RefreshCw, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, copied: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
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
      return (
        <div className="flex h-full w-full items-center justify-center p-6 bg-background text-foreground">
          <div className="max-w-md w-full rounded-xl border border-destructive/30 bg-destructive/5 p-6 text-center shadow-lg space-y-4">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10 text-destructive">
              <AlertCircle className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-foreground">Wystąpił nieoczekiwany błąd widoku</h2>
              <p className="mt-1 text-xs text-muted-foreground">
                Aplikacja napotkała problem podczas renderowania. Dane nie zostały utracone.
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
