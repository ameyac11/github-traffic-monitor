"""
gitlytics/api.py
Powers the FastAPI backend — serves traffic data and the React dashboard to the browser.
"""
import logging
import os
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException, Body, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from gitlytics.core import validate_token, get_user_profile, fetch_traffic_data
from gitlytics.process import process_uploaded_csv, build_react_payload

logger = logging.getLogger(__name__)

app = FastAPI(title="GitHub Traffic API")

# Only allow requests from localhost — this dashboard is never deployed publicly
_ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def _get_token(token: str = None) -> str:
    # Use the token from the request body, or fall back to the one set in the environment
    return token or os.environ.get("GITLYTICS_TOKEN")


@app.get("/api/config")
def get_config():
    # Lets the frontend know if it's running in headless/TV mode with a pre-set token
    return {
        "has_token": bool(os.environ.get("GITLYTICS_TOKEN")),
        "has_data_dir": bool(os.environ.get("GITLYTICS_DATA_DIR"))
    }


@app.post("/api/auth")
def auth(token: str = Body("", embed=True)):
    # Validate the token and return the user's GitHub profile info
    active_token = _get_token(token)
    if not active_token:
        raise HTTPException(status_code=401, detail="No token provided and no environment token found.")

    ok, username = validate_token(active_token)
    if not ok:
        # Log a warning without echoing the token value into logs
        logger.warning("Authentication attempt failed for a provided token.")
        raise HTTPException(status_code=401, detail=username)

    # Fetch the real display name and avatar URL — validate_token only gives us the login
    profile = get_user_profile(active_token)

    return {
        "authenticated": True,
        "username": profile["login"] or username,
        "name": profile["name"] or username,        # Real display name, e.g. "Ameya Chopade"
        "avatar_url": profile["avatar_url"],         # Real GitHub avatar URL
    }


@app.post("/api/traffic")
def get_traffic(token: str = Body("", embed=True)):
    # Serve traffic data — either from the historical CSV database or live from GitHub
    active_token = _get_token(token)
    if not active_token:
        raise HTTPException(status_code=401, detail="No token provided")

    ok, _ = validate_token(active_token)
    if not ok:
        raise HTTPException(status_code=401, detail="Invalid token")

    data_dir = os.environ.get("GITLYTICS_DATA_DIR")
    if data_dir:
        # Load from the historical CSV database (headless/TV mode)
        data_dir_path = Path(data_dir)
        csv_files = list(data_dir_path.glob("traffic_*.csv")) if data_dir_path.exists() else []
        dfs = []
        for f in csv_files:
            try:
                dfs.append(pd.read_csv(f))
            except Exception as exc:
                logger.warning(f"Skipping unreadable CSV '{f}': {exc}")
        if dfs:
            df = pd.concat(dfs, ignore_index=True)
            # Clean up any duplicate day-repo rows that crept in somehow
            df = df.drop_duplicates(subset=["date", "repository"], keep="last")
        else:
            # No CSVs found — fall through to a live fetch
            df = fetch_traffic_data(active_token)
    else:
        # Default: hit GitHub and get the live 14-day window
        df = fetch_traffic_data(active_token)

    # Replace any infinity or NaN values before JSON serialisation
    df = df.replace([float('inf'), float('-inf')], None).where(pd.notnull(df), None)

    # Transform the DataFrame into the array of objects the React app expects
    payload = build_react_payload(df)
    return payload


@app.post("/api/upload-csv")
def upload_csv(file: UploadFile = File(...)):
    # Accept a user-uploaded CSV and convert it to the same format as the API response
    try:
        df = process_uploaded_csv(file.file)
        df = df.replace([float('inf'), float('-inf')], None).where(pd.notnull(df), None)
        payload = build_react_payload(df)
        return payload
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Static file serving ───────────────────────────────────────────────────────
# The React build output lands in gitlytics/static/ after `npm run build`
frontend_dir = Path(__file__).parent / "static"


@app.get("/")
def serve_index():
    # Serve the React app's index.html for the root URL
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse(
        status_code=503,
        content={"error": "Frontend not found. Run 'npm run build' in the frontend directory."}
    )


@app.get("/{full_path:path}")
def serve_spa_fallback(full_path: str):
    """
    SPA catch-all — any URL that doesn't match an API route returns index.html
    so React Router can handle client-side navigation on hard refresh.
    Real static assets (JS/CSS) are served by the StaticFiles mount first.
    """
    # Serve the actual file if it exists (e.g. a JS or CSS asset)
    asset_file = frontend_dir / full_path
    if asset_file.exists() and asset_file.is_file():
        return FileResponse(asset_file)

    # For everything else (like /repos/my-repo), hand control to React Router
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)

    return JSONResponse(
        status_code=503,
        content={"error": "Frontend not found. Run 'npm run build' in the frontend directory."}
    )


# Mount the /assets directory for compiled JS and CSS — must come after route definitions
assets_dir = frontend_dir / "assets"
if assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
