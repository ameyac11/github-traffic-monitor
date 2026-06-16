# Gitlytics Python Module API Documentation

Welcome to the Gitlytics Python API! When you `import gitlytics`, you have access to three powerful commands designed for data scientists, automation engineers, and frontend web developers.

---

## 1. `gitlytics.fetch_traffic()`
**The Snapshot Tool.** Reaches out to GitHub and pulls the current 14-day traffic data. **Note:** It actively zero-pads missing dates, mathematically guaranteeing a continuous 14-day timeseries even if a repository received 0 views on certain days. It does not read or write to your local CSV database (unless you ask it to save a file).

### Parameters
- `token` **(Required, str)**: Your GitHub Personal Access Token. **Must have the `repo` scope enabled**, or GitHub will silently return 404 Not Found errors.
- `repo_name` *(Optional, str | list)*: Fetches data for a specific repository (e.g. `"user/repo"`) or a batch array of specific repositories (e.g. `["user/repo1", "user/repo2"]`). If a requested repository does not exist or the token lacks access, it will immediately raise a `ValueError`. **Default:** `None` (Fetches all repositories).
- `print_table` *(Optional, bool)*: If `True`, prints an ASCII table to your console. The function will still return its normal data structure alongside printing. **Default:** `False`.
- `return_format` *(Optional, str)*: Determines the shape of the returned data. Options: `"dataframe"`, `"timeseries"`, `"summary"`. **Default:** `"dataframe"`.
- `save_file` *(Optional, str)*: A file path string (e.g., `"./data.csv"` or `"./chart.json"`). If provided, saves the output. Note: If `return_format="summary"`, you must provide a `.json` file extension as CSV is unsupported for flat dictionaries. **Default:** `None`.

### Variations & Expected Outputs

**1. Default Behavior (DataFrame)**
Returns a Pandas DataFrame formatted as Tidy Data (exactly 14 rows per repository).

> [!WARNING]
> **Data Integrity Note:** GitHub provides `top_referrer` and `top_path` as a 14-day rolling aggregate, not daily discrete values. Since our DataFrame assigns these rolling values to every daily row, do NOT use `.sum()` on referrer or path columns in Pandas, as you will artificially inflate the data by 1400%.

> [!WARNING]
> **Snapshot vs Cumulative Math:** When analyzing the DataFrame, do NOT use `.sum()` on `stars` or `forks`. These are daily snapshots, not cumulative values. Summing a repo with 100 stars over a 14-day period would falsely calculate 1,400 stars. Use `.iloc[-1]` or `.max()` to extract the true value.

```python
import gitlytics
df = gitlytics.fetch_traffic(token="ghp_xxx")
print(df[["date", "repository", "views", "clones"]].head(3))
```
**Output:**
```text
         date          repository  views  clones
0  2026-06-14  ameyac11/gitlytics    100      20
1  2026-06-15  ameyac11/gitlytics    150      30
2  2026-06-16  ameyac11/gitlytics    120      25
```

**2. The Snapshot Backup (`save_file`)**
Grabs the exact 14-day data and saves it straight to a file. Returns the underlying data structure to your script.
```python
# Saves the DataFrame format to a CSV
gitlytics.fetch_traffic(token="ghp_xxx", save_file="./my_snapshot.csv")

# Saves the Timeseries Dictionary format to a JSON
gitlytics.fetch_traffic(token="ghp_xxx", return_format="timeseries", save_file="./chart.json")
```
**Output:**
```text
[INFO] Saved traffic snapshot to ./my_snapshot.csv
```

**3. The Terminal Viewer (`print_table=True`)**
Returns the requested data structure AND prints a beautifully spaced text table right to your terminal.
```python
df = gitlytics.fetch_traffic(token="ghp_xxx", print_table=True)
```
**Output:**
```text
REPOSITORY                VIEWS    CLONES    TOP REFERRER
---------------------------------------------------------
ameyac11/gitlytics        1500     300       github.com
ameyac11/awesome-cli      850      120       google.com
---------------------------------------------------------
Total Account Views: 2350
```

