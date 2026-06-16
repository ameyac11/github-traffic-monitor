export const API_BASE = "";

export const MAIN_REPO_URL = "https://github.com/ameyac11/gitlytics";

export const AUTOMATION_REPO_URL =
  "https://github.com/ameyac11/gitlytics-github-traffic-automation";

export interface AuthResult {
  authenticated: boolean;
  username: string;
  name: string;
  avatar_url: string;
}

export interface DailyPoint {
  timestamp: string;
  count: number;
  uniques: number;
}

export interface ReferrerPoint {
  referrer: string;
  count: number;
  uniques: number;
}

export interface PathPoint {
  path: string;
  title: string;
  count: number;
  uniques: number;
}

export interface RepoTraffic {
  repository: string;
  is_private: boolean;
  stars: number;
  forks: number;
  views: number;
  unique_visitors: number;
  clones: number;
  unique_cloners: number;
  top_referrer?: string;
  top_referrer_views?: number;
  top_referrer_uniques?: number;
  top_path?: string;
  top_path_views?: number;
  top_path_uniques?: number;
  date?: string;
  _daily_views?: DailyPoint[];
  _daily_clones?: DailyPoint[];
  _referrers?: ReferrerPoint[];
  _paths?: PathPoint[];
}

export async function authenticate(token: string): Promise<AuthResult> {
  const res = await fetch(`${API_BASE}/api/auth`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  if (!res.ok) {
    throw new Error(
      `Authentication failed (${res.status}). Check your token and that the backend is running.`,
    );
  }
  const data = (await res.json()) as AuthResult;
  if (!data.authenticated) throw new Error("Invalid GitHub token.");
  return data;
}

export async function fetchTraffic(token: string): Promise<RepoTraffic[]> {
  const res = await fetch(`${API_BASE}/api/traffic`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  if (!res.ok) {
    throw new Error(`Failed to load traffic data (${res.status}).`);
  }
  return (await res.json()) as RepoTraffic[];
}

export async function uploadCsv(file: File): Promise<RepoTraffic[]> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/api/upload-csv`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    throw new Error(`Failed to process CSV (${res.status}). Make sure the file format is correct.`);
  }
  return (await res.json()) as RepoTraffic[];
}

export function downloadCsv(repos: RepoTraffic[], filename = "github-traffic.csv") {
  const cols = [
    "date", "repository", "is_private", "views", "unique_visitors", "clones", "unique_cloners",
    "stars", "forks", "top_referrer", "top_referrer_views", "top_referrer_uniques",
    "top_path", "top_path_views", "top_path_uniques"
  ];
  const escape = (v: unknown) => {
    const s = v === undefined || v === null ? "" : String(v);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const header = cols.join(",");
  const rows: string[] = [];

  repos.forEach((r) => {
    const dailyMap = new Map<string, { views: number, unique_visitors: number, clones: number, unique_cloners: number }>();

    (r._daily_views || []).forEach(v => {
      const d = v.timestamp.substring(0, 10);
      if (!dailyMap.has(d)) dailyMap.set(d, { views: 0, unique_visitors: 0, clones: 0, unique_cloners: 0 });
      const entry = dailyMap.get(d)!;
      entry.views += v.count;
      entry.unique_visitors += v.uniques;
    });

    (r._daily_clones || []).forEach(c => {
      const d = c.timestamp.substring(0, 10);
      if (!dailyMap.has(d)) dailyMap.set(d, { views: 0, unique_visitors: 0, clones: 0, unique_cloners: 0 });
      const entry = dailyMap.get(d)!;
      entry.clones += c.count;
      entry.unique_cloners += c.uniques;
    });

    if (dailyMap.size === 0) {
      const dDate = r.date ? r.date.substring(0, 10) : new Date().toISOString().substring(0, 10);
      dailyMap.set(dDate, { views: 0, unique_visitors: 0, clones: 0, unique_cloners: 0 });
    }

    const sortedDates = Array.from(dailyMap.keys()).sort();

    sortedDates.forEach(date => {
      const daily = dailyMap.get(date)!;
      const rowData = [
        date, r.repository, r.is_private,
        daily.views, daily.unique_visitors, daily.clones, daily.unique_cloners,
        r.stars, r.forks,
        r.top_referrer, r.top_referrer_views, r.top_referrer_uniques,
        r.top_path, r.top_path_views, r.top_path_uniques
      ];
      rows.push(rowData.map(escape).join(","));
    });
  });

  const csv = [header, ...rows].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
