"""
gitlytics/process.py
Handles processing Tidy DataFrames into final JSON formats for the frontend and dashboard.
"""
import ast
import json
import logging

import pandas as pd

logger = logging.getLogger(__name__)


def build_json_payload(df: pd.DataFrame, return_format: str = "timeseries", export_public_only: bool = True) -> dict:
    """
    Transforms the Tidy Data DataFrame into the nested JSON structure.
    Uses .iloc[-1] for snapshot metrics like stars/forks to prevent inflation.
    """
    if df.empty:
        return {"account_totals": {}, "repositories": {}}

    # Strip private repos from the export if the user wants public-only output
    if export_public_only and "is_private" in df.columns:
        df = df[~df["is_private"]]

    if df.empty:
        return {"account_totals": {}, "repositories": {}}

    # Running totals across all repos for the account summary card
    account_views = 0
    account_clones = 0
    account_uniques = 0
    account_unique_cloners = 0
    account_stars = 0
    account_forks = 0

    repos_dict = {}

    for repo, group in df.groupby("repository"):
        # Sort oldest to newest so timeseries arrays are in chronological order
        group = group.sort_values("date")

        # Traffic is cumulative — sum it over the whole window
        r_views = int(group["views"].sum()) if "views" in group.columns else 0
        r_clones = int(group["clones"].sum()) if "clones" in group.columns else 0
        r_unique_v = int(group["unique_visitors"].sum()) if "unique_visitors" in group.columns else 0
        r_unique_c = int(group["unique_cloners"].sum()) if "unique_cloners" in group.columns else 0

        # Stars and forks are snapshots — use the most recent row to avoid inflating totals
        r_stars = int(group["stars"].dropna().iloc[-1]) if "stars" in group.columns and not group["stars"].dropna().empty else 0
        r_forks = int(group["forks"].dropna().iloc[-1]) if "forks" in group.columns and not group["forks"].dropna().empty else 0
        r_is_private = bool(group["is_private"].dropna().iloc[-1]) if "is_private" in group.columns and not group["is_private"].dropna().empty else False

        # Same for referrer and path — take the most recent snapshot
        top_ref = str(group["top_referrer"].dropna().iloc[-1]) if "top_referrer" in group.columns and not group["top_referrer"].dropna().empty else ""
        top_path = str(group["top_path"].dropna().iloc[-1]) if "top_path" in group.columns and not group["top_path"].dropna().empty else ""

        # Add this repo's traffic to the account-wide running totals
        account_views += r_views
        account_clones += r_clones
        account_uniques += r_unique_v
        account_unique_cloners += r_unique_c
        account_stars += r_stars
        account_forks += r_forks

        if return_format == "summary":
            # Summary mode: just the totals, no per-day breakdown
            repos_dict[repo] = {
                "is_private": r_is_private,
                "total_views": r_views,
                "total_clones": r_clones,
                "unique_visitors": r_unique_v,
                "unique_cloners": r_unique_c,
                "stars": r_stars,
                "forks": r_forks
            }
        else:
            # Timeseries mode: full day-by-day array the React charts can consume directly
            timeseries = []
            for _, row in group.iterrows():
                timeseries.append({
                    "date": str(row["date"]),
                    "views": int(row.get("views", 0)),
                    "unique_visitors": int(row.get("unique_visitors", 0)),
                    "clones": int(row.get("clones", 0)),
                    "unique_cloners": int(row.get("unique_cloners", 0))
                })

            repos_dict[repo] = {
                "timeseries": timeseries,
                "totals": {
                    "is_private": r_is_private,
                    "stars": r_stars,
                    "forks": r_forks,
                    "top_referrer": top_ref,
                    "top_path": top_path
                }
            }

    # Package the account-wide summary alongside the per-repo data
    account_totals = {
        "total_views": account_views,
        "total_clones": account_clones,
        "unique_visitors": account_uniques,
        "unique_cloners": account_unique_cloners,
        "total_stars": account_stars,
        "total_forks": account_forks
    }

    return {
        "account_totals": account_totals,
        "repositories": repos_dict
    }


def process_uploaded_csv(uploaded_file) -> pd.DataFrame:
    """
    Reads a user-uploaded CSV and normalises column names to match our tidy schema.
    Supports both our native format and the old github-traffic-monitor column names.
    """
    raw_df = pd.read_csv(uploaded_file)
    if "repository" not in raw_df.columns:
        if "repo_name" in raw_df.columns:
            # Old column name from the pre-rebranding days
            raw_df = raw_df.rename(columns={"repo_name": "repository"})
        elif "Repository" in raw_df.columns:
            # Title-case column names from an older export format
            raw_df = raw_df.rename(columns={
                "Repository": "repository", "Total Views": "views", "Unique Visitors": "unique_visitors",
                "Total Clones": "clones", "Unique Cloners": "unique_cloners", "Stars": "stars", "Forks": "forks"
            })
        else:
            raise ValueError("Invalid CSV format: missing 'repository' column")
    return raw_df


