# Changelog

## [0.1.2] - 2026-06-16
### Fixed
- Traffic data now always returns exactly 14 days, even when GitHub omits dates with zero views.
- Background sync cron process no longer hangs silently — exits cleanly on expired tokens (401).
- Database no longer fragments when the sync cron job runs from a different working directory.
- Cron logs now appear correctly in all environments instead of being swallowed by stdout buffering.
- Star and fork counts now reflect the latest snapshot rather than an inflated cumulative sum.

### Changed
- JSON exports now strip private repositories by default (`export_public_only=True`) to prevent accidental leaks.
- Dashboard now preloads historical CSVs on boot instead of relying solely on live GitHub API data.
- React frontend now reads the API URL from `VITE_API_URL`, allowing independent deployment (e.g. Vercel).

### Added
- Added `docs/api_documentation.md` with code examples and parameter tables for `fetch_traffic`, `sync`, and `serve_dashboard`.
- `croniter` dependency for cron scheduling support.

## [0.1.1] - 2026-06-15
### Changed
- Migrated dashboard from Streamlit to React + Vite.
- Replaced Streamlit backend with FastAPI + Uvicorn.
- Renamed CLI command and project to `gitlytics`.
- Redesigned dashboard UI with dark mode and animated charts.
- PyPI build now bundles the compiled React frontend automatically.

### Removed
- Streamlit dashboard and runner.

## [0.1.0] - 2026-06-14
### Added
- Initial release.
- Core traffic fetching logic.
- CLI commands: `fetch`, `sync`, `dashboard`.
- Streamlit dashboard.
- GitHub Actions automation template.
- PyPI distribution support.