# Feature Specification: Auto-Refresh Dashboard

**Feature Branch**: 003-auto-refresh
**Created**: 2026-06-16
**Status**: Draft
**Input**: User description: "auto-refresh on dashboard — only refresh currently visible tab, not hidden components"

## User Scenarios & Testing

### User Story 1 — Auto-Refresh Dashboard (Priority: P1)

As an operator monitoring vLLM servers, I want the dashboard to periodically refresh data automatically so I can see live metrics without manually reloading.

**Why this priority:** Core usability — without auto-refresh the operator must manually reload to see current data.

**Independent Test:** Open the dashboard, wait for the refresh interval to elapse, verify all charts update without user interaction.

**Acceptance Scenarios:**
- Given the dashboard is open, When the refresh interval elapses, Then all tabs' data updates automatically
- Given the dashboard auto-refreshes, When the data updates, Then metric cards, charts, and tables reflect new data
- Given a user is examining a chart, When auto-refresh fires, Then the user's tab selection and filters are preserved

## Edge Cases

- What happens when auto-refresh fires while a user is interacting with a control (typing in date input, selecting dropdown)? The refresh should not disrupt user input — Streamlet's rerun model handles this: the new execution starts and the old one is discarded.
- What happens when the database is under heavy load or unreachable? Cached data serves the current cycle; next cycle retries.
- What happens when all data is empty (first launch)? Auto-refresh still runs — after initial empty state, it will populate when data arrives.
- What happens with multiple browser tabs open? Each tab independently auto-refreshes — no cross-tab coordination needed.

## Requirements

### Functional Requirements

- **FR-001**: Dashboard MUST auto-refresh data on the configured scrape interval (from config.yaml)
- **FR-002**: Auto-refresh MUST use the same interval as the scrape/daemon's collection cycle, read from config.yaml
- **FR-003**: Auto-refresh MUST preserve the user's current state (selected tab, date range, server filter) across refreshes
- **FR-004**: Auto-refresh MUST fail gracefully on DB errors (no error popup, retry on next cycle)
- **FR-005**: DB queries SHOULD be cached per interval to avoid redundant queries on rerun

### Key Entities

- **Auto-Refresh Interval**: The period (in seconds) between automatic data refreshes, matching the scrape interval from config.yaml
- **Refresh Cycle**: A single automatic data refresh triggered by the interval timer

## Success Criteria

### Measurable Outcomes

- **SC-001**: Dashboard auto-refreshes all tabs at the configured interval (from config.yaml) without user interaction
- **SC-002**: DB queries are cached per interval — interactions within the cycle don't re-query
- **SC-003**: Auto-refresh can be disabled by setting `interval: 0` in config.yaml
- **SC-004**: All existing 24 tests still pass plus 1 new — no regressions

## Assumptions

- All 5 tabs render on every cycle using `st.tabs()` (Streamlit's standard behavior)
- Data loading cached via `st.cache_data(ttl=interval)` — same data serves all tabs
- Auto-refresh via `streamlit-autorefresh` component (`st_autorefresh`) — no full page reload
- Interval read from config.yaml `interval` key (default 60s); `interval: 0` disables auto-refresh
