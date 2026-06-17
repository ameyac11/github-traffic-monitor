"""
tests/conftest.py
Shared pytest configuration and fixtures for the gitlytics test suite.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 OFFLINE tests  (pytest, no token needed, instant)
   python -m pytest tests/ -v

   test_core.py        unit tests for core.py
   test_automation.py  unit tests for automation.py
   test_cli.py         unit tests for cli.py
   test_process.py     unit tests for process.py
   test_api.py         unit tests for api.py

 ONLINE / LIVE tests  (scripts, real GitHub API, writes to data/)
   python tests/live_module.py       → Python public API
   python tests/live_cli.py          → CLI commands via subprocess
   python tests/live_automation.py   → sync engine / CSV writing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This conftest.py applies only to the offline pytest suite.
It loads .env and provides shared fixtures.
"""
import os
import pytest
from pathlib import Path

# ── Load .env before any test runs ───────────────────────────────────────────
# Walk up two levels from tests/ to find the project root where .env lives
_PROJECT_ROOT = Path(__file__).resolve().parent.parent  # gitlytics/
_ENV_FILE = _PROJECT_ROOT / ".env"

try:
    from dotenv import load_dotenv
    if _ENV_FILE.exists():
        # override=False means we won't overwrite a token that's already in the shell env
        load_dotenv(_ENV_FILE, override=False)
except ImportError:
    pass  # python-dotenv not installed — rely on env vars that are already set

# ── Fixtures ──────────────────────────────────────────────────────────────────

# Points to d:\PROGRAMING\MAIN Projects\gitlytics\data (three levels up from tests/)
DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"


@pytest.fixture(scope="session")
def data_dir() -> Path:
    """
    Persistent data directory at d:\\PROGRAMING\\MAIN Projects\\gitlytics\\data.
    Created automatically if it doesn't exist.
    Use this in integration tests that need to write real output files.
    """
    # Create the folder if a previous test run hasn't already
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR


@pytest.fixture(scope="session")
def github_token() -> str:
    """
    Returns the GitHub token from the environment (.env or system env).
    Automatically skips any test that uses this fixture when no token is available,
    so unit tests that use mocks are never blocked.
    """
    token = os.environ.get("GITLYTICS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        pytest.skip("No GITHUB_TOKEN / GITLYTICS_TOKEN found in .env or environment")
    return token