**4. The Frontend Chart Data (`return_format="timeseries"`)**
Returns the 14-day daily array and repository metadata so you can feed it straight into a React/JS chart library. Features a top-level `account_totals` object for easy frontend math. The returned schema is 100% identical to the `export_json` schema in `sync()`.

> [!WARNING]
> **Unique Visitors Math Trap:** Because GitHub anonymizes and deduplicates traffic data internally, it is mathematically impossible to sum unique visitors across multiple repositories perfectly. The `unique_visitors` total provided in the `account_totals` is actually a "Sum of Repo Uniques", which is a slight overestimation.

```python
chart_data = gitlytics.fetch_traffic(token="ghp_xxx", repo_name="ameyac11/gitlytics", return_format="timeseries")
print(chart_data)
```
**Output:**
```json
{
  "account_totals": {
    "total_views": 2350,
    "total_clones": 420,
    "unique_visitors": 650,
    "unique_cloners": 140,
    "total_stars": 850,
    "total_forks": 240
  },
  "repositories": {
    "ameyac11/gitlytics": {
      "timeseries": [
        {
          "date": "2026-06-15", 
          "views": 45, 
          "unique_visitors": 12, 
          "clones": 5, 
          "unique_cloners": 2
        },
        ... (14 days of data!) ...
      ],
      "totals": {
        "is_private": false,
        "stars": 450,
        "forks": 120,
        "top_referrer": "github.com",
        "top_path": "/ameyac11/gitlytics"
      }
    }
  }
}
```

**5. The Summary (`return_format="summary"`)**
Returns flat totals for the account and its repositories. If `repo_name` is omitted, it includes every repository.
```python
stats = gitlytics.fetch_traffic(token="ghp_xxx", return_format="summary")
```
**Output:** 
```json
{
  "account_totals": {
    "total_views": 2350,
    "total_clones": 420,
    "unique_visitors": 650,
    "unique_cloners": 140,
    "total_stars": 850,
    "total_forks": 240
  },
  "repositories": {
    "ameyac11/gitlytics": {
      "is_private": false,
      "total_views": 1500, 
      "total_clones": 300, 
      "unique_visitors": 450,
      "unique_cloners": 100,
      "stars": 450,
      "forks": 120
    },
    "ameyac11/awesome-cli": {
      "is_private": false,
      "total_views": 850, 
      "total_clones": 120, 
      "unique_visitors": 200,
      "unique_cloners": 40,
      "stars": 400,
      "forks": 120
    }
  }
}
```

---

## 2. `gitlytics.sync()`
**The Database Tool.** It compares GitHub to your local files and APPENDS only the new days, guaranteeing you never lose historical data. **Returns `None`.**

### Parameters
- `token` **(Required, str)**: Your GitHub Personal Access Token. **Must have the `repo` scope enabled.**
- `repo_name` *(Optional, str | list)*: Tell the automation to only backup specific repositories. **Default:** `None` (Backs up all repos).
- `data_dir` *(Optional, str)*: Where to securely save the CSV database files. **Default:** `"./data"`.
- `output_mode` *(Optional, str)*: Controls chunking. Options: `"monthly"`, `"yearly"`. **Default:** `"monthly"` (starts a new file on the 1st of each month).
- `schedule_cron` *(Optional, str)*: A cron expression. Blocks the calling thread with 0% CPU usage using `time.sleep()` until the next trigger. The cron job is wrapped in a global exception handler (Wi-Fi drops will simply pause the daemon), but if it detects a **401 Unauthorized** error (e.g. an expired token), it will instantly terminate to prevent becoming a zombie process. Stop with `Ctrl+C`. **Default:** `None`.
- `export_json` *(Optional, str)*: A file path string (e.g., `"./traffic.json"`). Automatically completely overwrites this file with your entire historical database on every sync. On the first run, it fetches the 14 days, writes the CSV, and immediately dumps the JSON. **Default:** `None`.
- `export_public_only` *(Optional, bool)*: Security firewall for `export_json`. If `True`, the JSON export will strictly omit all private repositories, ensuring your confidential repository names and traffic data are never leaked if you host the JSON on a public React portfolio. This does NOT affect the local CSV database, which securely backs up both public and private repos. **Default:** `True`.

