"""
streamlit_app.py
Frontend only — all logic imported from github_traffic_fetch.py.

Run with:
    streamlit run streamlit_app.py
"""

import sys
from datetime import datetime, timezone as _tz
import streamlit as st
import pandas as pd

# Import all logic from our module
from github_traffic_fetch import (
    validate_token,
    fetch_all_traffic,
    to_csv_bytes,
)

# ── Guard against running with plain Python ───────────────────────────────────
if not st.runtime.exists():
    print("\n❌  Use:  streamlit run streamlit_app.py\n")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
#  Page config — must come first
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GitHub Traffic Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
#  Styles — dark, clean, minimal
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Base font and background */
html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif;
    background-color: #0d1117;
    color: #c9d1d9;
}

/* Hide Streamlit deploy button and branding */
#MainMenu                            { visibility: hidden; }
footer                               { visibility: hidden; }
[data-testid="stToolbar"]            { display: none !important; }
[data-testid="stDecoration"]         { display: none !important; }
[data-testid="stStatusWidget"]       { display: none !important; }
[data-testid="stHeaderDeployButton"] { display: none !important; }
[data-testid="stElementToolbar"]     { display: none !important; }

/* Sidebar background */

section[data-testid="stSidebar"] {
    background: #161b22;
    border-right: 1px solid #21262d;
}

/* Token password field container */
.stTextInput > div[data-baseweb="input"] {
    background-color: #0d1117 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.stTextInput > div[data-baseweb="input"]:focus-within {
    border-color: #58a6ff !important;
    box-shadow: 0 0 0 3px rgba(88,166,255,0.12) !important;
}

/* Inner input field styling */
.stTextInput input {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    color: #e6edf3 !important;
    font-size: 0.875rem;
}
.stTextInput input:focus {
    outline: none !important;
    border: none !important;
}

/* Hide 'Press Enter to apply' hint to prevent overlap with eye icon */
div[data-testid="InputInstructions"] {
    display: none !important;
}

/* Standard Action Buttons */
.stButton > button, [data-testid="stDownloadButton"] > button {
    width: 100%;
    background-color: #21262d !important;
    color: #c9d1d9 !important;
    border: 1px solid rgba(240, 246, 252, 0.1) !important;
    border-radius: 6px !important;
    padding: 0.5rem 1rem !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
    transition: all 0.2s ease !important;
    box-shadow: none !important;
}
.stButton > button:hover, [data-testid="stDownloadButton"] > button:hover {
    background-color: #30363d !important;
    border-color: #8b949e !important;
}

/* Metric cards */
[data-testid="metric-container"] {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 12px;
    padding: 0.8rem 1rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.35);
    transition: border-color 0.2s, box-shadow 0.2s, transform 0.2s;
    position: relative;
    overflow: hidden;
}
[data-testid="metric-container"]::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #58a6ff, #3fb950);
    opacity: 0;
    transition: opacity 0.2s;
}
[data-testid="metric-container"]:hover {
    border-color: #30363d;
    box-shadow: 0 6px 24px rgba(0,0,0,0.45);
    transform: translateY(-2px);
}
[data-testid="metric-container"]:hover::before { opacity: 1; }

