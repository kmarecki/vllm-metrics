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
- **Status**: open

## Summary

| Bug ID | Severity | Area | Status | Needs Clarification |
|--------|----------|------|--------|---------------------|
| BUG-001 | critical | DB connection | resolved | no |
| BUG-002 | major | date range filter | resolved | no |
| BUG-003 | minor | use_container_width deprecation | resolved | no |
| BUG-004 | minor | date range presets | open | no |

**Total Bugs**: 4
**Open**: 1
**In Progress**: 0
**Resolved**: 3
**Verified**: 0
