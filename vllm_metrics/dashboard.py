"""Streamlit dashboard for vLLM metrics.

Launched via: vllm-metrics dashboard
Reads from the SQLite DB and renders charts in NVIDIA black-and-green theme.
"""

from datetime import datetime, timezone
import os
import time

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from vllm_metrics import connect, get_db_path, load_config

# ── NVIDIA colour palette ──────────────────────────────────────────────
BG = "#0d1117"
BG2 = "#161b22"
BG3 = "#21262d"
GREEN = "#76b900"
GREEN_LIGHT = "#a4d62e"
TEXT = "#c9d1d9"
TEXT_DIM = "#8b949e"
ACCENT = "#00ff41"


# ── Formatting helpers (T003) ──────────────────────────────────────────

def fmt_number(n: float | None) -> str:
    if n is None:
        return "\u2014"
    if abs(n) >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f}B"
    if abs(n) >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if abs(n) >= 1_000:
        return f"{n/1_000:.1f}K"
    if n == int(n):
        return str(int(n))
    return f"{n:.1f}"


def fmt_ms(s: float | None) -> str:
    if s is None or s == 0:
        return "\u2014"
    return f"{s*1000:.1f}ms"


def fmt_s(s: float | None) -> str:
    if s is None or s == 0:
        return "\u2014"
    if s < 60:
        return f"{s:.1f}s"
    if s < 3600:
        return f"{s/60:.1f}m"
    return f"{s/3600:.1f}h"


def fmt_pct(f: float | None) -> str:
    if f is None:
        return "\u2014"
    return f"{f*100:.1f}%"


def fmt_decimal(n: float | None) -> str:
    if n is None:
        return "\u2014"
    if n == 0:
        return "0"
    if n >= 100:
        return f"{n:.0f}"
    if n >= 10:
        return f"{n:.1f}"
    if n >= 1:
        return f"{n:.2f}"
    if n >= 0.01:
        return f"{n:.3f}"
    return f"{n:.4f}"


# ── Theme / CSS ────────────────────────────────────────────────────────

def inject_css():
    """Inject NVIDIA-themed custom CSS."""
    st.markdown(f"""
    <style>
        .stApp {{ background-color: {BG}; color: {TEXT}; }}
        .stMarkdown, .stText, .stDataFrame {{ color: {TEXT}; }}
        h1, h2, h3, h4 {{ color: {GREEN} !important; }}
        .stSidebar {{ background-color: {BG2}; }}
        .stMetric label {{ color: {TEXT_DIM} !important; }}
        .stMetric [data-testid="metric-container"] {{
            background-color: {BG3};
            border: 1px solid {GREEN};
            border-radius: 8px;
            padding: 12px;
        }}
        .stMetric [data-testid="metric-value"] {{ color: {GREEN_LIGHT} !important; }}
        div[data-testid="stDecoration"] {{ background-image: none; background-color: {BG3}; }}
        hr {{ border-color: {BG3}; }}
    </style>
    """, unsafe_allow_html=True)


def plotly_theme() -> dict:
    return dict(
        paper_bgcolor=BG2,
        plot_bgcolor=BG2,
        font_color=TEXT,
        xaxis=dict(gridcolor=BG3, zerolinecolor=BG3),
        yaxis=dict(gridcolor=BG3, zerolinecolor=BG3),
        hoverlabel=dict(bgcolor=BG3, font_color=TEXT),
        legend=dict(font_color=TEXT),
    )


# ── Cached DB connection ───────────────────────────────────────────────

@st.cache_resource
def get_conn():
    """Open a cached connection to the vLLM metrics database."""
    cfg = load_config(
        os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    )
    db_path = get_db_path(cfg.get("database", "~/.vllm-metrics.db"))
    return connect(db_path)


# ── Data layer (T009) ──────────────────────────────────────────────────