[data-testid="metric-container"] label {
    color: #8b949e !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
[data-testid="stMetricValue"] {
    color: #e6edf3 !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] { color: #3fb950 !important; font-size: 0.8rem !important; }

/* Expandable repo sections */
[data-testid="stExpander"] {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 10px;
    margin-bottom: 8px;
    transition: border-color 0.2s;
}
[data-testid="stExpander"]:hover { border-color: #30363d; }
[data-testid="stExpander"] summary {
    color: #e6edf3 !important;
    font-weight: 500;
    font-size: 0.9rem;
    padding: 0.85rem 1rem;
}

/* Data tables */
[data-testid="stDataFrame"] {
    border: 1px solid #21262d;
    border-radius: 10px;
    overflow: hidden;
}

/* Loading bar */
[data-testid="stProgressBar"] > div {
    background: linear-gradient(90deg, #1f6feb, #58a6ff) !important;
    border-radius: 4px;
}

/* Divider lines */
hr { border: none; border-top: 1px solid #21262d; margin: 1rem 0; }

/* Thin custom scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #484f58; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Session state — initialise once
# ─────────────────────────────────────────────────────────────────────────────
# Default values for first run
DEFAULTS = {
    "authenticated": False,
    "token":         "",
    "username":      "",
    "name":          "",
    "avatar_url":    "",
    "df":            None,
    "fetched":       False,
}
for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── Always-visible floating sidebar toggle button injected via JS ─────────────
st.markdown("""
<script>
(function() {
    // Remove any existing custom toggle to avoid duplicates
    function removeOld() {
        var old = document.getElementById('custom-sidebar-btn');
        if (old) old.remove();
    }

    function createBtn() {
        removeOld();
        var btn = document.createElement('button');
        btn.id = 'custom-sidebar-btn';
        btn.title = 'Toggle sidebar';
        btn.innerHTML = '&#9776;';
        btn.style.cssText = [
            'position: fixed',
            'top: 12px',
            'left: 12px',
            'width: 36px',
            'height: 36px',
            'border-radius: 50%',
            'background: #21262d',
            'border: 1px solid #444c56',
            'color: #c9d1d9',
            'font-size: 16px',
            'cursor: pointer',
            'z-index: 9999999',
            'display: flex',
            'align-items: center',
            'justify-content: center',
            'box-shadow: 0 2px 8px rgba(0,0,0,0.7)',
            'transition: background 0.2s ease',
            'outline: none',
        ].join(' !important;') + ' !important';

        btn.onmouseenter = function() { this.style.background = '#30363d'; };
        btn.onmouseleave = function() { this.style.background = '#21262d'; };

        btn.onclick = function() {
            // Click Streamlit's real hidden toggle button
            var real = document.querySelector('[data-testid="collapsedControl"] button') ||
                       document.querySelector('button[kind="header"]') ||
                       document.querySelector('[data-testid="collapsedControl"]');
            if (real) { real.click(); }
        };

        document.body.appendChild(btn);
    }

    // Wait for DOM then create button
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createBtn);
    } else {
        createBtn();
    }

    // Re-create on Streamlit re-renders (MutationObserver on body)
    var observer = new MutationObserver(function(muts) {
        if (!document.getElementById('custom-sidebar-btn')) { createBtn(); }
    });
    observer.observe(document.body, { childList: true, subtree: false });
})();
</script>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:

    # App logo and title
    st.markdown("""
    <div style="text-align:center; padding: 0.5rem 0 1.5rem 0;">
        <div style="font-size:2.2rem;">🚀</div>
        <div style="font-size:1rem; font-weight:700; color:#e6edf3;">GitHub Traffic</div>
        <div style="font-size:0.72rem; color:#8b949e; margin-top:2px;">Local Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Show token input when not logged in ───────────────────────────────────
    if not st.session_state.authenticated:

        st.markdown("<p style='font-size:0.72rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#8b949e;margin-bottom:4px;'>Your GitHub Token</p>", unsafe_allow_html=True)

        # Password field — token stays hidden
        token_input = st.text_input(
            "token",
            type="password",
            placeholder="ghp_xxxxxxxxxxxxxxxxxxxx",
            label_visibility="collapsed",
            key="token_widget",
        )
        st.caption("💡 Needs `repo` scope for private repos")

        # Validate token on button click
        if st.button("🔐  Connect to GitHub", key="connect_btn"):
            if not token_input.strip():
                st.error("Please enter your token first.")
            else:
                with st.spinner("Authenticating…"):
                    ok, uname, avatar, name = validate_token(token_input.strip())

                if ok:
                    # Save auth info to session
                    st.session_state.update({
                        "authenticated": True,
                        "token":         token_input.strip(),
                        "username":      uname,
                        "name":          name or uname,
                        "avatar_url":    avatar,
                        "fetched":       False,
                        "df":            None,
                    })
                    st.rerun()
                else:
                    st.error(f"❌ {uname}")  # uname holds the error message on failure

    # ── Show controls when logged in ─────────────────────────────────────────
    else:

        # Profile card details
        st.markdown(f"""
        <div style="background:#0d1117;border:1px solid #21262d;border-radius:10px;
                    padding:12px 14px;margin-bottom:1rem;display:flex;align-items:center;gap:10px;">
            <img src="{st.session_state.avatar_url}"
                 style="width:36px;height:36px;border-radius:50%;border:2px solid #30363d;" />
            <div>
                <div style="font-weight:600;font-size:0.875rem;color:#e6edf3;">{st.session_state.name}</div>
                <div style="font-size:0.72rem;color:#8b949e;">@{st.session_state.username}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # Search filter inputs
        st.markdown("<p style='font-size:0.72rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#8b949e;margin-bottom:4px;'>🔍 Filter Repositories</p>", unsafe_allow_html=True)
        search = st.text_input(
            "Search",
            placeholder="Search repositories...",
            label_visibility="collapsed",
            key="search_box",
        )

        # Slide charts limits config
        if st.session_state.df is not None and not st.session_state.df.empty:
            st.markdown("<p style='font-size:0.72rem;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;color:#8b949e;margin-top:12px;margin-bottom:4px;'>📊 Chart Limit</p>", unsafe_allow_html=True)
            top_n = st.slider(
                "Show top N",
                5,
                min(30, len(st.session_state.df)),
                min(10, len(st.session_state.df)),
                key="top_n_slider",
                label_visibility="collapsed",
            )
        else:
            top_n = 10

        st.markdown("---")

        # Export CSV files locally
        if st.session_state.df is not None and not st.session_state.df.empty:
            fname = f"github_traffic_{datetime.now(_tz.utc).strftime('%Y-%m-%d')}.csv"
            st.download_button(
                label="⬇️  Download CSV",
                data=to_csv_bytes(st.session_state.df),
                file_name=fname,
                mime="text/csv",
                key="dl_btn",
            )
            st.markdown("---")

        # Re-fetch new traffic statistics
        if st.button("🔄  Refresh Data", key="fetch_btn"):
            st.session_state.fetched = False
            st.session_state.df     = None
            st.rerun()

        # Disconnect and reset session
        if st.button("🚪  Disconnect", key="logout_btn"):
            for k, v in DEFAULTS.items():
                st.session_state[k] = v
            st.rerun()

    # Flowing privacy metadata footer
    st.markdown("""
    <div style="margin-top: 2rem; padding: 10px; border-top: 1px solid #21262d; text-align: center;">
        <div style="font-size:0.68rem;color:#8b949e;line-height:1.6;">
            🔒 Token stays on your machine<br>Never sent anywhere
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
#  Main content area
# ─────────────────────────────────────────────────────────────────────────────

# Page title strip - only show when fetching or not logged in to save space
if not st.session_state.authenticated or not st.session_state.fetched or st.session_state.df is None:
    st.markdown("""
    <div style="padding: 1.5rem 0 1rem 0; border-bottom: 1px solid #21262d; margin-bottom: 1.5rem;">
        <h1 style="font-size:1.75rem;font-weight:800;color:#e6edf3;margin:0 0 0.25rem 0;letter-spacing:-0.02em;">
            GitHub Traffic Dashboard
        </h1>
        <p style="font-size:0.875rem;color:#8b949e;margin:0;">
            14-day analytics for all your repos — 100% local, fully private.
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    # Minimal spacer when dashboard is ready
    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)


# ── Landing page — not logged in ──────────────────────────────────────────────
if not st.session_state.authenticated:

    # Quick start card
    st.markdown("""
    <div style="background:#161b22;border:1px solid #21262d;border-radius:12px;
                padding:2rem 2.5rem;max-width:560px;margin:1rem 0;">
        <h3 style="font-size:1rem;font-weight:700;color:#e6edf3;margin:0 0 0.75rem 0;">
            👈 Get started in 3 steps
        </h3>
        <ol style="color:#8b949e;font-size:0.875rem;line-height:2.2;margin:0;padding-left:1.25rem;">
            <li>Open sidebar with the <strong style="color:#c9d1d9">&gt;</strong> button (top-left)</li>
            <li>Paste your <strong style="color:#c9d1d9">GitHub Personal Access Token</strong></li>
            <li>Click <strong style="color:#3fb950">Connect to GitHub</strong></li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    # How to create a token, collapsed by default
    with st.expander("📖  How to create a Personal Access Token"):
        st.markdown("""
1. Go to **[GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)**
2. Click **Generate new token (classic)**
3. Give it a name like *Traffic Dashboard*
4. Check the **`repo`** scope
5. Generate and copy the token immediately
6. Paste it in the sidebar 👈
""")
    st.stop()


# ── Fetch data if not already loaded ──────────────────────────────────────────
if not st.session_state.fetched or st.session_state.df is None:

    with st.status("Fetching GitHub Traffic Data...", expanded=True) as status:
        # Show a live progress bar while fetching
        prog = st.progress(0, text="Fetching repositories…")

        def _on_progress(frac: float):
            prog.progress(frac, text=f"Fetching traffic…  {int(frac * 100)}%")

        # fetch_all_traffic comes from github_traffic_fetch.py
        df = fetch_all_traffic(st.session_state.token, progress_cb=_on_progress)
        status.update(label="Fetching complete!", state="complete", expanded=False)

    st.session_state.df      = df
    st.session_state.fetched = True
    st.rerun()  # Rerun to update sidebar with download button and slider


# Pull from session for this render
df = st.session_state.df

# Nothing came back — warn and stop
if df is None or df.empty:
    st.warning("No repositories found, or no traffic data available for this token.")
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
#  Overview metrics row
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<p style='font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#8b949e;margin-bottom:0.75rem;'>Overview — Last 14 Days</p>", unsafe_allow_html=True)

c1, c2, c3, c4, c5, c6 = st.columns(6)
# Show totals across all repos
c1.metric("Repositories",    f"{len(df):,}")
c2.metric("Total Views",     f"{int(df['Total Views'].sum()):,}")
c3.metric("Unique Visitors", f"{int(df['Unique Visitors'].sum()):,}")
c4.metric("Total Clones",    f"{int(df['Total Clones'].sum()):,}")
c5.metric("⭐ Stars",         f"{int(df['Stars'].sum()):,}")
c6.metric("🍴 Forks",         f"{int(df['Forks'].sum()):,}")


# ─────────────────────────────────────────────────────────────────────────────
#  Bar charts — top N repos
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<p style='font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#8b949e;margin:2rem 0 0.75rem 0;'>Top Repositories by Traffic</p>", unsafe_allow_html=True)

# Build short labels list
df["_short"] = df["Repository"].str.split("/").str[1]

# Render primary traffic charts
col1, col2 = st.columns(2)
with col1:
    st.markdown("<p style='font-size:0.8rem;font-weight:600;color:#c9d1d9;margin-bottom:0.5rem;'>👁️ Views</p>", unsafe_allow_html=True)
    top_v = df.nlargest(top_n, "Total Views").set_index("_short")[["Total Views", "Unique Visitors"]]
    st.bar_chart(top_v, color=["#58a6ff", "#3fb950"])

with col2:
    st.markdown("<p style='font-size:0.8rem;font-weight:600;color:#c9d1d9;margin-bottom:0.5rem;'>📥 Clones</p>", unsafe_allow_html=True)
    top_c = df.nlargest(top_n, "Total Clones").set_index("_short")[["Total Clones", "Unique Cloners"]]
    st.bar_chart(top_c, color=["#ff7b72", "#e3b341"])

# Render secondary metadata charts
col3, col4 = st.columns(2)
with col3:
    st.markdown("<p style='font-size:0.8rem;font-weight:600;color:#c9d1d9;margin-bottom:0.5rem;'>⭐ Stars</p>", unsafe_allow_html=True)
    st.bar_chart(df.nlargest(top_n, "Stars").set_index("_short")[["Stars"]], color=["#e3b341"])

with col4:
    st.markdown("<p style='font-size:0.8rem;font-weight:600;color:#c9d1d9;margin-bottom:0.5rem;'>🍴 Forks</p>", unsafe_allow_html=True)
    st.bar_chart(df.nlargest(top_n, "Forks").set_index("_short")[["Forks"]], color=["#a371f7"])


# ─────────────────────────────────────────────────────────────────────────────
#  Full summary table
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<p style='font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#8b949e;margin:2rem 0 0.75rem 0;'>All Repositories</p>", unsafe_allow_html=True)

# Columns shown in dataframe
DISPLAY_COLS = [
    "Repository", "Private", "Stars", "Forks",
    "Total Views", "Unique Visitors", "Total Clones", "Unique Cloners",
    "Top Referrer", "Top Referrer Views", "Top Path", "Top Path Views",
]

# Render primary repositories table
st.dataframe(
    df[DISPLAY_COLS],
    use_container_width=True,
    height=400,
    hide_index=True,
    column_config={
        "Repository":         st.column_config.TextColumn("Repository", width="medium", help="Full repository name"),
        "Private":            st.column_config.CheckboxColumn("Private", help="Is the repository private?"),
        "Stars":              st.column_config.NumberColumn("Stars ⭐", format="%d"),
        "Forks":              st.column_config.NumberColumn("Forks 🍴", format="%d"),
        "Total Views":        st.column_config.ProgressColumn("Views", format="%d", min_value=0, max_value=int(df["Total Views"].max()) or 1),
        "Unique Visitors":    st.column_config.NumberColumn("Visitors 👥", format="%d"),
        "Total Clones":       st.column_config.ProgressColumn("Clones", format="%d", min_value=0, max_value=int(df["Total Clones"].max()) or 1),
        "Unique Cloners":     st.column_config.NumberColumn("Cloners 👥", format="%d"),
        "Top Referrer":       st.column_config.TextColumn("Top Referrer"),
        "Top Referrer Views": st.column_config.NumberColumn("Referrer Views", format="%d"),
        "Top Path":           st.column_config.TextColumn("Top Path"),
        "Top Path Views":     st.column_config.NumberColumn("Path Views", format="%d"),
    },
)


# ─────────────────────────────────────────────────────────────────────────────
#  Per-repo expandable detail
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<p style='font-size:0.72rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:#8b949e;margin:2rem 0 0.75rem 0;'>Repository Detail</p>", unsafe_allow_html=True)

# Filter list using search
filtered = df[df["Repository"].str.contains(search, case=False, na=False)] if search else df

if filtered.empty:
    st.info("No repositories match your search.")

for _, row in filtered.iterrows():

    # Private vs public colour
    is_private  = row["Private"]
    vis_label   = "🔒 Private" if is_private else "🌐 Public"
    vis_color   = "#f78166"    if is_private else "#3fb950"

    # Expander title shows key numbers at a glance
    label = f"{row['Repository'].split('/')[1]}  ·  {int(row['Total Views']):,} views  ·  {int(row['Total Clones']):,} clones"

    with st.expander(label):

        # Full repo name and visibility badge
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:1rem;">
            <span style="font-size:0.875rem;font-weight:700;color:#e6edf3;">{row['Repository']}</span>
            <span style="font-size:0.7rem;font-weight:600;color:{vis_color};
                         background:{vis_color}18;border:1px solid {vis_color}40;
                         border-radius:20px;padding:1px 9px;">{vis_label}</span>
        </div>
        """, unsafe_allow_html=True)

        # Six metric cards in a row
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Views",           f"{int(row['Total Views']):,}")
        m2.metric("Unique Visitors", f"{int(row['Unique Visitors']):,}")
        m3.metric("Clones",          f"{int(row['Total Clones']):,}")
        m4.metric("Unique Cloners",  f"{int(row['Unique Cloners']):,}")
        m5.metric("⭐ Stars",         f"{int(row['Stars']):,}")
        m6.metric("🍴 Forks",         f"{int(row['Forks']):,}")

        # Daily line charts side by side
        d_views  = row.get("_daily_views",  [])
        d_clones = row.get("_daily_clones", [])

        if d_views or d_clones:
            ch1, ch2 = st.columns(2)

            if d_views:
                with ch1:
                    dv = pd.DataFrame(d_views)
                    dv["date"] = pd.to_datetime(dv["timestamp"]).dt.date
                    dv = dv.set_index("date")[["count", "uniques"]].rename(columns={"count": "Views", "uniques": "Unique"})
                    st.markdown("<p style='font-size:0.78rem;font-weight:600;color:#8b949e;margin-bottom:4px;'>📅 Daily Views</p>", unsafe_allow_html=True)
                    st.line_chart(dv, color=["#58a6ff", "#1f6feb"])

            if d_clones:
                with ch2:
                    dc = pd.DataFrame(d_clones)
                    dc["date"] = pd.to_datetime(dc["timestamp"]).dt.date
                    dc = dc.set_index("date")[["count", "uniques"]].rename(columns={"count": "Clones", "uniques": "Unique"})
                    st.markdown("<p style='font-size:0.78rem;font-weight:600;color:#8b949e;margin-bottom:4px;'>📥 Daily Clones</p>", unsafe_allow_html=True)
                    st.line_chart(dc, color=["#f78166", "#ff7b72"])

        # Referrers and paths tables side by side
        refs  = row.get("_referrers", [])
        paths = row.get("_paths",     [])

        if refs or paths:
            t1, t2 = st.columns(2)

            if refs:
                with t1:
                    st.markdown("<p style='font-size:0.78rem;font-weight:600;color:#8b949e;margin-bottom:4px;'>🔗 Top Referrers</p>", unsafe_allow_html=True)
                    ref_df = pd.DataFrame(refs)[["referrer", "count", "uniques"]]
                    st.dataframe(
                        ref_df.rename(columns={"referrer": "Source", "count": "Views", "uniques": "Unique"}),
                        use_container_width=True,
                        hide_index=True,
                        height=180,
                    )

            if paths:
                with t2:
                    st.markdown("<p style='font-size:0.78rem;font-weight:600;color:#8b949e;margin-bottom:4px;'>📄 Popular Paths</p>", unsafe_allow_html=True)
                    path_df = pd.DataFrame(paths)[["path", "count", "uniques"]]
                    st.dataframe(
                        path_df.rename(columns={"path": "Path", "count": "Views", "uniques": "Unique"}),
                        use_container_width=True,
                        hide_index=True,
                        height=180,
                    )
