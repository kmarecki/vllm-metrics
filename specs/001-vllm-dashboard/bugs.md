# Bug Report: vLLM Dashboard

**Feature**: specs/001-vllm-dashboard/
**Created**: 2026-06-12
**Status**: Open

## Bug Log

### BUG-001: SQLite thread safety — check_same_thread=False not set

- **Severity**: critical
- **Area**: vllm_metrics/dashboard.py — DB connection via `@st.cache_resource`
- **Description**: Streamlit runs each interaction in a new thread. The SQLite connection created in one thread via `@st.cache_resource` is reused in another thread, causing `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread.`
- **Steps to Reproduce**:
  1. Run `./vllm-metrics dashboard`
  2. Wait for the dashboard to load (first render works because cache_resource creates the conn)
  3. Interact with the dashboard (change filter, select tab) — Streamlit reruns in a new thread
  4. Error appears: `ProgrammingError: SQLite objects created in a thread can only be used in that same thread.`
- **Actual Result**: Dashboard crashes on any interaction after initial load
- **Expected Result**: Dashboard should work across Streamlit's thread-switching reruns
- **Requires Clarification**: [x] no / [ ] yes
- **Plan Ref**: Plan section: BUG-001 Fix: SQLite thread safety in Streamlit dashboard
- **Status**: resolved

---

### BUG-002: Date range filter only shows last 2 days regardless of selection

- **Severity**: major
- **Area**: vllm_metrics/dashboard.py — `_build_sidebar` / date range filter logic
- **Description**: Selecting "7 days", "30 days", "90 days", or "All" in the date range selector all produce the same result — only the last 2 days of data are shown in the dashboard.
- **Steps to Reproduce**:
  1. Run `./vllm-metrics dashboard`
  2. Leave date range at default "7 days"
  3. Observe that charts show only 2 days of data
  4. Change to "All" — still only 2 days shown
- **Actual Result**: Only 2 days of data visible regardless of range selection
- **Expected Result**: Each range selection should show the corresponding number of days (7, 30, 90, or all available data)
- **Requires Clarification**: [x] no / [ ] yes
- **Plan Ref**: Plan section: BUG-002 Fix: Dashboard only queries daily_stats, missing raw_snapshots fallback
- **Status**: resolved

---

### BUG-003: Deprecated `use_container_width` parameter in Streamlit 1.58

- **Severity**: minor
- **Area**: vllm_metrics/dashboard.py — 9 calls to `st.plotly_chart()` and `st.dataframe()`
- **Description**: Streamlit 1.58 deprecates `use_container_width=True` in favor of `width='stretch'`. After 2025-12-31 the old parameter will be removed. Console shows 9 deprecation warnings on every load.
- **Steps to Reproduce**:
  1. Run `./vllm-metrics dashboard`
  2. Check terminal output — 9 warnings printed
- **Actual Result**: Console warnings: `Please replace use_container_width with width.`
- **Expected Result**: No deprecation warnings. Use `width='stretch'` instead.
- **Requires Clarification**: [x] no / [ ] yes
- **Plan Ref**: 
- **Status**: resolved

---

### BUG-004: Date range presets should use calendar periods (today, week, month, year) plus custom range

- **Severity**: minor
- **Area**: vllm_metrics/dashboard.py — `_build_sidebar` date range selector
- **Description**: Current presets (24 hours, 7 days, 30 days, 90 days, All) are relative durations, not calendar periods. Should be: Today, This week, This month, This year, All. Plus allow entering a custom start/end date range.
- **Steps to Reproduce**:
  1. Run `./vllm-metrics dashboard`
  2. Open date range dropdown — shows "24 hours", "7 days", "30 days", "90 days", "All"
- **Actual Result**: Relative duration presets, no custom date input
- **Expected Result**: Calendar-aligned presets (Today, This week, This month, This year, All) + two date inputs for custom range
- **Requires Clarification**: [x] no / [ ] yes
- **Plan Ref**: Plan section: BUG-004 Fix: Replace date range presets with calendar periods + custom range pickers
- **Status**: resolved

---

### BUG-005: Generation throughput chart shows only a small fragment of the selected date range

