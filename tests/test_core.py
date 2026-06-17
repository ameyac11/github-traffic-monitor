"""
tests/test_core.py
Unit tests for gitlytics/core.py — network calls are mocked so these run offline.
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from gitlytics.core import (
    validate_token, get_user_profile, make_headers,
    get_all_repos, get_repo_traffic, build_tidy_rows,
    fetch_traffic_data, pad_traffic_data, print_repo_table
)


# ── make_headers ──────────────────────────────────────────────────────────────

class TestMakeHeaders:
    def test_returns_dict(self):
        # Should give back a plain dict with auth info
        result = make_headers("mytoken")
        assert isinstance(result, dict)

    def test_contains_authorization(self):
        # The Authorization header must use the Bearer scheme
        result = make_headers("mytoken")
        assert result["Authorization"] == "Bearer mytoken"

    def test_contains_accept_header(self):
        # GitHub's v3 JSON media type must be set
        result = make_headers("mytoken")
        assert "application/vnd.github" in result.get("Accept", "")


# ── validate_token ────────────────────────────────────────────────────────────

class TestValidateToken:
    @patch("gitlytics.core.requests.get")
    def test_valid_token_returns_true_and_login(self, mock_get):
        # A 200 response with a login field means the token is good
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "testuser"}
        mock_get.return_value = mock_response

        valid, username = validate_token("valid_token")
        assert valid is True
        assert username == "testuser"

    @patch("gitlytics.core.requests.get")
    def test_401_returns_false(self, mock_get):
        # 401 = wrong token or it's expired
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        valid, msg = validate_token("bad_token")
        assert valid is False
        assert "401" in msg

    @patch("gitlytics.core.requests.get")
    def test_403_returns_false(self, mock_get):
        # 403 = token exists but doesn't have enough permissions
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        valid, msg = validate_token("limited_token")
        assert valid is False
        assert "403" in msg

    @patch("gitlytics.core.requests.get")
    def test_network_error_returns_false(self, mock_get):
        # Simulate being offline — should return False, not crash
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("No internet")
        valid, msg = validate_token("any_token")
        assert valid is False
        assert "No internet" in msg


# ── get_user_profile ──────────────────────────────────────────────────────────

class TestGetUserProfile:
    @patch("gitlytics.core.requests.get")
    def test_returns_all_fields(self, mock_get):
        # Should hand back login, name, and avatar_url from the GitHub response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "login": "ameyac11",
            "name": "Ameya Chopade",
            "avatar_url": "https://avatars.githubusercontent.com/u/123"
        }
        mock_get.return_value = mock_response

        profile = get_user_profile("token")
        assert profile["login"] == "ameyac11"
        assert profile["name"] == "Ameya Chopade"
        assert profile["avatar_url"].startswith("https://")

    @patch("gitlytics.core.requests.get")
    def test_null_name_falls_back_to_login(self, mock_get):
        # GitHub allows users to leave their display name blank — fall back to username
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "ameyac11", "name": None, "avatar_url": "https://x"}
        mock_get.return_value = mock_response

        profile = get_user_profile("token")
        assert profile["name"] == "ameyac11"  # login used as fallback

    @patch("gitlytics.core.requests.get")
    def test_non_200_returns_empty_strings(self, mock_get):
        # If the API call fails, return empty strings so callers don't have to handle None
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        profile = get_user_profile("bad_token")
        assert profile == {"login": "", "name": "", "avatar_url": ""}


# ── pad_traffic_data ──────────────────────────────────────────────────────────

class TestPadTrafficData:
    def test_always_returns_14_days(self):
        # GitHub only returns days with activity — we always want a full 14-day window
        traffic = {"views": {"views": []}, "clones": {"clones": []}}
        result = pad_traffic_data(traffic)
        assert len(result) == 14

    def test_fills_zeros_for_missing_days(self):
        # Days with no activity should get 0 counts, not be skipped
        traffic = {"views": {"views": []}, "clones": {"clones": []}}
        result = pad_traffic_data(traffic)
        assert all(r["views"] == 0 for r in result)

    def test_uses_api_data_for_active_days(self):
        # Actual traffic counts from GitHub should appear in the right day slot
        traffic = {
            "views": {"views": [{"timestamp": "2025-06-14T00:00:00Z", "count": 42, "uniques": 10}]},
            "clones": {"clones": [{"timestamp": "2025-06-14T00:00:00Z", "count": 5, "uniques": 3}]}
        }
        result = pad_traffic_data(traffic)
        day = next(r for r in result if r["date"] == "2025-06-14")
        assert day["views"] == 42
        assert day["clones"] == 5


# ── build_tidy_rows ───────────────────────────────────────────────────────────

class TestBuildTidyRows:
    def test_returns_14_rows(self):
        # One row per calendar day — always 14 rows for each repo
        repo = {"full_name": "user/repo", "private": False, "stargazers_count": 5, "forks_count": 2}
        traffic = {"views": {"views": []}, "clones": {"clones": []}, "referrers": [], "paths": []}
        rows = build_tidy_rows(repo, traffic)
        assert len(rows) == 14

    def test_each_row_has_repository_field(self):
        # Every row must carry the repo name so the DataFrame can be grouped
        repo = {"full_name": "user/repo", "private": False, "stargazers_count": 0, "forks_count": 0}
        traffic = {"views": {"views": []}, "clones": {"clones": []}, "referrers": [], "paths": []}
        rows = build_tidy_rows(repo, traffic)
        assert all(r["repository"] == "user/repo" for r in rows)

    def test_raw_fields_are_json_strings(self):
        # _raw_referrers and _raw_paths must be JSON strings — the dashboard decodes them
        repo = {"full_name": "u/r", "private": False, "stargazers_count": 0, "forks_count": 0}
        traffic = {
            "views": {"views": []}, "clones": {"clones": []},
            "referrers": [{"referrer": "github.com", "count": 5, "uniques": 3}],
            "paths": []
        }
        import json
        rows = build_tidy_rows(repo, traffic)
        assert json.loads(rows[0]["_raw_referrers"])[0]["referrer"] == "github.com"


# ── fetch_traffic_data (integration-style with mocks) ─────────────────────────

class TestFetchTrafficData:
    @patch("gitlytics.core.get_all_repos")
    @patch("gitlytics.core.get_repo_traffic")
    def test_returns_dataframe(self, mock_traffic, mock_repos):
        # Should always return a DataFrame — even when a repo has zero traffic
        mock_repos.return_value = [
            {"full_name": "user/repo", "private": False, "stargazers_count": 0, "forks_count": 0}
        ]
        mock_traffic.return_value = {
            "views": {"views": []}, "clones": {"clones": []},
            "referrers": [], "paths": []
        }
        result = fetch_traffic_data("token")
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 14  # 14-day window even with zero traffic

    @patch("gitlytics.core.get_all_repos")
    def test_empty_repo_list_returns_empty_df(self, mock_repos):
        # If the token has no repos at all, return an empty DataFrame gracefully
        mock_repos.return_value = []
        result = fetch_traffic_data("token")
        assert isinstance(result, pd.DataFrame)
        assert result.empty


# ── print_repo_table ──────────────────────────────────────────────────────────

class TestPrintRepoTable:
    def test_empty_df_prints_no_data_message(self, capsys):
        # When there's nothing to show, just print a friendly message
        print_repo_table(pd.DataFrame())
        captured = capsys.readouterr()
        assert "No data" in captured.out

    def test_prints_header_with_data(self, capsys):
        # A non-empty DataFrame should produce a table with a REPOSITORY header
        df = pd.DataFrame([{
            "repository": "user/repo", "views": 10, "unique_visitors": 5,
            "clones": 3, "unique_cloners": 2, "stars": 1, "forks": 0,
            "top_referrer": "github.com"
        }])
        print_repo_table(df)
        captured = capsys.readouterr()
        assert "REPOSITORY" in captured.out
