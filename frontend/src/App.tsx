import { useEffect, useState } from "react";
import { LoginView } from "@/components/LoginView";
import { DashboardView } from "@/components/DashboardView";
import type { AuthResult, RepoTraffic } from "@/lib/github-api";

const STORAGE_KEY = "gh-traffic-session";

type Session =
  | { mode: "api"; auth: AuthResult; token: string }
  | { mode: "csv"; data: RepoTraffic[]; filename?: string };

export function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) setSession(JSON.parse(raw));
    } catch {
      /* ignore */
    }
    setReady(true);
  }, []);

  function persist(s: Session) {
    setSession(s);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
    } catch {
      /* ignore quota errors */
    }
  }

  function handleApiSuccess(auth: AuthResult, token: string) {
    persist({ mode: "api", auth, token });
  }

  function handleCsvSuccess(data: RepoTraffic[], filename?: string) {
    persist({ mode: "csv", data, filename });
  }

  function handleLogout() {
    setSession(null);
    localStorage.removeItem(STORAGE_KEY);
  }

  if (!ready) return null;

  return session ? (
    <DashboardView source={session} onLogout={handleLogout} />
  ) : (
    <LoginView onApiSuccess={handleApiSuccess} onCsvSuccess={handleCsvSuccess} />
  );
}