- **Severity**: major
- **Area**: vllm_metrics/dashboard.py — `load_latest_snapshots()` / `_compute_gen_rates()`
- **Description**: The gen throughput chart in the Token Trends tab only shows a small fragment of time regardless of the selected date range preset. `load_latest_snapshots()` always returned only the last 500 snapshots (~8 hours at 60s intervals), so a "This week" selection would still only show 8 hours of data.
- **Steps to Reproduce**:
  1. Run `./vllm-metrics dashboard`
  2. Select "This week" (or any range with >8h of data)
  3. Look at the Generation Throughput chart — only shows ~8h instead of a week
- **Actual Result**: Gen throughput chart limited to last 500 snapshots regardless of date range
- **Expected Result**: Gen throughput chart spans the full selected date range
- **Requires Clarification**: [x] no / [ ] yes
- **Plan Ref**: Fixed: no LIMIT when date range specified — all snapshots in range loaded so panning works across full period
- **Status**: resolved

---

### BUG-006: Generation throughput chart x-axis shows UTC timestamps instead of local timezone

- **Severity**: minor
- **Area**: vllm_metrics/dashboard.py — `_compute_gen_rates()` and gen throughput chart x-axis
- **Description**: The Generation Throughput chart's x-axis timestamps are in UTC. They should be displayed in the configured local timezone (Europe/Prague), consistent with the raw snapshots table and other dashboard displays. The rate computation should remain using UTC, only the displayed x-axis labels need conversion.
- **Steps to Reproduce**:
  1. Run `./vllm-metrics dashboard`
  2. Go to Token Trends tab
  3. Check Generation Throughput chart x-axis — timestamps are UTC
- **Actual Result**: UTC timestamps on x-axis
- **Expected Result**: Local timezone timestamps on x-axis
- **Requires Clarification**: [x] no / [ ] yes
- **Plan Ref**: Plan section: BUG-006 Fix: Convert gen throughput x-axis timestamps to local timezone
- **Status**: resolved

---

### BUG-007: Custom date range date_inputs don't work in sidebar columns

- **Severity**: major
- **Area**: vllm_metrics/dashboard.py — `_build_sidebar()` custom date range
- **Description**: When "Custom..." is selected in the date range dropdown, `st.date_input` widgets are rendered inside `st.columns(2)` without explicit keys. Streamlit fails to properly track widget state in this configuration, so the date inputs don't respond to clicks and the dashboard never updates with the selected range.
- **Steps to Reproduce**:
  1. Run `./vllm-metrics dashboard`
  2. Select "Custom..." from the date range dropdown
  3. Click on a date input to change it
  4. Nothing happens — dashboard doesn't update
- **Actual Result**: Date inputs not usable; no way to select custom date range
- **Expected Result**: Date inputs respond to clicks, dashboard updates with selected range
- **Requires Clarification**: [x] no / [ ] yes
- **Plan Ref**: 
- **Status**: resolved

---

### BUG-008: Gen throughput chart connects line across server downtime gaps

- **Severity**: major
- **Area**: vllm_metrics/dashboard.py — `_compute_gen_rates()` / gen throughput chart
- **Description**: When a server is down, the generation throughput chart draws a continuous line connecting the last data point before downtime to the first point after. The line should break (show no line) when there's a gap >15 minutes between consecutive snapshots, so the chart accurately reflects server unavailability rather than showing a fake "bridge" across the gap.
- **Steps to Reproduce**:
  1. Run `./vllm-metrics dashboard`
  2. Look at Generation Throughput chart
  3. Find a period where a server was offline for >15 minutes
  4. Line connects across the gap, suggesting continuous throughput
- **Actual Result**: Line connects across downtime gaps, misleading the viewer
- **Expected Result**: Line breaks (NaN/split traces) when gap >15 minutes
- **Requires Clarification**: [x] no / [ ] yes
- **Plan Ref**: 
- **Status**: open

---

## Summary

| Bug ID | Severity | Area | Status | Needs Clarification |
|--------|----------|------|--------|---------------------|
| BUG-001 | critical | DB connection | resolved | no |
| BUG-002 | major | date range filter | resolved | no |
| BUG-003 | minor | use_container_width deprecation | resolved | no |
| BUG-004 | minor | date range presets | resolved | no |
| BUG-005 | major | gen throughput date range | resolved | no |
| BUG-006 | minor | gen throughput x-axis tz | resolved | no |
| BUG-007 | major | custom date range inputs | resolved | no |
| BUG-008 | major | gen throughput downtime gaps | open | no |

**Total Bugs**: 8
**Open**: 1
**In Progress**: 0
**Resolved**: 7
**Verified**: 0
