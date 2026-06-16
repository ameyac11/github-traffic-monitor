"""
gitlytics/api.py
This file powers the FastAPI backend, serving our data and React dashboard to the browser!
"""
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Header, Body, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

from gitlytics.core import validate_token, fetch_traffic_data
from gitlytics.process import process_uploaded_csv

app = FastAPI(title="GitHub Traffic API")

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _get_token(token: str = None) -> str:
    # Use explicit token, or fallback to environment (headless TV mode)
    return token or os.environ.get("GITLYTICS_TOKEN")

@app.get("/api/config")
def get_config():
    """Allows frontend to detect if we are running in headless TV mode."""
    return {
        "has_token": bool(os.environ.get("GITLYTICS_TOKEN")),
        "has_data_dir": bool(os.environ.get("GITLYTICS_DATA_DIR"))
    }

@app.post("/api/auth")
def auth(token: str = Body("", embed=True)):
    active_token = _get_token(token)
    if not active_token:
        raise HTTPException(status_code=401, detail="No token provided and no environment token found.")
        
    ok, username = validate_token(active_token)
    if not ok:
        raise HTTPException(status_code=401, detail=username)
        
    return {
        "authenticated": True,
        "username": username,
        "name": username,
    }

@app.post("/api/traffic")
def get_traffic(token: str = Body("", embed=True)):
    active_token = _get_token(token)
    if not active_token:
        raise HTTPException(status_code=401, detail="No token provided")
        
    ok, _ = validate_token(active_token)
    if not ok:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    data_dir = os.environ.get("GITLYTICS_DATA_DIR")
    if data_dir:
        # Load all history from the database!
        data_dir_path = Path(data_dir)
        csv_files = list(data_dir_path.glob("traffic_*.csv")) if data_dir_path.exists() else []
        dfs = []
        for f in csv_files:
            try:
                dfs.append(pd.read_csv(f))
            except Exception:
                pass
        if dfs:
            df = pd.concat(dfs, ignore_index=True)
            # Remove duplicate day-repo rows if any exist
            df = df.drop_duplicates(subset=["date", "repository"], keep="last")
        else:
            df = fetch_traffic_data(active_token)
    else:
        # Live 14-day fetch
        df = fetch_traffic_data(active_token)
        
    df = df.replace([float('inf'), float('-inf')], None).where(pd.notnull(df), None)
    return df.to_dict(orient="records")

@app.post("/api/upload-csv")
def upload_csv(file: UploadFile = File(...)):
    try:
        df = process_uploaded_csv(file.file)
        df = df.replace([float('inf'), float('-inf')], None).where(pd.notnull(df), None)
        return df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Mount the React frontend assets
frontend_dir = Path(__file__).parent / "static"

@app.get("/")
def serve_index():
    index_file = frontend_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return JSONResponse(
        status_code=404,
        content={"error": "Frontend not built. Run 'npm run build' in the frontend directory."}
    )

if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir), name="static")
