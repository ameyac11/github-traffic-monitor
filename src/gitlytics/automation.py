"""
gitlytics/automation.py
Handles continuous database appending, cron jobs, and JSON exporting.
"""
import os
import csv
import sys
import time
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from croniter import croniter
import pandas as pd

from gitlytics.core import fetch_traffic_data, validate_token
from gitlytics.process import build_json_payload

logger = logging.getLogger(__name__)


def get_csv_path(data_dir: str, mode: str) -> str:
    # Make sure the data folder exists, then return the right filename for this month or year
    data_dir_path = Path(data_dir).resolve()
    data_dir_path.mkdir(parents=True, exist_ok=True)

    today = datetime.now(timezone.utc)
    if mode == "yearly":
        filename = f"traffic_{today.year}.csv"
    else:
        # Monthly mode groups data by YYYY-MM so files stay manageable
        filename = f"traffic_{today.strftime('%Y-%m')}.csv"

    return str(data_dir_path / filename)


def export_json_database(data_dir: str, export_path: str, export_public_only: bool = True):
    # Read every CSV in the data folder and merge them into one big JSON file for the dashboard
    data_dir_path = Path(data_dir).resolve()
    if not data_dir_path.exists():
        return

    csv_files = list(data_dir_path.glob("traffic_*.csv"))
    if not csv_files:
        return

    # Load each CSV, skipping any that are corrupted
    dfs = []
    for f in csv_files:
        try:
            dfs.append(pd.read_csv(f))
        except Exception as exc:
            logger.warning(f"Skipping corrupt or unreadable CSV file '{f}': {exc}")

    if not dfs:
        return

    # Combine all historical data into one DataFrame
    master_df = pd.concat(dfs, ignore_index=True)

    # Deduplicate — if both a monthly and yearly CSV exist they contain overlapping rows.
    # Keep the LAST occurrence (most recently written) so schema migrations win.
    if "date" in master_df.columns and "repository" in master_df.columns:
        master_df = master_df.drop_duplicates(subset=["date", "repository"], keep="last")

    # Transform into the nested JSON structure the React dashboard expects
    payload = build_json_payload(master_df, return_format="timeseries", export_public_only=export_public_only)

    # Write the JSON to disk, creating parent folders if needed
    export_file = Path(export_path).resolve()
    export_file.parent.mkdir(parents=True, exist_ok=True)

    with open(export_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _merge_schema(existing_fields: list, new_fields: list) -> list:
    """
    Merges old and new CSV column schemas without dropping new fields.
    Existing fields keep their original order; new fields are appended at the end
    so historical rows stay compatible with the updated schema.
    """
    merged = list(existing_fields)
    for col in new_fields:
        if col not in merged:
            # A new column appeared in the API response — add it so it gets saved
            logger.info(f"Schema upgrade: adding new column '{col}' to existing CSV.")
            merged.append(col)
    return merged


def run_sync_cycle(token: str, repo_names=None, data_dir="./data", output_mode="monthly", export_json=None, export_public_only=True):
    # Fetch fresh traffic data from GitHub
    df = fetch_traffic_data(token, repo_names)
    if df.empty:
        logger.info("No traffic data found to sync.")
        return

    # Figure out which CSV file to write to based on today's date
    csv_path = get_csv_path(data_dir, output_mode)
    file_exists = os.path.exists(csv_path)

    existing_fields = None
    existing_data = {}

    if file_exists:
        # Read the existing column headers so we can migrate the schema if needed
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                existing_fields = next(reader)
            except StopIteration:
                pass

        # Load all existing rows into a dict keyed by (repo, date) for deduplication
        try:
            existing_df = pd.read_csv(csv_path)
            for _, row in existing_df.iterrows():
                existing_data[(str(row["repository"]), str(row["date"]))] = row.to_dict()
        except Exception as exc:
            logger.warning(f"Could not read existing CSV '{csv_path}': {exc}. Starting fresh.")

    # Merge old and new column schemas so we never lose new fields
    new_fields = list(df.columns)
    if existing_fields:
        existing_fields = _merge_schema(existing_fields, new_fields)
    else:
        existing_fields = new_fields

    # Overwrite existing rows with fresh data, and add brand-new day rows
    new_records_added = 0
    for _, row in df.iterrows():
        key = (str(row["repository"]), str(row["date"]))
        if key not in existing_data:
            new_records_added += 1
        existing_data[key] = row.to_dict()

    # Sort all rows by date and repo name before writing back to disk
    final_rows = []
    for v in existing_data.values():
        # Fill any missing schema columns with empty strings for old rows
        clean_row = {k: v.get(k, "") for k in existing_fields}
        final_rows.append(clean_row)

    final_rows.sort(key=lambda x: (x.get("date", ""), x.get("repository", "")))

    # Write everything back to the CSV file atomically
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=existing_fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(final_rows)

    logger.info(f"Successfully processed traffic data. Added {new_records_added} new daily records to {csv_path}")

    # If the user wants a JSON export, regenerate it from the full database
    if export_json:
        export_json_database(data_dir, export_json, export_public_only)
        logger.info(f"Exported historical database to {export_json}")


def run_sync(token: str, repo_names=None, data_dir="./data", output_mode="monthly", schedule_cron=None, export_json=None, export_public_only=True):
    # No cron expression = run once and exit
    if not schedule_cron:
        run_sync_cycle(token, repo_names, data_dir, output_mode, export_json, export_public_only)
        return

    logger.info("Starting Background Cron Job...")
    # Parse the cron expression — fail early if the format is wrong
    try:
        now_utc = datetime.now(timezone.utc)
        iter = croniter(schedule_cron, now_utc)
    except ValueError as e:
        logger.error(f"Invalid cron expression: {e}")
        return

    # Infinite loop — keeps running until the process is killed or the token dies
    while True:
        now_utc = datetime.now(timezone.utc)
        next_run = iter.get_next(datetime)

        # croniter may return naive datetimes on older versions — make it timezone-aware
        if next_run.tzinfo is None:
            next_run = next_run.replace(tzinfo=timezone.utc)

        sleep_secs = (next_run - now_utc).total_seconds()

        # Sleep until the next scheduled run
        if sleep_secs > 0:
            logger.info(f"Scheduled next sync for {next_run.strftime('%Y-%m-%d %H:%M:%S UTC')}. Sleeping...")
            time.sleep(sleep_secs)

        try:
            # Always re-validate the token before fetching to catch expiry early
            is_valid, msg = validate_token(token)
            if not is_valid:
                # Distinguish between a dead token (stop forever) and a network blip (retry next cycle)
                is_auth_failure = (
                    "401" in msg
                    or "authentication failed" in msg.lower()
                    or "invalid token" in msg.lower()
                    or "revoked" in msg.lower()
                )
                if is_auth_failure:
                    logger.critical(
                        "FATAL: Token is expired, revoked, or invalid (401 Unauthorized). "
                        "Terminating daemon to prevent zombie process."
                    )
                    sys.exit(1)
                else:
                    logger.warning(f"Network drop or temporary error: {msg}. Retrying next cycle.")
                    continue

            run_sync_cycle(token, repo_names, data_dir, output_mode, export_json, export_public_only)
        except Exception as e:
            # Don't let a single bad cycle kill the daemon — just log and carry on
            logger.error(f"Daemon encountered unexpected error: {e}. Recovering for next cycle.")
