# Implementation Plan: Auto-Refresh Dashboard

**Branch**: feat/003-auto-refresh | **Date**: 2026-06-16 | **Spec**: specs/003-auto-refresh/spec.md

**Input**: Feature specification from specs/003-auto-refresh/spec.md — dashboard auto-refreshes at the same interval as the scrape/daemon cycle.

## Summary

Add auto-refresh to the Streamlit dashboard. All 5 tabs render on every cycle (standard `st.tabs()`). Data loading functions are wrapped with `st.cache_data(ttl=interval)` so DB queries run once per refresh interval, not on every rerun. The auto-refresh loop is `time.sleep(interval)` + `st.rerun()` at end of `run()`.

## Technical Context

- **Language/Version:** Python 3.11+
- **Primary Dependencies:** streamlit, plotly, streamlit-autorefresh (new) |
- **Storage:** SQLite (~/.vllm-metrics.db) — unchanged
- **Testing:** 1 new test (interval config parsing), 25 total
- **Target Platform:** Linux, localhost access only
- **Constraints:** No new dependencies, no DB changes, no sidebar additions
- **Scale/Scope:** ~25 lines changed in dashboard.py

## Constitution Check

**GATE 1 — Minimal Dependencies:** PASS. `st.cache_data`, `time.sleep()`, `st.rerun()` — all already available.

**GATE 2 — Meaningful Statistics:** PASS. Refresh interval matches data collection rate.

**GATE 3 — Transparency:** PASS. Interval in config.yaml. Last-refreshed timestamp in footer.

## Design

### Changes

1. **Read interval** from config.yaml (`cfg.get("interval", 60)`)
2. **Cache data loading**: Wrap `load_raw_summary()`, `load_daily_summary()`, `load_latest_snapshots()` with `st.cache_data(ttl=interval)` — DB queries run once per interval, results serve all tabs
- Auto-refresh via `streamlit-autorefresh` component (`st_autorefresh`) — no full page reload
4. **Footer**: Append "Auto-refresh every Ns" or "Auto-refresh off"

### Auto-Refresh Flow

```
│  run()
│  ├── load_servers(), sidebar
│  ├── _cached_raw_summary()     ← cached for interval seconds
│  ├── _cached_daily_summary()   ← cached for interval seconds
│  ├── _cached_snapshots()       ← cached for interval seconds
│  ├── metric cards (all tabs)
│  ├── st.tabs() → all 5 render  ← standard Streamlit
│  ├── footer + caption
│  └── <meta refresh content="{interval}">  ← browser-native, no spinner
```

### Tab Switch Behavior

All tabs render on every cycle. `st.cache_data(ttl=interval)` prevents redundant DB queries on Streamlit interactions (tab clicks, filter changes). Data is always served from cache until the TTL expires, at which point the next auto-refresh cycle queries fresh data.

## Edge Cases

- **interval=0**: No auto-refresh. Dashboard static (current behavior).
- **interval not in config**: Default to 60s.
- **DB unreachable**: Cached data serves current cycle. Next cycle retries.
- **Multiple browsers**: Each session independently caches and refreshes.

No constitution violations.
