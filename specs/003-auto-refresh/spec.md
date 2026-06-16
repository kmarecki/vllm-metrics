# Feature Specification: Auto-Refresh Dashboard

**Feature Branch**: 003-auto-refresh
**Created**: 2026-06-16
**Status**: Draft
**Input**: User description: "auto-refresh on dashboard — only refresh currently visible tab, not hidden components"

## User Scenarios & Testing

### User Story 1 — Auto-Refresh Currently Visible Tab (Priority: P1)

As an operator monitoring vLLM servers, I want the dashboard to periodically refresh data automatically so I can see live metrics without manually reloading.

**Why this priority:** Core usability — without auto-refresh the operator must manually reload to see current data.

**Independent Test:** Open the dashboard on the Token Trends tab, wait for the refresh interval to elapse, verify the tab's data updates without user interaction.

**Acceptance Scenarios:**
- Given the dashboard is open on any tab, When the refresh interval elapses, Then the visible tab's data updates automatically
- Given the dashboard auto-refreshes, When the data updates, Then the metric cards, charts, and table for the visible tab reflect new data
- Given a user is examining a chart, When auto-refresh fires, Then the user's scroll position and tab selection are preserved

### User Story 2 — Skip Refresh on Hidden Tabs (Priority: P1)

As an operator, I want only the currently visible tab to query/refresh its data so that hidden tabs don't waste database resources on unnecessary queries.

**Why this priority:** Performance — with auto-refresh, all 5 tabs querying simultaneously on each cycle would multiply DB load 5x.

**Independent Test:** Open the dashboard on the Token Trends tab, observe the network/DB queries, verify that only Token Trends data is queried on refresh, not Daily Stats, Latency & Concurrency, Per-Model, or Server Stats tabs.

**Acceptance Scenarios:**
- Given 5 tabs exist on the dashboard, When auto-refresh fires, Then only the currently active tab fetches new data
- Given the operator switches to a different tab, When the next auto-refresh fires, Then the newly active tab fetches data and the previously active tab stops
- Given a tab has never been viewed this session, When the operator opens it, Then it fetches fresh data on first view

## Edge Cases

- What happens when auto-refresh fires while a user is interacting with a control (typing in date input, selecting dropdown)? The refresh should not disrupt user input — use debouncing or skip refresh if user is mid-interaction.
- What happens when the database is under heavy load or unreachable? The refresh should fail gracefully (no error toast) and retry on the next cycle.
- What happens when the user switches tabs mid-refresh? The refresh should complete for the current tab, and the new tab becomes active for the next cycle.
- What happens when all data is empty (first launch)? Auto-refresh still runs — after initial empty state, it will populate when data arrives.
- What happens with multiple browser tabs open? Each tab independently auto-refreshes — no cross-tab coordination needed.

## Requirements

### Functional Requirements

- **FR-001**: Dashboard MUST auto-refresh data on the configured scrape interval (from config.yaml) — only for the currently visible tab
- **FR-002**: Hidden/inactive tabs MUST NOT fetch or refresh data on auto-refresh cycles
- **FR-003**: Auto-refresh MUST use the same interval as the scrape/daemon's collection cycle, read from config.yaml
- **FR-004**: Auto-refresh MUST preserve the user's current state (selected tab, date range, server filter) across refreshes
- **FR-005**: Auto-refresh MUST fail gracefully on DB errors (no error popup, retry on next cycle)
- **FR-006**: Each tab's data loading SHOULD be lazy — data fetched only when the tab becomes active, not on initial load

### Key Entities

- **Auto-Refresh Interval**: The period (in seconds) between automatic data refreshes, matching the scrape interval from config.yaml
- **Active Tab**: The tab currently visible to the user — the only tab that queries data on refresh
- **Refresh Cycle**: A single automatic data update triggered by the interval timer

## Success Criteria

### Measurable Outcomes

- **SC-001**: Dashboard auto-refreshes the active tab every N seconds without user interaction
- **SC-002**: Switching tabs triggers a fresh data load for the newly active tab only
- **SC-003**: Hidden tabs show stale/initial data until the operator switches to them
- **SC-004**: Auto-refresh can be disabled via sidebar control
- **SC-005**: All existing 24 tests still pass — no regressions

## Assumptions

- Streamlit's execution model reruns the entire script on each interaction — "skip hidden tabs" means conditional data loading per active tab
- Existing `load_raw_summary()`, `load_latest_snapshots()` etc. are the data functions that should be lazily called per active tab
- Auto-refresh mechanism uses Streamlit's `st.rerun()` with `time.sleep()` or `st.empty().write()` patterns
- Scrape interval is read from config.yaml (same key used by the daemon)