### Variations & Expected Outputs

**1. The Standard Backup (Runs Once)**
Fetches data and safely appends it to monthly files like `data/traffic_2026-06.csv`.
```python
gitlytics.sync(token="ghp_xxx", data_dir="./data")
```
**Output:**
```text
[INFO] Successfully processed traffic data. Added 14 new daily records to data/traffic_2026-06.csv
```

**2. The Yearly Output Mode**
Groups data by year instead of month. Automatically starts a new file every January 1st.
```python
gitlytics.sync(token="ghp_xxx", data_dir="./data", output_mode="yearly")
```
**Output:**
```text
[INFO] Successfully processed traffic data. Added 14 new daily records to data/traffic_2026.csv
```

**3. The Ultimate Background Automation (`schedule_cron`)**
Turns your Python script into a permanent background cron job! Stop the cron job by pressing `Ctrl+C`.
```python
print("Starting Background Cron Job...")
# Runs every 13 days because GitHub provides 14 days of history (ensures 1 day of overlap buffer)
gitlytics.sync(token="ghp_xxx", data_dir="./data", schedule_cron="0 17 */13 * *")
```
**Output:**
```text
Starting Background Cron Job...
[INFO] Scheduled next sync for 2026-06-29 17:00:00. Sleeping...
```

**4. The Frontend Superweapon (`export_json`)**
Every time it syncs, it ALSO dumps your entire database perfectly formatted into a JSON file for your static React website! The schema is 100% identical to `fetch_traffic(return_format="timeseries")`.
```python
gitlytics.sync(
    token="ghp_xxx", 
    schedule_cron="0 0 * * *",
    export_json="./my-website/traffic.json"
)
```
**Output (Console):**
```text
[INFO] Appended 1 new day to data/traffic_2026-06.csv
[INFO] Exported 180 days of historical data to ./my-website/traffic.json
[INFO] Sleeping until tomorrow at 00:00:00...
```

---

## 3. `gitlytics.serve_dashboard()`
**The Visualizer.** Programmatically boots up the FastAPI backend and serves the React dashboard locally. Blocks the thread indefinitely while serving. Stop the server by pressing `Ctrl+C`.

*Note: Requires FastAPI and Uvicorn. Install via `pip install "gitlytics[dashboard]"`.*

### Parameters
- `token` *(Optional, str)*: Your GitHub Personal Access Token. If provided, it auto-authenticates the dashboard backend, completely bypassing the web login screen. **Default:** `None`.
- `data_dir` *(Optional, str)*: Path to your local CSV database (e.g., `"./data"`). If provided, the dashboard will auto-load your entire historical database instead of just fetching the live 14-day snapshot! **Default:** `None`.
- `host` *(Optional, str)*: The network host. **Default:** `"127.0.0.1"` (Restricted to localhost for security).
- `port` *(Optional, int)*: The network port. **Default:** `8000`.

### Variations & Expected Outputs

**1. Standard Local Run (Live 14-Day Data)**
```python
gitlytics.serve_dashboard(port=8080)
```
**Output:**
```text
INFO:     Started server process [15016]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8080 (Press CTRL+C to quit)
```

**2. The Historical Database Viewer (`data_dir`)**
Instantly visualizes your entire 6-month (or 5-year) local CSV database without needing to manually upload files in the browser.
```python
gitlytics.serve_dashboard(data_dir="./data", port=8000)
```

**3. The Headless TV Display (`token`)**
Perfect for displaying the dashboard on an office TV permanently without needing to login through the browser.
```python
gitlytics.serve_dashboard(token="ghp_xxx", port=8000)
```
