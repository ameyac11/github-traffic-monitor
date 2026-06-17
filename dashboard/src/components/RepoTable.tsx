import { useMemo, useState } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import {
  ArrowUpDown,
  Lock,
  Star,
  Eye,
  Download,
  ExternalLink,
  ChevronDown,
  Link2,
  FileText,
} from "lucide-react";
import type { RepoTraffic } from "@/lib/github-api";

type SortKey = "stars" | "views" | "clones";

const COLUMNS: { key: SortKey; label: string; icon: typeof Star }[] = [
  { key: "stars", label: "Stars", icon: Star },
  { key: "views", label: "Views", icon: Eye },
  { key: "clones", label: "Clones", icon: Download },
];

function DailyTrendsChart({ repo }: { repo: RepoTraffic }) {
  const data = useMemo(() => {
    const map = new Map<string, { date: string; views: number; clones: number }>();
    const fmt = (ts: string) => ts.slice(0, 10);
    (repo._daily_views ?? []).forEach((p) => {
      const date = fmt(p.timestamp);
      const e = map.get(date) ?? { date, views: 0, clones: 0 };
      e.views += p.count;
      map.set(date, e);
    });
    (repo._daily_clones ?? []).forEach((p) => {
      const date = fmt(p.timestamp);
      const e = map.get(date) ?? { date, views: 0, clones: 0 };
      e.clones += p.count;
      map.set(date, e);
    });
    return [...map.values()].sort((a, b) => a.date.localeCompare(b.date));
  }, [repo]);

  if (data.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center rounded-lg border border-border/60 text-sm text-muted-foreground">
        No daily trend data available
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
        <defs>
          <linearGradient id="gv" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--chart-1)" stopOpacity={0.5} />
            <stop offset="100%" stopColor="var(--chart-1)" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="gc" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--chart-2)" stopOpacity={0.5} />
            <stop offset="100%" stopColor="var(--chart-2)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
        <XAxis
          dataKey="date"
          tick={{ fill: "var(--muted-foreground)", fontSize: 10 }}
          tickFormatter={(d) => d.slice(5)}
          minTickGap={24}
        />
        <YAxis tick={{ fill: "var(--muted-foreground)", fontSize: 10 }} width={40} />
        <Tooltip
          contentStyle={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
          }}
          labelStyle={{ color: "var(--foreground)" }}
        />
        <Area type="monotone" dataKey="views" name="Views" stroke="var(--chart-1)" fill="url(#gv)" strokeWidth={2} />
        <Area type="monotone" dataKey="clones" name="Clones" stroke="var(--chart-2)" fill="url(#gc)" strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

