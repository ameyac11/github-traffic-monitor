"""
gitlytics/cli.py
Command line interface for Gitlytics.
Achieves 100% feature parity with the Python API.
"""
import argparse
import sys
import os
import json

from gitlytics import fetch_traffic, sync, serve_dashboard

def parse_repo_names(repo_arg: str):
    if not repo_arg:
        return None
    return [r.strip() for r in repo_arg.split(",")]

def main():
    parser = argparse.ArgumentParser(description="Gitlytics - Monitor and Automate your GitHub Traffic")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- FETCH COMMAND ---
    fetch_parser = subparsers.add_parser("fetch", help="Fetch traffic for one or all repositories.")
    fetch_parser.add_argument("-t", "--token", help="GitHub Personal Access Token.")
    fetch_parser.add_argument("--repo-name", help="Specific repository or comma-separated list.")
    fetch_parser.add_argument("--print-table", action="store_true", help="Print the ASCII traffic table.")
    fetch_parser.add_argument("--return-format", choices=["dataframe", "timeseries", "summary"], default="dataframe", help="Data shape to return.")
    fetch_parser.add_argument("--save-file", help="Path to save the output (.csv or .json).")

    # --- SYNC COMMAND ---
    sync_parser = subparsers.add_parser("sync", help="Append traffic data to a local CSV database.")
    sync_parser.add_argument("-t", "--token", help="GitHub Personal Access Token.")
    sync_parser.add_argument("--repo-name", help="Specific repository or comma-separated list.")
    sync_parser.add_argument("--data-dir", default="./data", help="Directory to store CSVs.")
    sync_parser.add_argument("--output-mode", choices=["monthly", "yearly"], default="monthly", help="Chunking strategy for CSV files.")
    sync_parser.add_argument("--schedule-cron", help="Cron expression for background daemon mode.")
    sync_parser.add_argument("--export-json", help="Path to export the merged historical database as JSON.")
    sync_parser.add_argument("--export-public-only", type=bool, default=True, help="Strip private repos from JSON export.")

    # --- DASHBOARD COMMAND ---
    dash_parser = subparsers.add_parser("dashboard", help="Serve the local React dashboard.")
    dash_parser.add_argument("--host", default="127.0.0.1", help="Host IP.")
    dash_parser.add_argument("--port", type=int, default=8000, help="Port to bind.")
    dash_parser.add_argument("-t", "--token", help="GitHub token for headless TV display.")
    dash_parser.add_argument("--data-dir", help="Inject historical CSV database.")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Resolve token (fallback to env)
    token = getattr(args, "token", None) or os.environ.get("GITLYTICS_TOKEN") or os.environ.get("GITHUB_TOKEN")

    if args.command in ["fetch", "sync"] and not token:
        print("❌ Error: No GitHub token provided. Use --token or set GITLYTICS_TOKEN.")
        sys.exit(1)

    if args.command == "fetch":
        repos = parse_repo_names(args.repo_name)
        result = fetch_traffic(
            token=token,
            repo_name=repos,
            print_table=args.print_table,
            return_format=args.return_format,
            save_file=args.save_file
        )
        if not args.print_table and not args.save_file:
            print("Fetch successful. Use --print-table or --save-file to see results.")

    elif args.command == "sync":
        repos = parse_repo_names(args.repo_name)
        sync(
            token=token,
            repo_name=repos,
            data_dir=args.data_dir,
            output_mode=args.output_mode,
            schedule_cron=args.schedule_cron,
            export_json=args.export_json,
            export_public_only=args.export_public_only
        )

    elif args.command == "dashboard":
        print(f"\n🚀 Starting Gitlytics Dashboard on http://{args.host}:{args.port}\n")
        serve_dashboard(
            host=args.host,
            port=args.port,
            token=token,
            data_dir=args.data_dir
        )

if __name__ == "__main__":
    main()
