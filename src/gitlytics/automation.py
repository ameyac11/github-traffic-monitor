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

def get_csv_path(data_dir: str, mode: str) -> str:
    """Safely resolve the absolute database path to prevent cron fragmentation."""
    data_dir_path = Path(data_dir).resolve()
    data_dir_path.mkdir(parents=True, exist_ok=True)
    
    today = datetime.now(timezone.utc)
    if mode == "yearly":
        filename = f"traffic_{today.year}.csv"
    else:
        filename = f"traffic_{today.strftime('%Y-%m')}.csv"
        
    return str(data_dir_path / filename)

def export_json_database(data_dir: str, export_path: str, export_public_only: bool = True):
    """Compiles the entire historical CSV database into the master JSON schema for React."""
    data_dir_path = Path(data_dir).resolve()
    if not data_dir_path.exists():
        return
        
    csv_files = list(data_dir_path.glob("traffic_*.csv"))
    if not csv_files:
        return
        
    dfs = []
    for f in csv_files:
        try:
            dfs.append(pd.read_csv(f))
        except Exception:
            pass
            
    if not dfs:
        return
        
    master_df = pd.concat(dfs, ignore_index=True)
    
    payload = build_json_payload(master_df, return_format="timeseries", export_public_only=export_public_only)
    
    export_file = Path(export_path).resolve()
    export_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(export_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

def run_sync_cycle(token: str, repo_names=None, data_dir="./data", output_mode="monthly", export_json=None, export_public_only=True):
    df = fetch_traffic_data(token, repo_names)
    if df.empty:
        logging.info("No traffic data found to sync.")
        return
        
    csv_path = get_csv_path(data_dir, output_mode)
    file_exists = os.path.exists(csv_path)
    
    # Protect against CSV Header Misalignment
    existing_fields = None
    existing_data = {}
    
    if file_exists:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                existing_fields = next(reader)
            except StopIteration:
                pass
                
        try:
            existing_df = pd.read_csv(csv_path)
            for _, row in existing_df.iterrows():
                existing_data[(str(row["repository"]), str(row["date"]))] = row.to_dict()
        except Exception:
            pass
            
    # Merge fresh snapshots over historical overlaps
    new_records_added = 0
    for _, row in df.iterrows():
        key = (str(row["repository"]), str(row["date"]))
        if key not in existing_data:
            new_records_added += 1
        existing_data[key] = row.to_dict()
        
    if not existing_fields:
        existing_fields = list(df.columns)
        
    final_rows = []
    for v in existing_data.values():
        clean_row = {k: v.get(k, "") for k in existing_fields}
        final_rows.append(clean_row)
        
    final_rows.sort(key=lambda x: (x.get("date", ""), x.get("repository", "")))
    
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=existing_fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(final_rows)
        
    logging.info(f"Successfully processed traffic data. Added {new_records_added} new daily records to {csv_path}")
    
    if export_json:
        export_json_database(data_dir, export_json, export_public_only)
        logging.info(f"Exported historical database to {export_json}")

def run_sync(token: str, repo_names=None, data_dir="./data", output_mode="monthly", schedule_cron=None, export_json=None, export_public_only=True):
    if not schedule_cron:
        run_sync_cycle(token, repo_names, data_dir, output_mode, export_json, export_public_only)
        return
        
    logging.info("Starting Background Cron Job...")
    try:
        iter = croniter(schedule_cron, datetime.now())
    except ValueError as e:
        logging.error(f"Invalid cron expression: {e}")
        return
        
    while True:
        next_run = iter.get_next(datetime)
        sleep_secs = (next_run - datetime.now()).total_seconds()
        
        if sleep_secs > 0:
            logging.info(f"Scheduled next sync for {next_run.strftime('%Y-%m-%d %H:%M:%S')}. Sleeping...")
            time.sleep(sleep_secs)
            
        try:
            is_valid, msg = validate_token(token)
            if not is_valid:
                # Zombie Daemon Protection
                if "401" in msg or "authentication failed" in msg.lower():
                    logging.critical(f"FATAL ERROR: Token expired or revoked (401 Unauthorized). Terminating zombie daemon!")
                    sys.exit(1)
                else:
                    logging.warning(f"Network drop or temporary error: {msg}. Retrying next cycle.")
                    continue
                    
            run_sync_cycle(token, repo_names, data_dir, output_mode, export_json, export_public_only)
        except Exception as e:
            logging.error(f"Daemon encountered unexpected error: {e}. Recovering for next cycle.")
