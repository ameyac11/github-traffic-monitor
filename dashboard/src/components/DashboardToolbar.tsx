import { Search, Download, RefreshCw, SlidersHorizontal } from "lucide-react";

export function DashboardToolbar({
  query,
  setQuery,
  topN,
  setTopN,
  maxN,
  onDownload,
  onReload,
  reloading,
  canReload,
}: {
  query: string;
  setQuery: (v: string) => void;
  topN: number;
  setTopN: (v: number) => void;
  maxN: number;
  onDownload: () => void;
  onReload: () => void;
  reloading: boolean;
  canReload: boolean;
}) {
  return (
    <div className="glass gradient-border animate-slide-up flex flex-col gap-4 rounded-xl p-4 lg:flex-row lg:items-center lg:justify-between">
      <div className="relative w-full lg:max-w-xs">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Filter repositories…"
          className="w-full rounded-lg border border-input bg-background/60 py-2 pl-9 pr-3 text-sm outline-none transition-colors placeholder:text-muted-foreground/60 focus:border-primary focus:ring-2 focus:ring-primary/30"
        />
      </div>

      <div className="flex items-center gap-2.5">
        <SlidersHorizontal className="h-4 w-4 text-muted-foreground" />
        <span className="whitespace-nowrap text-xs text-muted-foreground">Top N</span>
        <input
          type="range"
          min={1}
          max={Math.max(maxN, 1)}
          value={Math.min(topN, Math.max(maxN, 1))}
          onChange={(e) => setTopN(Number(e.target.value))}
          className="h-1.5 w-40 cursor-pointer appearance-none rounded-full bg-border accent-primary"
        />
        <span className="w-8 text-center text-sm font-semibold tabular-nums text-primary">{topN}</span>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onDownload}
          className="flex items-center gap-1.5 rounded-lg border border-input bg-background/40 px-3 py-2 text-xs font-medium transition-all hover:scale-[1.02] hover:bg-foreground/5"
        >
          <Download className="h-3.5 w-3.5" />
          Download CSV
        </button>
        {canReload && (
          <button
            onClick={onReload}
            disabled={reloading}
            className="flex items-center gap-1.5 rounded-lg border border-input bg-background/40 px-3 py-2 text-xs font-medium transition-all hover:scale-[1.02] hover:bg-foreground/5 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${reloading ? "animate-spin" : ""}`} />
            Reload
          </button>
        )}
      </div>
    </div>
  );
}
