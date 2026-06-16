import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { LogOut, Github, Loader2, AlertCircle, ExternalLink, FileSpreadsheet } from "lucide-react";
import {
  fetchTraffic,
  downloadCsv,
  MAIN_REPO_URL,
  AUTOMATION_REPO_URL,
  type AuthResult,
  type RepoTraffic,
} from "@/lib/github-api";
import { MetricsGrid } from "./MetricsGrid";
import { TrafficCharts } from "./TrafficCharts";
import { RepoTable, type SortKey } from "./RepoTable";
import { CloneLeaderboard } from "./CloneLeaderboard";
import { DashboardToolbar } from "./DashboardToolbar";

const DEFAULT_AVATAR = "https://github.com/octocat.png";

type Source =
  | { mode: "api"; auth: AuthResult; token: string }
  | { mode: "csv"; data: RepoTraffic[] };

export function DashboardView({
  source,
  onLogout,
}: {
  source: Source;
  onLogout: () => void;
}) {
  const isApi = source.mode === "api";

  const query = useQuery({
    queryKey: ["traffic", isApi ? (source as any).auth.username : "csv"],
    queryFn: () => fetchTraffic((source as any).token),
    staleTime: 60_000,
    enabled: isApi,
  });

  const data: RepoTraffic[] = isApi ? (query.data ?? []) : (source as any).data;
  const isLoading = isApi && query.isLoading;
  const isError = isApi && query.isError;

  const [search, setSearch] = useState("");
  const [topN, setTopN] = useState(10);
  const [sortKey, setSortKey] = useState<SortKey>("clones");
  const [dir, setDir] = useState<"asc" | "desc">("desc");

  const filtered = useMemo(() => {
    const f = data.filter((r) => r.repository.toLowerCase().includes(search.toLowerCase()));
    return [...f].sort((a, b) => {
      const av = Number(a[sortKey]) || 0;
      const bv = Number(b[sortKey]) || 0;
      return dir === "desc" ? bv - av : av - bv;
    });
  }, [data, search, sortKey, dir]);

  function toggleSort(key: SortKey) {
    if (key === sortKey) setDir((d) => (d === "desc" ? "asc" : "desc"));
    else {
      setSortKey(key);
      setDir("desc");
    }
  }

  return (
    <div className="min-h-screen">
      <header className="glass sticky top-0 z-10 border-b border-border">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/15 ring-1 ring-primary/30">
              <Github className="h-5 w-5 text-primary" />
            </div>
            <div className="leading-tight">
              <p className="text-sm font-semibold">Gitlytics</p>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
                <a
                  href={MAIN_REPO_URL}
                  target="_blank"
                  rel="noreferrer"
                  className="group flex items-center gap-1 text-muted-foreground transition-colors hover:text-primary"
                >
                  gitlytics
                  <ExternalLink className="h-3 w-3 opacity-50 transition-opacity group-hover:opacity-100" />
                </a>
                <a
                  href={AUTOMATION_REPO_URL}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center gap-1 hover:text-primary"
                >
                  automation
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2.5">
              <img
                src={
                  isApi
                    ? (source as any).auth.avatar_url || DEFAULT_AVATAR
                    : DEFAULT_AVATAR
                }
                alt={isApi ? (source as any).auth.name || (source as any).auth.username : ((source as any).filename || "Demo user")}
                onError={(e) => {
                  (e.currentTarget as HTMLImageElement).src = DEFAULT_AVATAR;
                }}
                className="h-8 w-8 rounded-full ring-1 ring-primary/40"
              />
              <div className="hidden text-right leading-tight sm:block">
                <p className="text-sm font-medium">
                  {isApi ? (source as any).auth.name || (source as any).auth.username : ((source as any).filename || "Demo User")}
                </p>
                <p className="text-xs text-muted-foreground">
                  {isApi ? "@" + (source as any).auth.username : (!(source as any).filename ? "@octocat" : "CSV Upload")}
                </p>
              </div>
              {!isApi && !(source as any).filename && (
                <span className="hidden items-center gap-1.5 rounded-lg bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary ring-1 ring-primary/25 sm:flex">
                  <FileSpreadsheet className="h-3.5 w-3.5" />
                  Demo
                </span>
              )}
            </div>


            <button
              onClick={onLogout}
              className="flex items-center gap-1.5 rounded-lg border border-input bg-background/40 px-3 py-1.5 text-xs font-medium transition-all hover:scale-[1.02] hover:bg-destructive/15 hover:text-destructive"
            >
              <LogOut className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Reset</span>
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-6 px-4 py-6 sm:px-6">
        {isLoading && (
          <div className="flex flex-col items-center justify-center gap-3 py-32 text-muted-foreground">
            <Loader2 className="h-7 w-7 animate-spin text-primary" />
            <p className="text-sm">Loading your traffic data…</p>
          </div>
        )}

        {isError && (
          <div className="glass mx-auto flex max-w-md flex-col items-center gap-3 rounded-xl p-8 text-center">
            <AlertCircle className="h-8 w-8 text-destructive" />
            <p className="text-sm text-muted-foreground">
              {query.error instanceof Error ? query.error.message : "Failed to load data."}
            </p>
            <button
              onClick={() => query.refetch()}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-transform hover:scale-[1.02]"
            >
              Try again
            </button>
          </div>
        )}

        {!isLoading && !isError && data.length > 0 && (
          <>
            <DashboardToolbar
              query={search}
              setQuery={setSearch}
              topN={topN}
              setTopN={setTopN}
              maxN={Math.min(30, filtered.length)}
              onDownload={() => downloadCsv(filtered)}
              onReload={() => query.refetch()}
              reloading={isApi && query.isFetching}
              canReload={isApi}
            />
            <MetricsGrid repos={filtered} />
            <TrafficCharts repos={filtered} topN={topN} />
            <CloneLeaderboard repos={filtered} />
            <RepoTable repos={filtered} sortKey={sortKey} dir={dir} onSort={toggleSort} />
          </>
        )}

        {!isLoading && !isError && data.length === 0 && (
          <div className="glass mx-auto max-w-md rounded-xl p-10 text-center text-muted-foreground">
            No repository traffic data available.
          </div>
        )}
      </main>
    </div>
  );
}
