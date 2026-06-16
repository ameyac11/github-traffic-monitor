"""
gitlytics/process.py
Handles processing Tidy DataFrames into final JSON formats for the frontend and dashboard.
"""
import pandas as pd

def build_json_payload(df: pd.DataFrame, return_format: str = "timeseries", export_public_only: bool = True) -> dict:
    """
    Transforms the Tidy Data DataFrame into the nested JSON structure.
    Prevents metric inflation by correctly using .iloc[-1] for snapshots like stars/forks.
    """
    if df.empty:
        return {"account_totals": {}, "repositories": {}}
        
    if export_public_only and "is_private" in df.columns:
        df = df[~df["is_private"]]
        
    if df.empty:
        return {"account_totals": {}, "repositories": {}}

    account_views = 0
    account_clones = 0
    account_uniques = 0
    account_unique_cloners = 0
    account_stars = 0
    account_forks = 0

    repos_dict = {}

    for repo, group in df.groupby("repository"):
        group = group.sort_values("date")
        
        # Cumulative Sums for traffic over the period
        r_views = int(group["views"].sum()) if "views" in group.columns else 0
        r_clones = int(group["clones"].sum()) if "clones" in group.columns else 0
        r_unique_v = int(group["unique_visitors"].sum()) if "unique_visitors" in group.columns else 0
        r_unique_c = int(group["unique_cloners"].sum()) if "unique_cloners" in group.columns else 0
        
        # Snapshots for metrics to prevent inflation (81,000 stars flaw)
        r_stars = int(group["stars"].dropna().iloc[-1]) if "stars" in group.columns and not group["stars"].dropna().empty else 0
        r_forks = int(group["forks"].dropna().iloc[-1]) if "forks" in group.columns and not group["forks"].dropna().empty else 0
        r_is_private = bool(group["is_private"].dropna().iloc[-1]) if "is_private" in group.columns and not group["is_private"].dropna().empty else False
        
        top_ref = str(group["top_referrer"].dropna().iloc[-1]) if "top_referrer" in group.columns and not group["top_referrer"].dropna().empty else ""
        top_path = str(group["top_path"].dropna().iloc[-1]) if "top_path" in group.columns and not group["top_path"].dropna().empty else ""

        # Accumulate account totals
        account_views += r_views
        account_clones += r_clones
        account_uniques += r_unique_v
        account_unique_cloners += r_unique_c
        account_stars += r_stars
        account_forks += r_forks

        if return_format == "summary":
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
    Fallback for manual dashboard CSV uploads. 
    Reads the CSV and ensures column names match our tidy data schema.
    """
    raw_df = pd.read_csv(uploaded_file)
    if "repository" not in raw_df.columns:
        if "repo_name" in raw_df.columns:
            raw_df = raw_df.rename(columns={"repo_name": "repository"})
        elif "Repository" in raw_df.columns:
            raw_df = raw_df.rename(columns={
                "Repository": "repository", "Total Views": "views", "Unique Visitors": "unique_visitors",
                "Total Clones": "clones", "Unique Cloners": "unique_cloners", "Stars": "stars", "Forks": "forks"
            })
        else:
            raise ValueError("Invalid CSV format: missing 'repository' column")
    return raw_df
