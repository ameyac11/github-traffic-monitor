"""
gitlytics/__init__.py
The public API for the gitlytics package.
"""
import os
import sys
import logging
import json
import uvicorn
from .core import fetch_traffic_data, print_repo_table
from .automation import run_sync
from .process import build_json_payload

# Configure standard python logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def fetch_traffic(token: str, repo_name=None, print_table: bool = False, return_format: str = "dataframe", save_file: str = None):
    """
    Fetches the last 14 days of traffic data for one or all repositories.
    """
    df = fetch_traffic_data(token, repo_name)
    
    if print_table:
        print_repo_table(df)
        
    if return_format == "dataframe":
        if save_file:
            if save_file.endswith(".json"):
                payload = build_json_payload(df, return_format="timeseries", export_public_only=True)
                with open(save_file, "w", encoding="utf-8") as f:
                    json.dump(payload, f, indent=2)
            else:
                df.to_csv(save_file, index=False)
        return df
        
    # Return JSON payloads
    payload = build_json_payload(df, return_format=return_format, export_public_only=False)
    if save_file:
        with open(save_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            
    return payload

def sync(token: str, repo_name=None, data_dir: str = "./data", output_mode: str = "monthly", schedule_cron: str = None, export_json: str = None, export_public_only: bool = True):
    """
    Fetches data and appends it to a local CSV database, optionally running as a permanent background daemon.
    """
    run_sync(
        token=token,
        repo_names=repo_name,
        data_dir=data_dir,
        output_mode=output_mode,
        schedule_cron=schedule_cron,
        export_json=export_json,
        export_public_only=export_public_only
    )

def serve_dashboard(host: str = "127.0.0.1", port: int = 8000, token: str = None, data_dir: str = None):
    """
    Starts the React + FastAPI dashboard server.
    """
    # We pass token and data_dir through environment variables so api.py can read them
    if token:
        os.environ["GITLYTICS_TOKEN"] = token
    if data_dir:
        os.environ["GITLYTICS_DATA_DIR"] = os.path.abspath(data_dir)
        
    uvicorn.run("gitlytics.api:app", host=host, port=port, reload=False)