def load_servers() -> pd.DataFrame:
    """Load all tracked servers."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, name, url, last_seen FROM servers ORDER BY name"
    ).fetchall()
    return pd.DataFrame(
        [dict(r) for r in rows],
        columns=["id", "name", "url", "last_seen"],
    )


def load_daily_summary(since: str | None = None) -> pd.DataFrame:
    """Load daily_stats aggregated by date, optionally filtered."""
    conn = get_conn()
    where = ""
    params = []
    if since:
        where = "WHERE d.date >= ?"
        params.append(since)
    qry = f"""
        SELECT
            d.date,
            s.name AS server,
            m.model_name AS model,
            d.prompt_tokens,
            d.generation_tokens,
            d.prompt_tokens_cached,
            d.completed_requests,
            d.preemptions,
            d.avg_running,
            d.max_running,
            d.avg_waiting,
            d.avg_kv_cache_pct,
            d.avg_ttft_ms,
            d.avg_itl_ms,
            d.avg_e2e_s,
            d.avg_queue_s,
            d.num_snapshots
        FROM daily_stats d
        JOIN servers s ON d.server_id = s.id
        LEFT JOIN models m ON d.model_id = m.id
        {where}
        ORDER BY d.date, s.name, m.model_name
    """
    rows = conn.execute(qry, params).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def load_latest_snapshots(limit: int = 500) -> pd.DataFrame:
    """Load the most recent raw_snapshots rows."""
    conn = get_conn()
    rows = conn.execute(f"""
        SELECT
            r.timestamp,
            datetime(r.timestamp, 'unixepoch') AS ts_str,
            s.name AS server,
            m.model_name AS model,
            r.num_requests_running,
            r.num_requests_waiting,
            r.kv_cache_usage_perc,
            r.prompt_tokens_total,
            r.generation_tokens_total,
            r.request_success_total
        FROM raw_snapshots r
        JOIN servers s ON r.server_id = s.id
        LEFT JOIN models m ON r.model_id = m.id
        ORDER BY r.timestamp DESC
        LIMIT ?
    """, (limit,)).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def load_raw_summary(since: str | None = None) -> pd.DataFrame:
    """Load aggregated raw_snapshots by date (fallback when daily_stats is empty).

    Mirrors the report command's _run_raw_summary logic: sums token counters
    and averages gauges per (date, server, model).
    """
    conn = get_conn()
    where = ""
    params = []
    if since:
        where = "WHERE DATE(r.timestring) >= ?"
        params.append(since)
    qry = f"""
        SELECT
            DATE(r.timestring) AS date,
            s.name AS server,
            m.model_name AS model,
            SUM(r.prompt_tokens_total)        AS prompt_tokens,
            SUM(r.generation_tokens_total)    AS generation_tokens,
            SUM(r.prompt_tokens_cached_total) AS prompt_tokens_cached,
            SUM(r.request_success_total)      AS completed_requests,
            SUM(r.num_preemptions_total)      AS preemptions,
            AVG(r.num_requests_running)       AS avg_running,
            MAX(r.num_requests_running)       AS max_running,
            AVG(r.num_requests_waiting)       AS avg_waiting,
            AVG(r.kv_cache_usage_perc)        AS avg_kv_cache_pct,
            AVG(r.ttft_sum / NULLIF(r.ttft_count, 0)) * 1000 AS avg_ttft_ms,
            AVG(r.itl_sum / NULLIF(r.itl_count, 0)) * 1000   AS avg_itl_ms,
            AVG(r.e2e_sum / NULLIF(r.e2e_count, 0))          AS avg_e2e_s,
            AVG(r.queue_sum / NULLIF(r.queue_count, 0))      AS avg_queue_s,
            COUNT(*)                                          AS num_snapshots
        FROM raw_snapshots r
        JOIN servers s ON r.server_id = s.id
        LEFT JOIN models m ON r.model_id = m.id
        {where}
        GROUP BY DATE(r.timestring), s.name, m.model_name
        HAVING m.model_name IS NOT NULL
        ORDER BY date, s.name, m.model_name
    """
    rows = conn.execute(qry, params).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


# ── Dashboard UI ───────────────────────────────────────────────────────

def _build_sidebar(servers_df: pd.DataFrame) -> tuple[str, str | None]:
    """Build sidebar controls. Returns (selected_server, range_since)."""
    st.sidebar.header("Servers")
    server_options = ["All"] + sorted(servers_df["name"].tolist())
    selected_server = st.sidebar.selectbox("Filter server", server_options,
                                           label_visibility="collapsed")

    st.sidebar.header("Date Range")
    range_preset = st.sidebar.selectbox(
        "Range", ["24 hours", "7 days", "30 days", "90 days", "All"], index=0,
        label_visibility="collapsed",
    )
    from datetime import timedelta
    range_map = {"24 hours": 1, "7 days": 7, "30 days": 30, "90 days": 90, "All": 9999}
    days = range_map[range_preset]
    if days < 9999:
        since = (datetime.now(timezone.utc).date() - timedelta(days=days)).isoformat()
    else:
        since = None

    st.sidebar.header("Server Status")
    now_ts = time.time()
    for _, sv in servers_df.iterrows():
        is_online = sv["last_seen"] and (now_ts - sv["last_seen"]) < 300
        color = GREEN if is_online else "#f85149"
        label = "online" if is_online else "offline"
        st.sidebar.markdown(
            f'<div style="margin:2px 0;">'
            f'<span style="color:{TEXT_DIM};">{sv["name"]}</span> '
            f'<span style="color:{color};">\u25cf {label}</span></div>',
            unsafe_allow_html=True,
        )

    st.sidebar.markdown("---")
    st.sidebar.caption("vLLM Metrics Collector")

    return selected_server, since


def _build_metric_cards(daily: pd.DataFrame):
    """Render top-level metric cards (FR-002)."""
    total_prompt = int(daily["prompt_tokens"].sum())
    total_gen = int(daily["generation_tokens"].sum())
    total_cached = int(daily["prompt_tokens_cached"].sum())
    total_requests = int(daily["completed_requests"].sum())
    total_tokens = total_prompt + total_gen

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Tokens", fmt_number(total_tokens))
    with col2:
        st.metric("Prompt", fmt_number(total_prompt))
    with col3:
        st.metric("Generation", fmt_number(total_gen))
    with col4:
        st.metric("Requests", fmt_number(total_requests))
    with col5:
        cache_pct = (total_cached / total_prompt * 100) if total_prompt > 0 else 0
        st.metric("Cache Hit Rate", fmt_pct(cache_pct / 100))


def _build_tab_token_trends(daily: pd.DataFrame, raw: pd.DataFrame):
    """Token volume and generation throughput (FR-003, FR-004)."""
    st.subheader("Token Volume Over Time")

    daily_agg = daily.groupby("date", as_index=False)[
        ["prompt_tokens", "generation_tokens", "prompt_tokens_cached"]
    ].sum()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=daily_agg["date"], y=daily_agg["prompt_tokens"],
        name="Prompt Tokens", marker_color=GREEN,
    ))
    fig.add_trace(go.Bar(
        x=daily_agg["date"], y=daily_agg["generation_tokens"],
        name="Generation Tokens", marker_color=ACCENT,
    ))
    fig.add_trace(go.Bar(
        x=daily_agg["date"], y=daily_agg["prompt_tokens_cached"],
        name="Cached (prefix)", marker_color="#58a6ff",
    ))
    fig.update_layout(barmode="group", title="Daily Token Volume",
                      **plotly_theme())
    st.plotly_chart(fig, use_container_width=True)

    # Generation throughput
    st.subheader("Generation Throughput")
    rate_rows = _compute_gen_rates(raw)
    if rate_rows:
        rate_df = pd.DataFrame(rate_rows)
        fig = px.line(
            rate_df, x="ts", y="gen_tok_s",
            color="model" if "model" in rate_df.columns else None,
            line_dash="server" if "server" in rate_df.columns else None,
            markers=True,
            title="Generation Throughput (tok/s)",
        )
        fig.update_traces(line_color=GREEN)
        fig.update_layout(**plotly_theme())
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No generation throughput data available for the selected period.")


def _compute_gen_rates(raw: pd.DataFrame) -> list[dict]:
    """Compute gen throughput from consecutive gen-producing snapshots."""
    if raw.empty or "timestamp" not in raw.columns:
        return []
    raw_ts = raw.copy()
    raw_ts["ts"] = pd.to_datetime(raw_ts["timestamp"], unit="s")
    raw_ts = raw_ts.sort_values("ts")

    rate_rows = []
    for (sv, mdl), grp in raw_ts.groupby(["server", "model"]):
        grp = grp.sort_values("ts")
        ts_series = grp["ts"]
        vals = grp["generation_tokens_total"].values
        for j in range(1, len(vals)):
            dt = (ts_series.iloc[j] - ts_series.iloc[j - 1]).total_seconds()
            gd = vals[j] - vals[j - 1]
            if dt > 0 and gd > 0:
                rate = gd / dt
                if 0.1 <= rate <= 10000:
                    rate_rows.append({
                        "ts": ts_series.iloc[j],
                        "server": sv,
                        "model": mdl,
                        "gen_tok_s": rate,
                    })
    return rate_rows


def _build_tab_latency_concurrency(daily: pd.DataFrame):
    """Concurrency, KV cache, and latency charts (FR-005, FR-006, FR-007)."""
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Concurrent Requests")
        daily_conc = daily.groupby("date", as_index=False)[
            ["avg_running", "avg_waiting"]
        ].mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_conc["date"], y=daily_conc["avg_running"],
            name="Avg Running", mode="lines+markers",
            line=dict(color=GREEN, width=2),
            marker=dict(size=4, color=GREEN),
        ))
        fig.add_trace(go.Scatter(
            x=daily_conc["date"], y=daily_conc["avg_waiting"],
            name="Avg Waiting", mode="lines+markers",
            line=dict(color="#f0883e", width=2),
            marker=dict(size=4, color="#f0883e"),
        ))
        fig.update_layout(title="Average Concurrent Requests", **plotly_theme())
        st.plotly_chart(fig, use_container_width=True)

        daily_peak = daily.groupby("date", as_index=False)["max_running"].max()
        fig = px.bar(daily_peak, x="date", y="max_running",
                     title="Peak Concurrent Requests")
        fig.update_traces(marker_color=GREEN_LIGHT)
        fig.update_layout(**plotly_theme())
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("KV Cache Usage")
        daily_kv = daily.groupby("date", as_index=False)["avg_kv_cache_pct"].mean()
        fig = px.area(daily_kv, x="date", y="avg_kv_cache_pct",
                      title="KV Cache Usage (%)")
        fig.update_traces(line_color=GREEN,
                          fillcolor=f"rgba(118, 185, 0, 0.2)")
        fig.update_layout(**plotly_theme())
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Latency Metrics")
        lat = daily[["date", "avg_ttft_ms", "avg_itl_ms", "avg_e2e_s"]].copy()
        lat["avg_e2e_ms"] = lat["avg_e2e_s"] * 1000
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=lat["date"], y=lat["avg_ttft_ms"],
            name="TTFT (ms)", mode="lines+markers",
            line=dict(color=GREEN, width=2),
        ))
        fig.add_trace(go.Scatter(
            x=lat["date"], y=lat["avg_itl_ms"],
            name="ITL/TPOT (ms)", mode="lines+markers",
            line=dict(color=ACCENT, width=2),
        ))
        fig.add_trace(go.Scatter(
            x=lat["date"], y=lat["avg_e2e_ms"],
            name="E2E (ms)", mode="lines+markers",
            line=dict(color="#58a6ff", width=2),
        ))
        fig.update_layout(title="Latency Over Time", **plotly_theme())
        st.plotly_chart(fig, use_container_width=True)


def _build_tab_per_model(daily: pd.DataFrame):
    """Per-model breakdown table + chart (FR-008)."""
    st.subheader("Per-Model Summary")
    if "model" in daily.columns and daily["model"].notna().any():
        pm = daily.groupby(["server", "model"], as_index=False).agg({
            "prompt_tokens": "sum",
            "generation_tokens": "sum",
            "completed_requests": "sum",
            "preemptions": "sum",
            "avg_ttft_ms": "mean",
            "avg_itl_ms": "mean",
        })
        pm.columns = [
            "Server", "Model", "Prompt Tokens", "Gen Tokens",
            "Requests", "Preemptions", "Avg TTFT (ms)", "Avg ITL (ms)",
        ]
        st.dataframe(pm, use_container_width=True, hide_index=True)

        fig = px.bar(
            pm, x="Model", y=["Prompt Tokens", "Gen Tokens"],
            barmode="group", title="Token Distribution Per Model",
            color_discrete_map={
                "Prompt Tokens": GREEN, "Gen Tokens": ACCENT,
            },
        )
        fig.update_layout(**plotly_theme())
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No per-model data available.")


def _build_tab_server_stats(raw: pd.DataFrame):
    """Server stats tab with raw snapshot table (FR-012)."""
    st.subheader("Recent Snapshots")
    if raw.empty:
        st.info("No snapshot data available.")
        return
    disp = raw.copy()
    disp["ts"] = pd.to_datetime(disp["timestamp"], unit="s")
    disp = disp[["ts", "server", "model", "num_requests_running",
                  "num_requests_waiting", "kv_cache_usage_perc"]].rename(
        columns={
            "ts": "Timestamp", "server": "Server", "model": "Model",
            "num_requests_running": "Running",
            "num_requests_waiting": "Waiting",
            "kv_cache_usage_perc": "KV Cache %",
        })
    st.dataframe(disp.head(50), use_container_width=True, hide_index=True)


# ── Main ───────────────────────────────────────────────────────────────

def run():
    """Entry point for the dashboard."""
    st.set_page_config(page_title="vLLM Metrics", page_icon="\U0001f4ca",
                       layout="wide", initial_sidebar_state="expanded")
    inject_css()

    st.title("vLLM Metrics Dashboard")
    st.markdown(
        f'<p style="color:{TEXT_DIM};">'
        f"Token generation and server metrics"
        f"</p>",
        unsafe_allow_html=True,
    )

    servers = load_servers()
    if servers.empty:
        st.warning(
            "No servers configured. Run `vllm-metrics scrape` first "
            "to collect data."
        )
        return

    # Sidebar
    selected_server, since = _build_sidebar(servers)

    # Data — mirror report command strategy: raw_snapshots first, daily_stats fallback
    daily = load_raw_summary(since=since)
    if daily.empty:
        daily = load_daily_summary(since=since)
    raw = load_latest_snapshots()

    if selected_server != "All":
        daily = daily[daily["server"] == selected_server]
        raw = raw[raw["server"] == selected_server]

    if daily.empty:
        st.info(
            "No daily stats data yet. "
            "Run the scraper to collect metrics."
        )
        return

    # Metric cards
    _build_metric_cards(daily)
    st.divider()

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "\U0001f4c8 Token Trends",
        "\u26a1 Latency & Concurrency",
        "\U0001f4cb Per-Model Breakdown",
        "\U0001f527 Server Stats",
    ])
    with tab1:
        _build_tab_token_trends(daily, raw)
    with tab2:
        _build_tab_latency_concurrency(daily)
    with tab3:
        _build_tab_per_model(daily)
    with tab4:
        _build_tab_server_stats(raw)

    st.divider()
    st.caption(
        f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )


if __name__ == "__main__":
    run()
