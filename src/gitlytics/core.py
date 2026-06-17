"""
gitlytics/core.py
Handles fetching traffic data from GitHub API.
"""
import json
import logging
import requests
import pandas as pd
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)

# GitHub API base URL
BASE = "https://api.github.com"


def make_headers(token: str) -> dict:
    # Build the auth headers GitHub needs to identify us
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def validate_token(token: str) -> tuple[bool, str]:
    # Try to reach the GitHub /user endpoint with the given token
    try:
        r = requests.get(f"{BASE}/user", headers=make_headers(token), timeout=10)
    except requests.exceptions.ConnectionError:
        return False, "No internet connection."
    except Exception as e:
        return False, str(e)

    # 200 means the token is valid — return the username
    if r.status_code == 200:
        data = r.json()
        return True, data.get("login", "")
    # 401 means the token is wrong or expired
    if r.status_code == 401:
        return False, "Invalid token — authentication failed (401 Unauthorized)."
    # 403 means the token exists but doesn't have enough permissions
    if r.status_code == 403:
        return False, "Token has insufficient permissions (403 Forbidden)."
    return False, f"GitHub returned HTTP {r.status_code}."


def get_user_profile(token: str) -> dict:
    """
    Returns the authenticated user's full profile from GitHub.
    Includes login (username), name (display name), and avatar_url.
    Falls back gracefully if any field is missing.
    """
    try:
        r = requests.get(f"{BASE}/user", headers=make_headers(token), timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {
                "login": data.get("login", ""),
                # GitHub's "name" field is the display name — it can be null if not set
                "name": data.get("name") or data.get("login", ""),
                "avatar_url": data.get("avatar_url", ""),
            }
    except Exception as exc:
        logger.warning(f"Could not fetch user profile: {exc}")
    # Return empty strings so callers don't have to handle None
    return {"login": "", "name": "", "avatar_url": ""}


def _safe_get(url: str, headers: dict, params: dict = None) -> tuple:
    """
    Wraps requests.get with error handling and returns (data, status_code).
    Callers can distinguish between genuine zero-data and fetch failures.

    Returns:
        (data, status_code) where data is the parsed JSON on success,
        or an empty container ({} or []) on failure.
    """
    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            return r.json(), 200
        # 429 means we hit the rate limit — warn and return empty
        if r.status_code == 429:
            logger.warning(f"GitHub API rate limit hit (429) for {url}. Data for this endpoint will be empty.")
        # 403 usually means the token doesn't have traffic read permission for this repo
        elif r.status_code == 403:
            logger.warning(f"Access denied (403) for {url}. Token may lack traffic permission for this repository.")
        elif r.status_code != 404:
            logger.warning(f"Unexpected HTTP {r.status_code} for {url}.")
        return {}, r.status_code
    except requests.exceptions.Timeout:
        logger.warning(f"Request timed out for {url}.")
        return {}, -1
    except Exception as exc:
        logger.warning(f"Request failed for {url}: {exc}")
        return {}, -1


def get_all_repos(token: str) -> list[dict]:
    # Page through every repo the token can see (handles accounts with 100+ repos)
    headers = make_headers(token)
    repos, page = [], 1
    seen = set()  # dedup guard in case GitHub returns the same repo on multiple pages
    while True:
        data, _ = _safe_get(f"{BASE}/user/repos", headers, {"per_page": 100, "page": page, "type": "all"})
        if not data or not isinstance(data, list):
            break
        for repo in data:
            fname = repo.get("full_name")
            if fname and fname not in seen:
                seen.add(fname)
                repos.append(repo)
        # GitHub stops paginating when a page has fewer than 100 results
        if len(data) < 100:
            break
        page += 1
    return repos


def get_single_repo(token: str, full_name: str) -> dict:
    # Fetch metadata for one specific repo and raise a friendly error if it's missing
    headers = make_headers(token)
    data, status = _safe_get(f"{BASE}/repos/{full_name}", headers)
    if not data or "name" not in data:
        raise ValueError(
            f"Repository '{full_name}' not found or token lacks access "
            f"(HTTP {status})."
        )
    return data


def get_repo_traffic(token: str, full_name: str) -> dict:
    # Fetch all four traffic endpoints for a single repo in one go
    h = make_headers(token)
    views,  _  = _safe_get(f"{BASE}/repos/{full_name}/traffic/views", h)
    clones, _  = _safe_get(f"{BASE}/repos/{full_name}/traffic/clones", h)
    refs,   _  = _safe_get(f"{BASE}/repos/{full_name}/traffic/popular/referrers", h)
    paths,  _  = _safe_get(f"{BASE}/repos/{full_name}/traffic/popular/paths", h)

    # Make sure each field is the correct type even if the API returned nothing
    return {
        "views":     views  if isinstance(views,  dict) else {},
        "clones":    clones if isinstance(clones, dict) else {},
        "referrers": refs   if isinstance(refs,   list) else [],
        "paths":     paths  if isinstance(paths,  list) else [],
    }


def pad_traffic_data(traffic: dict) -> list[dict]:
    # GitHub only returns days with activity, so we fill in the missing days with zeros
    views_list = traffic.get("views", {}).get("views", [])
    clones_list = traffic.get("clones", {}).get("clones", [])

    # Find the latest date GitHub has processed so our window is accurate
    latest_date_str = None
    for item in views_list + clones_list:
        date_str = item["timestamp"][:10]
        if latest_date_str is None or date_str > latest_date_str:
            latest_date_str = date_str

    if latest_date_str:
        end_date = datetime.strptime(latest_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        # If the repo has zero traffic, anchor the window to today
        end_date = datetime.now(timezone.utc)

    # Build a continuous 14-day window ending on the latest known date
    dates = [(end_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(13, -1, -1)]

    # Index the API data by date so we can look up each day in O(1)
    views_map = {v["timestamp"][:10]: v for v in views_list}
    clones_map = {c["timestamp"][:10]: c for c in clones_list}

    padded = []
    for d in dates:
        v = views_map.get(d, {})
        c = clones_map.get(d, {})
        # Use 0 for any day that GitHub didn't return (no traffic that day)
        padded.append({
            "date": d,
            "views": v.get("count", 0),
            "unique_visitors": v.get("uniques", 0),
            "clones": c.get("count", 0),
            "unique_cloners": c.get("uniques", 0)
        })
    return padded


def build_tidy_rows(repo: dict, traffic: dict) -> list[dict]:
    # Start with a zero-padded 14-day timeseries for this repo
    padded = pad_traffic_data(traffic)
    refs = traffic.get("referrers", [])
    paths = traffic.get("paths", [])

    # Pull out the top referrer and path (rank #1 only — full list goes in _raw_* columns)
    top_ref = refs[0].get("referrer", "") if refs else ""
    top_ref_views = refs[0].get("count", 0) if refs else 0
    top_ref_uniques = refs[0].get("uniques", 0) if refs else 0

    top_path = paths[0].get("path", "") if paths else ""
    top_path_views = paths[0].get("count", 0) if paths else 0
    top_path_uniques = paths[0].get("uniques", 0) if paths else 0

    rows = []
    for day in padded:
        # One CSV row per calendar day, with repo metadata repeated on every row
        rows.append({
            "date": day["date"],
            "repository": repo["full_name"],
            "is_private": repo.get("private", False),
            "views": day["views"],
            "unique_visitors": day["unique_visitors"],
            "clones": day["clones"],
            "unique_cloners": day["unique_cloners"],
            # Stars and forks are current snapshots, not daily totals
            "stars": repo.get("stargazers_count", 0),
            "forks": repo.get("forks_count", 0),
            "top_referrer": top_ref,
            "top_referrer_views": top_ref_views,
            "top_referrer_uniques": top_ref_uniques,
            "top_path": top_path,
            "top_path_views": top_path_views,
            "top_path_uniques": top_path_uniques,
            # Store the full referrer and path lists as JSON strings for the dashboard charts
            "_raw_referrers": json.dumps(refs),
            "_raw_paths": json.dumps(paths)
        })
    return rows


def fetch_traffic_data(token: str, repo_names=None) -> pd.DataFrame:
    # Decide whether to fetch one repo, a custom list, or all repos
    if repo_names:
        if isinstance(repo_names, str):
            repo_names = [repo_names]
        repos = [get_single_repo(token, name) for name in repo_names]
    else:
        repos = get_all_repos(token)

    # Fetch traffic for each repo and combine everything into one big DataFrame
    all_rows = []
    for repo in repos:
        traffic = get_repo_traffic(token, repo["full_name"])
        all_rows.extend(build_tidy_rows(repo, traffic))

    return pd.DataFrame(all_rows) if all_rows else pd.DataFrame()


def print_repo_table(df: pd.DataFrame):
    if df.empty:
        print("No data to display.")
        return

    # Make the repo name column wide enough to fit the longest name
    repo_width = max(30, df["repository"].str.len().max() + 2)

    header = f"{'REPOSITORY':<{repo_width}} {'VIEWS':<8} {'U.VIEWS':<8} {'CLONES':<8} {'U.CLONES':<8} {'STARS':<8} {'FORKS':<8} {'TOP REFERRER':<15}"
    print(header)
    print("-" * len(header))

    total_account_views = 0
    total_account_uniques = 0
    total_account_clones = 0

    for repo in df["repository"].unique():
        repo_df = df[df["repository"] == repo]

        # Sum traffic over the 14-day window
        views = repo_df["views"].sum()
        u_views = repo_df["unique_visitors"].sum()
        clones = repo_df["clones"].sum()
        u_clones = repo_df["unique_cloners"].sum()

        # Stars and forks are point-in-time — use the most recent row
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