def _parse_raw(val) -> list:
    # Try JSON first, then Python literal eval, then give up and return an empty list
    if isinstance(val, str) and val.strip() != "":
        try:
            return json.loads(val)
        except Exception:
            try:
                return ast.literal_eval(val)
            except Exception:
                return []
    if isinstance(val, list):
        return val
    return []


def build_react_payload(df: pd.DataFrame) -> list:
    """
    Transforms the Tidy Data DataFrame into the exact array of RepoTraffic objects
    expected by the React frontend. Prevents duplicate rows and populates all chart data.
    """
    if df.empty:
        return []

    repos = []
    for repo, group in df.groupby("repository"):
        # Sort so the timeseries arrays are always oldest → newest
        group = group.sort_values("date")

        # Sum traffic metrics across the whole window
        r_views = int(group["views"].sum()) if "views" in group.columns else 0
        r_clones = int(group["clones"].sum()) if "clones" in group.columns else 0
        r_unique_v = int(group["unique_visitors"].sum()) if "unique_visitors" in group.columns else 0
        r_unique_c = int(group["unique_cloners"].sum()) if "unique_cloners" in group.columns else 0

        # Snapshot metrics — always from the most recent row to avoid inflating numbers
        r_stars = int(group["stars"].dropna().iloc[-1]) if "stars" in group.columns and not group["stars"].dropna().empty else 0
        r_forks = int(group["forks"].dropna().iloc[-1]) if "forks" in group.columns and not group["forks"].dropna().empty else 0
        r_is_private = bool(group["is_private"].dropna().iloc[-1]) if "is_private" in group.columns and not group["is_private"].dropna().empty else False

        top_ref = str(group["top_referrer"].dropna().iloc[-1]) if "top_referrer" in group.columns and not group["top_referrer"].dropna().empty else ""
        top_ref_views = int(group["top_referrer_views"].dropna().iloc[-1]) if "top_referrer_views" in group.columns and not group["top_referrer_views"].dropna().empty else 0
        top_ref_uniques = int(group["top_referrer_uniques"].dropna().iloc[-1]) if "top_referrer_uniques" in group.columns and not group["top_referrer_uniques"].dropna().empty else 0

        top_path = str(group["top_path"].dropna().iloc[-1]) if "top_path" in group.columns and not group["top_path"].dropna().empty else ""
        top_path_views = int(group["top_path_views"].dropna().iloc[-1]) if "top_path_views" in group.columns and not group["top_path_views"].dropna().empty else 0
        top_path_uniques = int(group["top_path_uniques"].dropna().iloc[-1]) if "top_path_uniques" in group.columns and not group["top_path_uniques"].dropna().empty else 0

        # Build separate daily arrays for the views and clones line charts
        daily_views = []
        daily_clones = []
        for _, row in group.iterrows():
            date_str = str(row["date"])
            daily_views.append({
                "timestamp": date_str,
                "count": int(row.get("views", 0)),
                "uniques": int(row.get("unique_visitors", 0))
            })
            daily_clones.append({
                "timestamp": date_str,
                "count": int(row.get("clones", 0)),
                "uniques": int(row.get("unique_visitor", 0) if "unique_visitor" in row else row.get("unique_cloners", 0))
            })

        # Use the most recent row's raw data — it reflects the current referrer ranking
        raw_refs_val = group["_raw_referrers"].iloc[-1] if "_raw_referrers" in group.columns else None
        raw_paths_val = group["_raw_paths"].iloc[-1] if "_raw_paths" in group.columns else None

        # Decode the JSON-encoded full referrer and path lists
        full_refs = _parse_raw(raw_refs_val)
        full_paths = _parse_raw(raw_paths_val)

        # Fall back to the summary columns if the raw JSON columns are missing
        if not full_refs and top_ref:
            full_refs = [{"referrer": top_ref, "count": top_ref_views, "uniques": top_ref_uniques}]
        if not full_paths and top_path:
            full_paths = [{"path": top_path, "title": top_path, "count": top_path_views, "uniques": top_path_uniques}]

        repos.append({
            "repository": repo,
            "is_private": r_is_private,
            "stars": r_stars,
            "forks": r_forks,
            "views": r_views,
            "unique_visitors": r_unique_v,
            "clones": r_clones,
            "unique_cloners": r_unique_c,
            "top_referrer": top_ref,
            "top_referrer_views": top_ref_views,
            "top_referrer_uniques": top_ref_uniques,
            "top_path": top_path,
            "top_path_views": top_path_views,
            "top_path_uniques": top_path_uniques,
            # Per-day arrays for the charts
            "_daily_views": daily_views,
            "_daily_clones": daily_clones,
            # Full referrer and path breakdowns for the pie/bar charts
            "_referrers": full_refs,
            "_paths": full_paths
        })

    return repos