function MiniTable({
  title,
  icon: Icon,
  head,
  rows,
}: {
  title: string;
  icon: typeof Link2;
  head: [string, string];
  rows: { label: string; sub?: string; count: number; uniques: number }[];
}) {
  return (
    <div className="rounded-lg border border-border/60 bg-background/30">
      <div className="flex items-center gap-2 border-b border-border/60 px-3 py-2 text-xs font-semibold">
        <Icon className="h-3.5 w-3.5 text-primary" />
        {title}
      </div>
      {rows.length === 0 ? (
        <div className="px-3 py-6 text-center text-xs text-muted-foreground">No data available</div>
      ) : (
        <table className="w-full text-xs">
          <thead>
            <tr className="text-left text-muted-foreground">
              <th className="px-3 py-1.5 font-medium">{head[0]}</th>
              <th className="px-3 py-1.5 text-right font-medium">Views</th>
              <th className="px-3 py-1.5 text-right font-medium">Uniques</th>
            </tr>
          </thead>
          <tbody>
            {rows.slice(0, 8).map((r, i) => (
              <tr key={i} className="border-t border-border/40">
                <td className="max-w-[160px] truncate px-3 py-1.5" title={r.label}>
                  {r.label}
                  {r.sub && <span className="ml-1 text-muted-foreground">{r.sub}</span>}
                </td>
                <td className="px-3 py-1.5 text-right tabular-nums">{r.count.toLocaleString()}</td>
                <td className="px-3 py-1.5 text-right tabular-nums text-muted-foreground">
                  {r.uniques.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function RepoRow({ repo, defaultOpen = false }: { repo: RepoTraffic; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <>
      <tr
        onClick={() => setOpen((o) => !o)}
        className="cursor-pointer border-b border-border/60 transition-colors last:border-0 hover:bg-foreground/[0.03]"
      >
        <td className="px-4 py-3">
          <div className="flex items-center gap-2">
            <ChevronDown
              className={`h-4 w-4 shrink-0 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`}
            />
            {repo.is_private && <Lock className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />}
            <a
              href={`https://github.com/${repo.repository}`}
              target="_blank"
              rel="noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="group flex items-center gap-1 font-medium hover:text-primary"
            >
              {repo.repository}
              <ExternalLink className="h-3 w-3 opacity-0 transition-opacity group-hover:opacity-100" />
            </a>
          </div>
        </td>
        <td className="px-4 py-3 text-right tabular-nums text-muted-foreground">
          {repo.stars.toLocaleString()}
        </td>
        <td className="px-4 py-3 text-right tabular-nums text-muted-foreground">
          {repo.views.toLocaleString()}
        </td>
        <td className="px-4 py-3 text-right tabular-nums text-muted-foreground">
          {repo.clones.toLocaleString()}
        </td>
        <td className="hidden px-4 py-3 text-right text-muted-foreground sm:table-cell">
          {repo.top_referrer || "NA"}
        </td>
      </tr>
      {open && (
        <tr className="border-b border-border/60 bg-background/30">
          <td colSpan={5} className="px-4 py-5">
            <div className="animate-slide-up space-y-4">
              <div>
                <h4 className="mb-2 text-xs font-semibold text-muted-foreground">Daily Trends</h4>
                <DailyTrendsChart repo={repo} />
              </div>
              <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
                <MiniTable
                  title="Top Referrers"
                  icon={Link2}
                  head={["Referrer", "Views"]}
                  rows={(repo._referrers ?? []).map((r) => ({
                    label: r.referrer,
                    count: r.count,
                    uniques: r.uniques,
                  }))}
                />
                <MiniTable
                  title="Popular Paths"
                  icon={FileText}
                  head={["Path", "Views"]}
                  rows={(repo._paths ?? []).map((p) => ({
                    label: p.path,
                    sub: p.title,
                    count: p.count,
                    uniques: p.uniques,
                  }))}
                />
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

export function RepoTable({
  repos,
  sortKey,
  dir,
  onSort,
}: {
  repos: RepoTraffic[];
  sortKey: SortKey;
  dir: "asc" | "desc";
  onSort: (k: SortKey) => void;
}) {
  return (
    <div className="glass gradient-border animate-slide-up rounded-xl">
      <div className="border-b border-border p-4">
        <h3 className="text-sm font-semibold">All Repositories</h3>
        <p className="mt-0.5 text-xs text-muted-foreground">Click a row to expand deep-dive analytics</p>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted-foreground">
              <th className="px-4 py-3 font-medium">Repository</th>
              {COLUMNS.map((c) => (
                <th key={c.key} className="px-4 py-3 font-medium">
                  <button
                    onClick={() => onSort(c.key)}
                    className={`ml-auto flex items-center gap-1 transition-colors hover:text-foreground ${
                      sortKey === c.key ? "text-primary" : ""
                    }`}
                  >
                    <c.icon className="h-3.5 w-3.5" />
                    {c.label}
                    <ArrowUpDown className="h-3 w-3 opacity-60" />
                    {sortKey === c.key && <span className="text-[10px]">{dir === "desc" ? "↓" : "↑"}</span>}
                  </button>
                </th>
              ))}
              <th className="hidden px-4 py-3 text-right font-medium sm:table-cell">Top Referrer</th>
            </tr>
          </thead>
          <tbody>
            {repos.map((r, i) => (
              <RepoRow key={r.repository} repo={r} defaultOpen={i === 0} />
            ))}
            {repos.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-10 text-center text-muted-foreground">
                  No repositories match your filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export type { SortKey };
