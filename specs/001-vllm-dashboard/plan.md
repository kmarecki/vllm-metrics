# Implementation Plan: vLLM Dashboard

**Branch**: feat/001-vllm-dashboard | **Date**: 2026-06-12 | **Spec**: specs/001-vllm-dashboard/spec.md

**Input**: Feature specification from specs/001-vllm-dashboard/spec.md — Streamlit dashboard in NVIDIA black/green color scheme for presenting captured vLLM metrics.

## Summary

Add a `vllm-metrics dashboard` subcommand that launches a Streamlit web app reading from the existing SQLite metrics database. The dashboard has four tabs: Token Trends, Latency & Concurrency, Per-Model Breakdown, and Server Stats — all styled with NVIDIA's dark background (#0d1117) and green accent (#76b900). Optional dependency: streamlit + plotly.

## Technical Context

- **Language/Version:** Python 3.11+
- **Primary Dependencies:** streamlit, plotly (optional — dashboard only)
- **Storage:** SQLite (~/.vllm-metrics.db), read-only queries on daily_stats + raw_snapshots + servers + models
- **Testing:** Manual validation against report command output (no automated UI tests for v1)
- **Target Platform:** Linux (Ubuntu aarch64 primary), localhost access only
- **Project Type:** CLI tool with optional Streamlit dashboard subcommand
- **Performance Goals:** Dashboard loads in <5s with 30 days of daily_stats data
- **Constraints:** No authentication, no multi-user, local DB only
- **Scale/Scope:** 1–5 servers, 1–20 models, up to years of daily_stats

## Constitution Check

**GATE 1 — Minimal Dependencies:** PASS. Core CLI (scrape/daemon/report) unchanged. Streamlit only imported when the `dashboard` subcommand is invoked. `vllm-metrics --help` still works without streamlit.

**GATE 2 — Meaningful Statistics:** PASS. Dashboard reuses the same SQL queries and aggregation logic as the report command. Throughput computed from consecutive gen-producing snapshots, not time-window fallback.

**GATE 3 — Transparency:** PASS. Data source is the same SQLite DB. Calculations documented in data-model.md.

## Project Structure

### Artifacts (this feature)

```
specs/001-vllm-dashboard/
├── spec.md              # Phase 1 — requirements
├── plan.md              # This file — implementation plan
├── research.md          # Technology decision
├── data-model.md        # SQL queries and data flow
└── quickstart.md        # Validation scenarios

vllm_metrics/
├── dashboard.py         # NEW — Streamlit app (all tabs, styling, queries)
├── daemon.py            # UNCHANGED
├── db.py                # UNCHANGED
├── report.py            # UNCHANGED
├── scraper.py           # UNCHANGED
└── __init__.py          # UNCHANGED

vllm-metrics             # MODIFIED — add 'dashboard' subcommand
```

### Files Changed

| File | Action | Scope |
|------|--------|-------|
| `vllm_metrics/dashboard.py` | **CREATE** | ~500 lines: Streamlit app with 4 tabs, NVIDIA theme, all SQL queries |
| `vllm-metrics` (CLI) | **MODIFY** | +5 lines: add `dashboard` subparser + `cmd_dashboard` function |

## Implementation Phases

### Phase 4a — Core infrastructure
- Create `vllm_metrics/dashboard.py` with DB connection, config loading, helper functions (formatting, NVIDIA CSS)
- Wire `vllm-metrics dashboard` subcommand into the CLI entry point

### Phase 4b — Token Trends tab
- Metric cards (total tokens, prompt, gen, requests, cache hit rate)
- Token volume bar chart (daily aggregation)
- Generation throughput line chart (from raw_snapshots)

### Phase 4c — Latency & Concurrency tab
- Concurrency charts (avg running, avg waiting, peak running)
- Latency charts (TTFT, ITL, E2E)
- KV cache usage area chart

### Phase 4d — Per-Model & Server Stats tabs
- Per-model summary table + bar chart
- Server status sidebar with online/offline indicators
- Raw snapshots table (last 50)
- Server filter dropdown

## Edge Cases Covered

- **Empty DB**: Informational message, no crash
- **Single data point**: Line chart renders a single point marker
- **No throughput data**: Empty state in gen throughput chart
- **Missing config.yaml**: Graceful fallback to default path
- **Large datasets**: Streamlit caches DB connection; daily aggregation means at most 365 rows per chart
- **Streamlit not installed**: ImportError at subcommand dispatch — clear error message suggesting pip install

## Complexity Tracking

No constitution violations. Architecture is a single new file reading existing tables.

### BUG-001 Fix: SQLite thread safety in Streamlit dashboard

**Root cause**: `sqlite3.connect()` creates connections bound to the calling thread. Streamlit's `@st.cache_resource` caches the connection on first call but reruns the dashboard script in a new thread on each interaction. The cached connection is used from the wrong thread.

**Fix**: Add `check_same_thread=False` to `sqlite3.connect()` in `vllm_metrics/db.py`'s `connect()` function. This tells SQLite to allow the connection to be used from any thread.

**Constitution check**: The dashboard is an optional subcommand. Core CLI commands (daemon, scrape, report) run single-threaded and are unaffected. Streamlit's rerun model inherently crosses threads — this is safe and expected usage.

**Additive note**: Single-line change. No existing plan sections modified.

### BUG-002 Fix: Dashboard only queries daily_stats, missing raw_snapshots fallback

**Root cause**: The dashboard's `load_daily_summary()` only queries the `daily_stats` table. This table is populated only by the `vllm-metrics prune` command. The daemon stores all scrapes in `raw_snapshots` but does not automatically create daily rollups. The report command handles this correctly by querying `raw_snapshots` first (via `_run_raw_summary`) and falling back to `daily_stats`.

**Fix**: Add a `load_raw_summary()` function to the dashboard that queries `raw_snapshots` with time-weighted averages (matching the report's `_run_raw_summary` logic). Modify the dashboard's `run()` to try `load_daily_summary()` first, and if it returns empty or insufficient data, fall back to `load_raw_summary()`. This mirrors the report command's query strategy.

**Constitution check**: Meaningful Statistics principle — the raw_snapshots fallback uses the same time-weighted average logic as the report command (active-only, consecutive snapshot deltas). No idle gaps included.

**Additive note**: New helper function + fallback logic in `run()`. No existing code modified — only additions.

### BUG-004 Fix: Replace date range presets with calendar periods + custom range pickers

**Root cause**: The `_build_sidebar()` function uses relative duration presets (24 hours, 7 days, 30 days, 90 days) mapped to `timedelta(days=N)`. No support for calendar-aligned periods or custom date inputs.

**Fix**: Replace the single selectbox with:
- A selectbox for presets: "Today", "This week", "This month", "This year", "All", "Custom..."
- When "Custom..." is selected, show two `st.date_input()` widgets for start and end dates
- Calendar periods compute `since`/`until` from current date:
  - Today: `since = today`, `until = today`
  - This week: `since = Monday of this week`, `until = today`
  - This month: `since = 1st of this month`, `until = today`
  - This year: `since = Jan 1 of this year`, `until = today`
  - All: `since = None`, `until = None`
  - Custom: user picks start and end dates
- `load_raw_summary()` already accepts `since` — also pass `until` to query.

**Constitution check**: Meaningful Statistics — calendar periods show exactly the data the user expects for each period.

**Additive note**: Replace `_build_sidebar()` internals and `run()` call chain. Update `load_raw_summary()` and `load_daily_summary()` to accept optional `until` parameter.
