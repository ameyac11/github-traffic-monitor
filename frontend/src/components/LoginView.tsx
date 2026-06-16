import { useRef, useState } from "react";
import {
  KeyRound,
  Github,
  Loader2,
  ShieldCheck,
  UploadCloud,
  FileSpreadsheet,
  Zap,
  ExternalLink,
  PlayCircle,
} from "lucide-react";
import {
  authenticate,
  uploadCsv,
  MAIN_REPO_URL,
  AUTOMATION_REPO_URL,
  type AuthResult,
  type RepoTraffic,
} from "@/lib/github-api";
import { DEMO_DATA } from "@/lib/demo-data";
import { LoadingScreen } from "./LoadingScreen";

type Mode = "api" | "csv";

export function LoginView({
  onApiSuccess,
  onCsvSuccess,
}: {
  onApiSuccess: (auth: AuthResult, token: string) => void;
  onCsvSuccess: (data: RepoTraffic[], filename?: string) => void;
}) {
  const [mode, setMode] = useState<Mode>("api");
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  async function handleApiSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!token.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const [auth] = await Promise.all([
        authenticate(token.trim()),
        new Promise((r) => setTimeout(r, 25000))
      ]);
      onApiSuccess(auth, token.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  async function handleFile(file: File) {
    if (!file.name.toLowerCase().endsWith(".csv")) {
      setError("Please upload a .csv file.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [data] = await Promise.all([
        uploadCsv(file),
        new Promise((r) => setTimeout(r, 3000))
      ]);
      onCsvSuccess(data, file.name);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to process CSV.");
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return <LoadingScreen label={mode === "api" ? "Connecting your account…" : "Processing your CSV…"} durationMs={mode === "api" ? 25000 : 3000} />;
  }

  return (
    <div className="flex h-screen items-center justify-center overflow-hidden px-4 py-6">
      <div className="w-full max-w-md">
        <div className="mb-5 flex flex-col items-center text-center">
          <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/15 ring-1 ring-primary/30">
            <Github className="h-7 w-7 text-primary" />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight">Gitlytics</h1>
          <p className="mt-1.5 text-sm text-muted-foreground">
            Track views, clones and visitors across all your repositories.
          </p>
        </div>


        <div className="mb-5 grid grid-cols-2 gap-2 rounded-xl bg-surface/60 p-1.5 ring-1 ring-border">
          <button
            onClick={() => {
              setMode("api");
              setError(null);
            }}
            className={`flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
              mode === "api"
                ? "bg-primary text-primary-foreground shadow"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Zap className="h-4 w-4" />
            Live API
          </button>
          <button
            onClick={() => {
              setMode("csv");
              setError(null);
            }}
            className={`flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
              mode === "csv"
                ? "bg-primary text-primary-foreground shadow"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <FileSpreadsheet className="h-4 w-4" />
            CSV Upload
          </button>
        </div>

        <div className="glass gradient-border animate-slide-up rounded-2xl p-6">
          {mode === "api" ? (
            <form onSubmit={handleApiSubmit} className="space-y-4">
              <div>
                <label className="mb-1.5 flex items-center gap-1.5 text-sm font-medium">
                  <KeyRound className="h-3.5 w-3.5 text-muted-foreground" />
                  Personal Access Token
                </label>
                <input
                  type="password"
                  value={token}
                  onChange={(e) => setToken(e.target.value)}
                  placeholder="ghp_••••••••••••••••••••"
                  autoComplete="off"
                  className="w-full rounded-lg border border-input bg-background/60 px-3.5 py-2.5 text-sm outline-none transition-colors placeholder:text-muted-foreground/60 focus:border-primary focus:ring-2 focus:ring-primary/30"
                />
              </div>

              {error && (
                <p className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={loading || !token.trim()}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition-all hover:scale-[1.01] hover:brightness-110 active:scale-[0.99] disabled:cursor-not-allowed disabled:opacity-50"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ShieldCheck className="h-4 w-4" />
                )}
                {loading ? "Connecting…" : "Connect Account"}
              </button>
              <p className="text-center text-xs text-muted-foreground">
                Your token is sent only to your local backend and never stored remotely.
              </p>
            </form>
          ) : (
            <div className="space-y-4">
              <input
                ref={fileInput}
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleFile(f);
                }}
              />
              <div
                onClick={() => !loading && fileInput.current?.click()}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragging(true);
                }}
                onDragLeave={() => setDragging(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragging(false);
                  const f = e.dataTransfer.files?.[0];
                  if (f) handleFile(f);
                }}
                className={`flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed px-6 py-8 text-center transition-all ${
                  dragging
                    ? "border-primary bg-primary/10"
                    : "border-border hover:border-primary/60 hover:bg-foreground/[0.02]"
                }`}
              >
                {loading ? (
                  <Loader2 className="h-8 w-8 animate-spin text-primary" />
                ) : (
                  <UploadCloud className="h-8 w-8 text-primary" />
                )}
                <div>
                  <p className="text-sm font-medium">
                    {loading ? "Processing your file…" : "Drag & drop your CSV here"}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    or click to browse — monthly traffic exports
                  </p>
                </div>
              </div>

              {error && (
                <p className="rounded-lg border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {error}
                </p>
              )}
              <p className="text-center text-xs text-muted-foreground">
                GitHub keeps only 14 days of traffic — these monthly CSVs preserve full history.
              </p>
            </div>
          )}
        </div>

        <div className="mt-4 flex items-center gap-3 text-xs text-muted-foreground">
          <div className="h-px flex-1 bg-border" />
          just want to look around?
          <div className="h-px flex-1 bg-border" />
        </div>

        <button
          onClick={() => onCsvSuccess(DEMO_DATA)}
          className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg border border-success/40 bg-success/10 px-4 py-2.5 text-sm font-semibold text-success transition-all hover:scale-[1.01] hover:bg-success/20"
        >
          <PlayCircle className="h-4 w-4" />
          Explore the Demo with Sample Data
        </button>

        <div className="mt-5 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-xs text-muted-foreground">
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
    </div>
  );
}
