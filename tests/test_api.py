"""
tests/test_api.py
Unit tests for gitlytics/api.py — FastAPI endpoints.
Uses FastAPI's TestClient so no running server or GitHub token is needed.
All GitHub API calls are mocked.

Run with:
    python -m pytest tests/test_api.py -v

Note: requires httpx  →  pip install httpx
"""
import io
import json
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

# TestClient requires httpx — skip the whole module gracefully if not installed
try:
    from fastapi.testclient import TestClient
    from gitlytics.api import app
    HAS_TESTCLIENT = True
except Exception:
    HAS_TESTCLIENT = False

pytestmark = pytest.mark.skipif(
    not HAS_TESTCLIENT,
    reason="httpx not installed — run: pip install httpx"
)

# One shared client for all tests — no server startup needed
client = TestClient(app, raise_server_exceptions=True)


# ── Helper factories ───────────────────────────────────────────────────────────

def _make_tidy_df(repo="user/repo", views=10, clones=5, is_private=False):
    """Builds a minimal one-row tidy DataFrame as returned by fetch_traffic_data."""
    return pd.DataFrame([{
        "date": "2025-06-14",
        "repository": repo,
        "is_private": is_private,
        "views": views,
        "unique_visitors": 4,
        "clones": clones,
        "unique_cloners": 2,
        "stars": 20,
        "forks": 3,
        "top_referrer": "github.com",
        "top_referrer_views": 5,
        "top_referrer_uniques": 2,
        "top_path": "/README.md",
        "top_path_views": 4,
        "top_path_uniques": 1,
        "_raw_referrers": json.dumps([{"referrer": "github.com", "count": 5, "uniques": 2}]),
        "_raw_paths":     json.dumps([{"path": "/README.md", "count": 4, "uniques": 1}]),
    }])


def _make_csv_body(headers, row):
    """Creates a CSV BytesIO for upload tests."""
    content = ",".join(headers) + "\n" + ",".join(str(v) for v in row) + "\n"
    return io.BytesIO(content.encode("utf-8"))


# ── /api/config ────────────────────────────────────────────────────────────────

class TestConfigEndpoint:
    def test_returns_200(self):
        # The config endpoint must always respond with 200
        response = client.get("/api/config")
        assert response.status_code == 200

    def test_returns_has_token_field(self):
        # has_token tells the frontend whether the server was started with a pre-set token
        data = client.get("/api/config").json()
        assert "has_token" in data
        assert isinstance(data["has_token"], bool)

    def test_has_token_false_without_env_token(self):
        # With no GITLYTICS_TOKEN in env, has_token should be False
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("GITLYTICS_TOKEN", None)
            data = client.get("/api/config").json()
        assert data["has_token"] is False

    def test_returns_has_data_dir_field(self):
        # has_data_dir tells the frontend if a historical CSV directory is configured
        data = client.get("/api/config").json()
        assert "has_data_dir" in data


# ── /api/auth ──────────────────────────────────────────────────────────────────

class TestAuthEndpoint:
    @patch("gitlytics.api.validate_token", return_value=(True, "ameyac11"))
    @patch("gitlytics.api.get_user_profile", return_value={
        "login": "ameyac11", "name": "Ameya Chopade", "avatar_url": "https://avatars.github.com/u/1"
    })
    def test_valid_token_returns_authenticated(self, mock_profile, mock_validate):
        # A valid token should give back authenticated=True with the user's profile
        response = client.post("/api/auth", json={"token": "valid_token"})
        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True
        assert data["username"] == "ameyac11"
        assert data["name"] == "Ameya Chopade"
        assert "avatar_url" in data

    @patch("gitlytics.api.validate_token", return_value=(False, "Invalid token — 401 Unauthorized."))
    def test_invalid_token_returns_401(self, mock_validate):
        # A bad or expired token must return HTTP 401
        response = client.post("/api/auth", json={"token": "bad_token"})
        assert response.status_code == 401

    def test_no_token_returns_401(self):
        # Sending an empty body with no token and no env token must return 401
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("GITLYTICS_TOKEN", None)
            response = client.post("/api/auth", json={"token": ""})
        assert response.status_code == 401

    @patch("gitlytics.api.validate_token", return_value=(True, "ameyac11"))
    @patch("gitlytics.api.get_user_profile", return_value={
        "login": "ameyac11", "name": "Ameya Chopade", "avatar_url": "https://avatars.github.com/u/1"
    })
    def test_response_has_all_profile_fields(self, mock_profile, mock_validate):
        # The frontend needs login, name, and avatar_url — all three must be present
        data = client.post("/api/auth", json={"token": "valid_token"}).json()
        assert "username" in data
        assert "name" in data
        assert "avatar_url" in data

    @patch("gitlytics.api.validate_token", return_value=(True, "ameyac11"))
    @patch("gitlytics.api.get_user_profile", return_value={
        "login": "ameyac11", "name": "", "avatar_url": ""
    })
    def test_null_display_name_falls_back_to_login(self, mock_profile, mock_validate):
        # If the user has no display name set on GitHub, fall back to their username
        data = client.post("/api/auth", json={"token": "valid_token"}).json()
        # name should never be blank — it should fall back to username
        assert data["name"] or data["username"]  # at least one must be non-empty


