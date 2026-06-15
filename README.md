<div align="center">

# Gitlytics
## 🚀 GitHub Traffic Monitor 📊

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/gitlytics?color=blue)](https://pypi.org/project/gitlytics/)
[![React](https://img.shields.io/badge/UI-React-61dafb?logo=react)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Automation](https://img.shields.io/badge/Data%20Backup-Automation%20Tool-purple?logo=github-actions)](https://github.com/ameyac11/github-traffic-monitor-automation)

**Beautiful GitHub traffic analytics for all your repositories — public and private.** 📈

Please consider giving this project a ⭐ if you find it helpful!

</div>

---

> **⚠️ NOTE: NAME AND TECH STACK UPGRADE!**
> This library was formerly known as `github-traffic-monitor`. We have officially rebranded to **`gitlytics`**! 
>
> In addition to the name change, we have migrated away from Streamlit. The dashboard is currently a base version working on a new and better **React + Vite** architecture, powered by a **FastAPI** backend!

---

A local-only GitHub traffic analytics tool with two modes:
- **🖥️ Web UI** — Beautiful React + FastAPI dashboard (recommended)
- **⌨️ CLI** — Terminal output + CSV export

View 14-day views, clones, referrers, and popular paths for **all** your repositories. Everything runs on your machine. Your token never leaves your device.

![GitHub Traffic Dashboard](https://raw.githubusercontent.com/ameyac11/gitlytics/main/assets/gittracker_thumnail1.png)

---

## 🚨 The 14-Day Catch (And How to Fix It!)

> **⚠️ Did you know?** GitHub normally **only saves your repository traffic data for 14 days**. After two weeks, your valuable views and clones data is permanently deleted.

**Don't lose your data!** We built a companion automation tool that runs silently in the background every 13 days using GitHub Actions to fetch and save your data permanently. 

👉 **[Set up GitHub Traffic Automation here](https://github.com/ameyac11/github-traffic-monitor-automation)** (It takes literally 2 minutes to set up!)

Once you have your automated data saved, you can seamlessly plug it right into this dashboard to visualize your beautiful, long-term historical charts.

---

## ✨ Features

| Feature | React UI | CLI |
|---|:---:|:---:|
| **Dual Mode Interface** (Live API & CSV Upload) | ✅ | ❌ |
| Token input (no hardcoding) | ✅ | ✅ |
| Upload & visualize historical CSV data | ✅ | ❌ |
| Summary metrics (views, clones, stars, forks) | ✅ | ✅ |
| Animated Area & Pie charts per repository | ✅ | ❌ |
| Per-repo daily views & clones chart | ✅ | ✅ |
| Top referrers & popular paths | ✅ | ✅ |
| Expandable repository list | ✅ | ❌ |
| Export to CSV | ✅ (download button) | ✅ (file) |
| Runs 100% locally | ✅ | ✅ |

---

## 🛠️ Installation

You can install the package directly from PyPI.

```bash
# Basic CLI installation
pip install gitlytics

# Installation with Dashboard UI support
pip install "gitlytics[dashboard]"
```

### Generating a GitHub Personal Access Token (PAT)
To use either the CLI or Dashboard, you'll need a GitHub token.

1. Go to **[GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)**
2. Click **Generate new token (classic)**
3. Select the **`repo`** scope — required to read traffic data for private repositories
4. Click **Generate token** and **copy it immediately**

> **🔒 Security Note:** Your token is completely safe, used only on your machine, and never sent to any external server. 

---

## 🖥️ Run: React Dashboard (Recommended)

If you installed with the `[dashboard]` extra, you can launch the beautiful web UI with a single command:

```bash
gitlytics dashboard
```

The server opens automatically in your terminal and you can view your dashboard at `http://localhost:8000`.

---

## ⌨️ Run: CLI (Terminal Mode)

If you just want terminal output or to export CSV files, you can use the CLI commands.

**Fetch data and print to terminal:**
```bash
gitlytics fetch --token ghp_your_token_here
```

**Fetch data and save to a specific CSV file:**
```bash
gitlytics fetch --token ghp_your_token_here --output my_report.csv
```

**Sync data (Append today's traffic to historical monthly CSVs):**
```bash
gitlytics sync --token ghp_your_token_here --dir ./data
```

You can also store your token in a `.env` file as `GITHUB_TOKEN=ghp_...` so you don't have to type it out every time.

---

## 📊 CSV Output Columns

| Column | Description |
|---|---|
| `Repository` | Full repo name (`user/repo`) |
| `Private` | `True` / `False` |
| `Stars` | Current star count |
| `Forks` | Current fork count |
| `Total Views` | Page views in last 14 days |
| `Unique Visitors` | Unique visitors in last 14 days |
| `Total Clones` | Clone count in last 14 days |
| `Unique Cloners` | Unique cloners in last 14 days |
| `Top Referrer` | Highest-traffic referral source |
| `Top Referrer Views` | View count from top referrer |
| `Top Path` | Most visited path |
| `Top Path Views` | View count for top path |
| `Fetched At` | UTC timestamp of the fetch |

---

## ⚠️ Requirements

- **Python 3.9+**
- A GitHub account with at least one repository
- A GitHub Personal Access Token with the `repo` scope

---

## 🛠️ Development Install

```bash
git clone https://github.com/ameyac11/gitlytics
cd gitlytics
pip install -e ".[dev,dashboard]"
```

## 🧪 Running Tests

```bash
pip install pytest
pytest
```

---

## 🌟 Show Your Support

If you find this project useful, please consider giving it a ⭐ on [GitHub](https://github.com/ameyac11/gitlytics)! It helps more people discover the tool.

---

## 📄 License

This project is licensed under the [Apache License 2.0](LICENSE).
