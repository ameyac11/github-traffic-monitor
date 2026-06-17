import { useEffect, useRef, useState } from "react";
import { BarChart3, Github, ExternalLink } from "lucide-react";
import { MAIN_REPO_URL, AUTOMATION_REPO_URL } from "@/lib/github-api";

export function LoadingScreen({ label = "Connecting…", durationMs = 3000 }: { label?: string; durationMs?: number }) {
  const [progress, setProgress] = useState(8);
  const [showLinks, setShowLinks] = useState(false);
  const ref = useRef<number | null>(null);

  useEffect(() => {
    if (durationMs > 10000) {
      const t = setTimeout(() => setShowLinks(true), 2000);
      return () => clearTimeout(t);
    }
  }, [durationMs]);

  useEffect(() => {
    const interval = Math.max(10, Math.floor(durationMs / 100));
    ref.current = window.setInterval(() => {
      setProgress((p) => {
        if (p >= 99) return p;
        return Math.min(99, p + 1);
      });
    }, interval);
    return () => {
      if (ref.current) window.clearInterval(ref.current);
    };
  }, [durationMs]);

  return (
    <div className="fixed inset-0 z-50 flex h-screen w-screen flex-col items-center justify-center bg-background px-6">
      <div className="flex w-full max-w-sm flex-col items-center text-center">
        <div className="mb-6 flex h-14 w-14 animate-pulse items-center justify-center rounded-2xl bg-primary/15 ring-1 ring-primary/30">
          <BarChart3 className="h-7 w-7 text-primary" />
        </div>
        <p className="text-base font-semibold tracking-tight">{label}</p>
        <p className="mt-1 text-sm text-muted-foreground">Crunching your repository traffic…</p>

        <div className="mt-7 h-2 w-full overflow-hidden rounded-full bg-surface ring-1 ring-border">
          <div
            className="h-full rounded-full bg-primary transition-all duration-300 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="mt-3 text-sm font-medium tabular-nums text-primary">{Math.round(progress)}%</p>

        {durationMs > 10000 && (
          <div className={`mt-12 flex flex-col items-center gap-3 transition-opacity duration-1000 ${showLinks ? "opacity-100" : "opacity-0"}`}>
            <p className="text-xs text-muted-foreground">
              In the meantime, feel free to explore or star the project:
            </p>
            <div className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-xs text-muted-foreground">
              <a
                href={MAIN_REPO_URL}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 transition-colors hover:text-primary"
              >
                <Github className="h-3.5 w-3.5" />
                gitlytics
                <ExternalLink className="h-3 w-3" />
              </a>
              <a
                href={AUTOMATION_REPO_URL}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 transition-colors hover:text-primary"
              >
                <Github className="h-3.5 w-3.5" />
                gitlytics-github-traffic-automation
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
