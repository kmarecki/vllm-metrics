# Implementation Plan: Daily Stats Tab

**Branch**: feat/002-daily-stats | **Date**: 2026-06-16 | **Spec**: specs/002-daily-stats/spec.md

**Input**: Feature specification from specs/002-daily-stats/spec.md — add a 5th tab to the dashboard showing per-calendar-day aggregated stats matching the report command's DAILY TREND section.

## Summary

Add a "Daily Stats" tab to the existing Streamlit dashboard. The tab reuses the existing `load_raw_summary()` data layer — no new DB queries, no new dependencies. It aggregates the already-fetched daily data across (server, model) per local date and displays a table (date descending) plus a grouped bar chart.

## Technical Context

- **Language/Version:** Python 3.11+
- **Primary Dependencies:** streamlit, plotly (already installed for dashboard)
- **Storage:** SQLite (~/.vllm-metrics.db) — no new tables or queries
- **Testing:** 2 new tests (aggregation logic + empty state), 24 total
- **Target Platform:** Linux, localhost access only
- **Project Type:** CLI tool with optional Streamlit dashboard
- **Performance Goals:** Same <5s load time — data already fetched by dashboard's `run()`
- **Constraints:** No new dependencies, no DB changes
- **Scale/Scope:** Single new function ~60 lines

## Constitution Check

**GATE 1 — Minimal Dependencies:** PASS. Existing dashboard dependencies (streamlit + plotly) reused. Core CLI unchanged.

**GATE 2 — Meaningful Statistics:** PASS. Uses same timezone-shifted `load_raw_summary()` data as the rest of the dashboard. Aggregation per calendar day matches report's DAILY TREND logic.

**GATE 3 — Transparency:** PASS. Data source is the same SQLite DB. Aggregation is a simple pandas groupby per (date) across servers/models.

## Project Structure

### Artifacts (this feature)

```
specs/002-daily-stats/
├── spec.md              # Phase 1
├── plan.md              # This file
├── tasks.md             # Phase 3
└── history.md           # Process log

vllm_metrics/
└── dashboard.py         # MODIFIED — add _build_tab_daily_stats() + wire 5th tab
```

### Files Changed

| File | Action | Scope |
|------|--------|-------|
| `vllm_metrics/dashboard.py` | **MODIFY** | +~60 lines: new `_build_tab_daily_stats()` function, +1 tab |
| `tests/test_dashboard.py` | **MODIFY** | +~50 lines: 2 new tests (T032-T033) |

## Implementation

### Phase 4a — Implementation

1. Add `_build_tab_daily_stats(daily: pd.DataFrame)` function:
   - Check for empty data → info message
   - Groupby "date" across all server/model rows, summing tokens/requests and averaging concurrent
   - Build display columns: Date, Total Tokens, Prompt, Generation, Requests, Avg Running, Avg Waiting
   - Sort by date descending (most recent first)
   - Render as `st.dataframe` with NVIDIA theme
   - Render grouped bar chart (prompt + gen) via plotly go.Figure

2. Wire 5th tab in `run()`:
   - Add "Daily Stats" tab to `st.tabs([...])`
   - Call `_build_tab_daily_stats(daily)` in the 5th tab

3. Add tests:
   - T032: Verify aggregation across servers/models per local date
   - T033: Verify empty data handling

## Edge Cases Covered

- **Empty daily data**: Info message, no crash
- **Multiple servers/models per date**: Aggregated into single row per day
- **Single day of data**: Chart renders single bar pair
- **Timezone boundary**: `load_raw_summary()` already handles local-date shifts — reuse as-is

## Complexity Tracking

No constitution violations. Single new function, no new queries or dependencies.
