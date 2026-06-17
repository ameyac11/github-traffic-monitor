import { useEffect, useState } from "react";
import { LoginView } from "@/components/LoginView";
import { DashboardView } from "@/components/DashboardView";
import type { AuthResult, RepoTraffic } from "@/lib/github-api";

const STORAGE_KEY = "gh-traffic-session";

// Fix #21: Properly typed discriminated union — no `as any` needed downstream.
type ApiSession = { mode: "api"; auth: AuthResult; token: string };
type CsvSession = { mode: "csv"; data: RepoTraffic[]; filename?: string };
type Session = ApiSession | CsvSession;

export function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      // Fix #15: Use sessionStorage instead of localStorage so the token is
      // cleared when the browser tab/window is closed. Raw GitHub tokens
      // should not survive browser restarts in plaintext.
      const raw = sessionStorage.getItem(STORAGE_KEY);
      if (raw) setSession(JSON.parse(raw));
    } catch {
      /* ignore */
    }
    setReady(true);
  }, []);

  function persist(s: Session) {
    setSession(s);
    try {
      // Fix #15: Store in sessionStorage (cleared on tab close) rather than
      // localStorage (persists indefinitely and is readable by any JS on the origin).
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(s));
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
    sessionStorage.removeItem(STORAGE_KEY);
  }

  if (!ready) return null;

  return session ? (
    <DashboardView source={session} onLogout={handleLogout} />
  ) : (
    <LoginView onApiSuccess={handleApiSuccess} onCsvSuccess={handleCsvSuccess} />
  );
}