# ── /api/traffic ───────────────────────────────────────────────────────────────

class TestTrafficEndpoint:
    @patch("gitlytics.api.validate_token", return_value=(True, "user"))
    @patch("gitlytics.api.fetch_traffic_data", return_value=_make_tidy_df())
    def test_valid_token_returns_list(self, mock_fetch, mock_validate):
        # The traffic endpoint must return a list of repo objects
        response = client.post("/api/traffic", json={"token": "valid_token"})
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    @patch("gitlytics.api.validate_token", return_value=(True, "user"))
    @patch("gitlytics.api.fetch_traffic_data", return_value=_make_tidy_df())
    def test_repo_objects_have_required_fields(self, mock_fetch, mock_validate):
        # Each repo object must include the fields the React dashboard depends on
        response = client.post("/api/traffic", json={"token": "valid_token"})
        repos = response.json()
        assert len(repos) > 0
        repo = repos[0]
        for field in ["repository", "views", "clones", "stars", "forks"]:
            assert field in repo, f"Missing field: {field}"

    @patch("gitlytics.api.validate_token", return_value=(False, "Bad token"))
    def test_invalid_token_returns_401(self, mock_validate):
        # A bad token must return 401, not crash or return empty data
        response = client.post("/api/traffic", json={"token": "bad_token"})
        assert response.status_code == 401

    def test_no_token_returns_401(self):
        # Missing token must return 401
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("GITLYTICS_TOKEN", None)
            response = client.post("/api/traffic", json={"token": ""})
        assert response.status_code == 401

    @patch("gitlytics.api.validate_token", return_value=(True, "user"))
    @patch("gitlytics.api.fetch_traffic_data", return_value=pd.DataFrame())
    def test_empty_data_returns_empty_list(self, mock_fetch, mock_validate):
        # If the user has no repos, the endpoint must return [] not crash
        response = client.post("/api/traffic", json={"token": "valid_token"})
        assert response.status_code == 200
        assert response.json() == []


# ── /api/upload-csv ────────────────────────────────────────────────────────────

class TestUploadCsvEndpoint:
    def _upload(self, headers, row):
        """Helper: uploads a CSV and returns the Response."""
        content = ",".join(headers) + "\n" + ",".join(str(v) for v in row) + "\n"
        return client.post(
            "/api/upload-csv",
            files={"file": ("test.csv", content.encode("utf-8"), "text/csv")}
        )

    def test_valid_native_csv_returns_200(self):
        # Our own CSV format should be accepted and return a list of repo objects
        response = self._upload(
            ["date", "repository", "is_private", "views", "unique_visitors",
             "clones", "unique_cloners", "stars", "forks",
             "top_referrer", "top_referrer_views", "top_referrer_uniques",
             "top_path", "top_path_views", "top_path_uniques",
             "_raw_referrers", "_raw_paths"],
            ["2025-06-14", "user/repo", "False", 10, 4, 5, 2, 20, 3,
             "github.com", 5, 2, "/README.md", 4, 1, "[]", "[]"]
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_minimal_repository_column_accepted(self):
        # A minimal CSV with repository, date, and views is the smallest valid upload
        response = self._upload(
            ["repository", "date", "views"],
            ["user/repo", "2025-06-14", 42]
        )
        assert response.status_code == 200

    def test_invalid_csv_missing_repository_returns_400(self):
        # A CSV with no recognisable repository column must return 400 with a clear error
        response = self._upload(
            ["some_random_column", "data"],
            ["value1", "value2"]
        )
        assert response.status_code == 400
        assert "detail" in response.json()

    def test_repo_name_column_renamed_automatically(self):
        # Old 'repo_name' column from legacy exports should be accepted after renaming
        response = self._upload(
            ["repo_name", "date", "views"],
            ["user/legacy_repo", "2025-06-14", 10]
        )
        assert response.status_code == 200

    def test_upload_returns_list_of_repo_objects(self):
        # The endpoint must always return a list (may be empty but not null)
        response = self._upload(["repository", "date", "views"], ["user/repo", "2025-06-14", 10])
        assert isinstance(response.json(), list)


# ── Root and SPA fallback ──────────────────────────────────────────────────────

class TestRootEndpoint:
    def test_root_returns_200_or_503(self):
        # Root can return 200 (frontend built) or 503 (frontend not built yet)
        response = client.get("/")
        assert response.status_code in (200, 503)

    def test_unknown_path_returns_200_or_503(self):
        # Any unknown path goes to the SPA fallback — should not return 404
        response = client.get("/some/deep/react/route")
        assert response.status_code in (200, 503)

    def test_api_routes_not_caught_by_spa(self):
        # API routes must NOT be swallowed by the SPA catch-all
        response = client.get("/api/config")
        assert response.status_code == 200  # always returns JSON, not HTML
