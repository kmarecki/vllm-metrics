# Implementation Plan: Auto-Refresh Dashboard

**Branch**: feat/003-auto-refresh | **Date**: 2026-06-16 | **Spec**: specs/003-auto-refresh/spec.md

**Input**: Feature specification from specs/003-auto-refresh/spec.md — dashboard auto-refreshes at the same interval as the scrape/daemon cycle; only the currently visible tab renders its charts.

## Summary

Replace `st.tabs()` with a horizontally styled `st.radio()` that looks identical to the current tab bar. The radio's value is the active tab — only its `if` branch executes chart rendering. Hidden tabs create zero plotly Figures. Data loading is cached with `st.cache_data(ttl=interval)`. Auto-refresh via `time.sleep(interval)` + `st.rerun()` at end of `run()`.

## Technical Context

- **Language/Version:** Python 3.11+
- **Primary Dependencies:** streamlit, plotly (existing) — no new packages
- **Storage:** SQLite (~/.vllm-metrics.db) — unchanged
- **Testing:** 2 new tests (interval config parsing, interval=0 disables), 26 total
- **Target Platform:** Linux, localhost access only
- **Project Type:** CLI tool with optional Streamlit dashboard
- **Performance Goals:** Only 1 tab's chart code runs per cycle. DB queries cached per interval.
- **Constraints:** No new dependencies, no DB changes, no sidebar additions
- **Scale/Scope:** ~60 lines changed in dashboard.py

## Constitution Check

**GATE 1 — Minimal Dependencies:** PASS. Uses `st.radio()` + CSS — both already available. No new packages.

**GATE 2 — Meaningful Statistics:** PASS. Refresh interval matches the data collection rate. Only active tab queries data.

**GATE 3 — Transparency:** PASS. Interval in config.yaml. Last-refreshed timestamp already shown.

## Project Structure

### Files Changed

| File | Action | Scope |
|------|--------|-------|
| `vllm_metrics/dashboard.py` | **MODIFY** | Replace st.tabs with radio + CSS, add conditional per-tab rendering, cache_data TTL, sleep+rerun loop |

## Design

### Overview

```
run()
  │
  ├── cfg, tz, sidebar
  ├── metric cards (always rendered)
  │
  ├── radio styled as tab bar  ← active_tab value tracks selection
  │
  ├── if active_tab == "📈 Token Trends":
  │     load cached daily/raw → _build_tab_token_trends()
  ├── elif active_tab == "⚡ Latency":
  │     load cached daily → _build_tab_latency_concurrency()
  ├── elif ...  (only ONE branch runs)
  │
  ├── divider + last-refreshed caption
  │
  └── sleep(interval) + st.rerun()
```

### Tab Bar via Radio + CSS

Instead of Streamlit's `st.tabs()` (which forces all blocks to execute), use a horizontal radio styled to look like the current tab bar:

```python
st.markdown("""
<style>
    /* Horizontal row for radio options */
    div.stRadio > div[role="radiogroup"] {
        flex-direction: row !important;
        gap: 0 !important;
    }
    /* Individual tab buttons */
    div.stRadio > div[role="radiogroup"] label {
        border: 1px solid #30363d;
        border-right: none;
        padding: 6px 20px;
        margin: 0;
        background: #161b22;
        cursor: pointer;
        color: #c9d1d9;
        font-size: 14px;
    }
    div.stRadio > div[role="radiogroup"] label:first-of-type {
        border-radius: 6px 0 0 6px;
    }
    div.stRadio > div[role="radiogroup"] label:last-of-type {
        border-radius: 0 6px 6px 0;
        border-right: 1px solid #30363d;
    }
    /* Active tab highlight */
    div.stRadio > div[role="radiogroup"] label[data-selected="true"] {
        background: #76b900;
        color: #0d1117;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

TAB_NAMES = ["📈 Token Trends", "⚡ Latency & Concurrency",
             "📋 Per-Model Breakdown", "📅 Daily Stats", "🔧 Server Stats"]
active_tab = st.radio("", TAB_NAMES, index=0, label_visibility="collapsed")
```

### Conditional Per-Tab Rendering

Each tab loads its data independently. Since all calls use the same `since`/`until`/`tz` parameters, `st.cache_data` serves the same cached DataFrame to all tabs — but only the active tab's `if` branch runs:

```python
if active_tab == TAB_NAMES[0]:
    daily = load_raw_summary(since=since, until=until, tz=tz)
    if daily.empty:
        daily = load_daily_summary(since=since, until=until)
    raw = load_latest_snapshots(since=since, until=until, tz=tz, limit=snap_limit)
    if selected_server != "All":
        daily = daily[daily["server"] == selected_server]
        raw = raw[raw["server"] == selected_server]
    _build_metric_cards(daily)
    _build_tab_token_trends(daily, raw, tz)
elif active_tab == TAB_NAMES[1]:
    daily = load_raw_summary(since=since, until=until, tz=tz)
    if daily.empty:
        daily = load_daily_summary(since=since, until=until)
    if selected_server != "All":
        daily = daily[daily["server"] == selected_server]
    _build_metric_cards(daily)
    _build_tab_latency_concurrency(daily)
...
```

`load_raw_summary()` and `load_latest_snapshots()` are wrapped with `st.cache_data(ttl=interval)` so they only query the DB once per interval, regardless of how many tabs reference the result or how many times the user clicks.

Metric cards render inside the active tab branch — they update with the tab switch.

### Auto-Refresh Loop

At the very end of `run()`, after all rendering:

```python
interval = cfg.get("interval", 60)
if interval > 0:
    time.sleep(interval)
    st.rerun()
```

`interval: 0` in config.yaml disables auto-refresh (dashboard behaves as today).

### Tab Switch Flow

```
[User on Tab A] → Tab A renders charts
    ↓
[User clicks Tab B] → Streamlit reruns
    ↓
active_tab = "Tab B"
    ↓
daily/raw loaded → from cache (instant, no DB query)
    ↓
Tab B renders charts immediately
    ↓
sleep(interval) → st.rerun() → cache TTL check
    ├── expired → fresh DB query → new charts
    └── valid  → cached data → same charts
```

## Edge Cases

- **interval=0**: Auto-refresh disabled. Dashboard static (current behavior).
- **interval not in config**: Default to 60s.
- **Tab switch mid-cycle**: Instant — cached data serves immediately. No extra DB query.
- **DB unreachable**: Cached data served. Next cycle retries.
- **Multiple browser tabs**: Each session independently caches and refreshes.
- **Metric cards**: Render per active tab (consistent with visible charts).

## Complexity Tracking

No constitution violations.
