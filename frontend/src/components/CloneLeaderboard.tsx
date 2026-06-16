import { Download, ExternalLink, Lock, Trophy } from "lucide-react";
import type { RepoTraffic } from "@/lib/github-api";

export function CloneLeaderboard({ repos }: { repos: RepoTraffic[] }) {
  const ranked = [...repos]
    .sort((a, b) => (Number(b.clones) || 0) - (Number(a.clones) || 0))
    .slice(0, 10);

  return (
    <div className="glass gradient-border animate-slide-up rounded-xl">
      <div className="flex items-center gap-2 border-b border-border p-4">
        <Download className="h-4 w-4 text-primary" />
        <div>
          <h3 className="text-sm font-semibold">Most Cloned Repositories</h3>
          <p className="mt-0.5 text-xs text-muted-foreground">Ranked by total clones</p>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted-foreground">
              <th className="px-4 py-3 font-medium">#</th>
              <th className="px-4 py-3 font-medium">Repository</th>
              <th className="px-4 py-3 text-right font-medium">Clones</th>
              <th className="px-4 py-3 text-right font-medium">Unique Cloners</th>
              <th className="hidden px-4 py-3 text-right font-medium sm:table-cell">Views</th>
              <th className="hidden px-4 py-3 text-right font-medium sm:table-cell">Stars</th>
              <th className="hidden px-4 py-3 text-right font-medium sm:table-cell">Forks</th>
            </tr>
          </thead>
          <tbody>
            {ranked.map((r, i) => (
              <tr
                key={r.repository}
                className="border-b border-border/60 transition-colors last:border-0 hover:bg-foreground/[0.03]"
              >
                <td className="px-4 py-3 text-muted-foreground">
                  {i < 3 ? (
                    <span className="inline-flex items-center gap-1 font-semibold text-primary">
                      <Trophy className="h-3.5 w-3.5" />
                      {i + 1}
                    </span>
                  ) : (
                    <span className="tabular-nums">{i + 1}</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    {r.is_private && <Lock className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />}
                    <a
                      href={`https://github.com/${r.repository}`}
                      target="_blank"
                      rel="noreferrer"
                      className="group flex items-center gap-1 font-medium hover:text-primary"
                    >
                      {r.repository}
                      <ExternalLink className="h-3 w-3 opacity-0 transition-opacity group-hover:opacity-100" />
                    </a>
                  </div>
                </td>
                <td className="px-4 py-3 text-right font-semibold tabular-nums text-primary">
                  {r.clones.toLocaleString()}
                </td>
                <td className="px-4 py-3 text-right tabular-nums text-muted-foreground">
                  {(Number(r.unique_cloners) || 0).toLocaleString()}
                </td>
                <td className="hidden px-4 py-3 text-right tabular-nums text-muted-foreground sm:table-cell">
                  {r.views.toLocaleString()}
                </td>
                <td className="hidden px-4 py-3 text-right tabular-nums text-muted-foreground sm:table-cell">
                  {r.stars.toLocaleString()}
                </td>
                <td className="hidden px-4 py-3 text-right tabular-nums text-muted-foreground sm:table-cell">
                  {r.forks.toLocaleString()}
                </td>
              </tr>
            ))}
            {ranked.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-muted-foreground">
                  No clone data available.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
