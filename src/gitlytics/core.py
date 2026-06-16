"""
gitlytics/core.py
Handles fetching traffic data from GitHub API.
"""
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta

BASE = "https://api.github.com"

def make_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

def validate_token(token: str) -> tuple[bool, str]:
    try:
        r = requests.get(f"{BASE}/user", headers=make_headers(token), timeout=10)
    except requests.exceptions.ConnectionError:
        return False, "No internet connection."
    except Exception as e:
        return False, str(e)

    if r.status_code == 200:
        data = r.json()
        return True, data.get("login", "")
    if r.status_code == 401:
        return False, "Invalid token \u2014 authentication failed."
    if r.status_code == 403:
        return False, "Token has insufficient permissions."
    return False, f"GitHub returned HTTP {r.status_code}."

def _safe_get(url: str, headers: dict, params: dict = None):
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        return r.json() if r.status_code == 200 else {}
    except Exception:
        return {}

def get_all_repos(token: str) -> list[dict]:
    headers = make_headers(token)
    repos, page = [], 1
    seen = set()
    while True:
        data = _safe_get(f"{BASE}/user/repos", headers, {"per_page": 100, "page": page, "type": "all"})
        if not data or not isinstance(data, list):
            break
        for repo in data:
            fname = repo.get("full_name")
            if fname and fname not in seen:
                seen.add(fname)
                repos.append(repo)
        if len(data) < 100:
            break
        page += 1
    return repos

def get_single_repo(token: str, full_name: str) -> dict:
    headers = make_headers(token)
    data = _safe_get(f"{BASE}/repos/{full_name}", headers)
    if not data or "name" not in data:
        raise ValueError(f"Repository {full_name} not found or token lacks access.")
    return data

def get_repo_traffic(token: str, full_name: str) -> dict:
    h = make_headers(token)
    views   = _safe_get(f"{BASE}/repos/{full_name}/traffic/views", h)
    clones  = _safe_get(f"{BASE}/repos/{full_name}/traffic/clones", h)
    refs    = _safe_get(f"{BASE}/repos/{full_name}/traffic/popular/referrers", h)
    paths   = _safe_get(f"{BASE}/repos/{full_name}/traffic/popular/paths", h)

    return {
        "views":     views  if isinstance(views,  dict) else {},
        "clones":    clones if isinstance(clones, dict) else {},
        "referrers": refs   if isinstance(refs,   list) else [],
        "paths":     paths  if isinstance(paths,  list) else [],
    }

def pad_traffic_data(traffic: dict) -> list[dict]:
    views_list = traffic.get("views", {}).get("views", [])
    clones_list = traffic.get("clones", {}).get("clones", [])
    
    # Dynamically find the latest date GitHub has actually processed
    latest_date_str = None
    for item in views_list + clones_list:
        date_str = item["timestamp"][:10]
        if latest_date_str is None or date_str > latest_date_str:
            latest_date_str = date_str
            
    if latest_date_str:
        end_date = datetime.strptime(latest_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        # Fallback if the repository has literally 0 views and 0 clones over 14 days
        end_date = datetime.now(timezone.utc)
        
    # Generate exactly 14 days ending on the latest available date
    dates = [(end_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(13, -1, -1)]
    
    views_map = {v["timestamp"][:10]: v for v in views_list}
    clones_map = {c["timestamp"][:10]: c for c in clones_list}
    
    padded = []
    for d in dates:
        v = views_map.get(d, {})
        c = clones_map.get(d, {})
        padded.append({
            "date": d,
            "views": v.get("count", 0),
            "unique_visitors": v.get("uniques", 0),
            "clones": c.get("count", 0),
            "unique_cloners": c.get("uniques", 0)
        })
    return padded

def build_tidy_rows(repo: dict, traffic: dict) -> list[dict]:
    padded = pad_traffic_data(traffic)
    refs = traffic.get("referrers", [])
    paths = traffic.get("paths", [])
    
    top_ref = refs[0].get("referrer", "") if refs else ""
    top_ref_views = refs[0].get("count", 0) if refs else 0
    top_ref_uniques = refs[0].get("uniques", 0) if refs else 0
    
    top_path = paths[0].get("path", "") if paths else ""
    top_path_views = paths[0].get("count", 0) if paths else 0
    top_path_uniques = paths[0].get("uniques", 0) if paths else 0
    
    rows = []
    for day in padded:
        rows.append({
            "date": day["date"],
            "repository": repo["full_name"],
            "is_private": repo.get("private", False),
            "views": day["views"],
            "unique_visitors": day["unique_visitors"],
            "clones": day["clones"],
            "unique_cloners": day["unique_cloners"],
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "top_referrer": top_ref,
            "top_referrer_views": top_ref_views,
            "top_referrer_uniques": top_ref_uniques,
            "top_path": top_path,
            "top_path_views": top_path_views,
            "top_path_uniques": top_path_uniques
        })
    return rows

def fetch_traffic_data(token: str, repo_names=None) -> pd.DataFrame:
    if repo_names:
        if isinstance(repo_names, str):
            repo_names = [repo_names]
        repos = [get_single_repo(token, name) for name in repo_names]
    else:
        repos = get_all_repos(token)
        
    all_rows = []
    for repo in repos:
        traffic = get_repo_traffic(token, repo["full_name"])
        all_rows.extend(build_tidy_rows(repo, traffic))
        
    return pd.DataFrame(all_rows) if all_rows else pd.DataFrame()

def print_repo_table(df: pd.DataFrame):
    if df.empty:
        print("No data to display.")
        return
        
    # Dynamic repository column width based on the longest name, minimum 30
    repo_width = max(30, df["repository"].str.len().max() + 2)
    
    header = f"{'REPOSITORY':<{repo_width}} {'VIEWS':<8} {'U.VIEWS':<8} {'CLONES':<8} {'U.CLONES':<8} {'STARS':<8} {'FORKS':<8} {'TOP REFERRER':<15}"
    print(header)
    print("-" * len(header))
    
    total_account_views = 0
    total_account_uniques = 0
    total_account_clones = 0
    
    for repo in df["repository"].unique():
        repo_df = df[df["repository"] == repo]
        
        views = repo_df["views"].sum()
        u_views = repo_df["unique_visitors"].sum()
        clones = repo_df["clones"].sum()
        u_clones = repo_df["unique_cloners"].sum()
        
        # Snapshots for stars/forks
        stars = repo_df.iloc[-1]["stars"]
        forks = repo_df.iloc[-1]["forks"]
        top_ref = repo_df.iloc[-1]["top_referrer"]
        
        total_account_views += views
        total_account_uniques += u_views
        total_account_clones += clones
        
        print(f"{repo:<{repo_width}} {views:<8} {u_views:<8} {clones:<8} {u_clones:<8} {stars:<8} {forks:<8} {top_ref:<15}")
        
    print("-" * len(header))
    print(f"Total Account Views:  {total_account_views} (Unique: {total_account_uniques})")
    print(f"Total Account Clones: {total_account_clones}")
