import { Eye, Users, GitFork, Star, Download, FolderGit2, type LucideIcon } from "lucide-react";
import type { RepoTraffic } from "@/lib/github-api";

function formatNum(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "k";
  return n.toString();
}

interface Metric {
  label: string;
  value: number;
  icon: LucideIcon;
  tint: string;
}

export function MetricsGrid({ repos }: { repos: RepoTraffic[] }) {
  const sum = (key: keyof RepoTraffic) =>
    repos.reduce((acc, r) => acc + (Number(r[key]) || 0), 0);

  const metrics: Metric[] = [
    { label: "Repositories", value: repos.length, icon: FolderGit2, tint: "text-primary" },
    { label: "Total Views", value: sum("views"), icon: Eye, tint: "text-chart-1" },
    { label: "Unique Visitors", value: sum("unique_visitors"), icon: Users, tint: "text-chart-4" },
    { label: "Total Clones", value: sum("clones"), icon: Download, tint: "text-success" },
    { label: "Total Stars", value: sum("stars"), icon: Star, tint: "text-chart-3" },
    { label: "Total Forks", value: sum("forks"), icon: GitFork, tint: "text-chart-5" },
  ];

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
      {metrics.map((m, i) => (
        <div
          key={m.label}
          style={{ animationDelay: `${i * 60}ms` }}
          className="glass gradient-border animate-slide-up group rounded-xl p-4 transition-all duration-300 hover:-translate-y-1 hover:border-primary/40"
        >
          <div className="mb-3 flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">{m.label}</span>
            <m.icon className={`h-4 w-4 ${m.tint} transition-transform group-hover:scale-110`} />
          </div>
          <div className="text-2xl font-semibold tracking-tight">{formatNum(m.value)}</div>
        </div>
      ))}
    </div>
  );
}
