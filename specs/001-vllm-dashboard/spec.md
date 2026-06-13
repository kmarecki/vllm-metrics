# Feature Specification: vLLM Dashboard

**Feature Branch**: 001-vllm-dashboard
**Created**: 2026-06-12
**Status**: Draft
**Input**: User description: "clean professional dashboard in nvidia schemas colour black and green for presenting captured vllm metrics"

## User Scenarios & Testing

### User Story 1 — View Real-Time Dashboard (Priority: P1)

As an operator of vLLM servers, I want to open a dashboard that shows live and historical metrics so I can monitor token generation, server health, and system performance at a glance.

**Why this priority:** This is the primary value of the feature — without it there's no dashboard.

**Independent Test:** Launch the dashboard, verify it displays data from the SQLite database with no errors, and all panels render.

**Acceptance Scenarios:**
- Given the dashboard is launched, When data exists in the database, Then all metric panels display non-empty charts
- Given a server is online, When the dashboard loads, Then the server status shows as online
- Given a server has been unreachable for >5 minutes, When the dashboard loads, Then that server shows as offline

### User Story 2 — Token Volume & Throughput Charts (Priority: P1)

As an operator, I want to see token volume (prompt, generation, cached) over time and generation throughput rates so I can identify usage patterns and capacity needs.

**Why this priority:** Token metrics are the core data the collector captures — charts are the primary value.

**Independent Test:** Generate a report at a known date range, verify the charted values match the raw data in the DB.

**Acceptance Scenarios:**
- Given daily_stats has data for N days, When viewing token trends, Then a bar/line chart shows prompt, gen, and cached tokens per day
- Given raw_snapshots have generation token data, When viewing throughput, Then a line chart shows gen tok/s over time

### User Story 3 — Latency & Concurrency Monitoring (Priority: P1)

As an operator, I want to see TTFT, ITL, E2E latency, KV cache usage, and concurrent request counts so I can diagnose performance issues.

**Why this priority:** Latency and concurrency directly impact user experience — essential for troubleshooting.

**Independent Test:** Compare dashboard latency values with the report command output for the same period.

**Acceptance Scenarios:**
- Given daily_stats has latency data, When viewing the latency tab, Then TTFT, ITL, and E2E are shown as time-series charts
- Given daily_stats has running/waiting data, When viewing concurrency, Then avg running and waiting are shown

### User Story 4 — Per-Model Breakdown (Priority: P2)

As an operator, I want to see metrics segmented by model name so I can understand which models consume the most resources.

**Why this priority:** Useful for capacity planning, but the dashboard is still valuable without it.

**Independent Test:** Verify the model breakdown table and chart match the report command's per-model section.

**Acceptance Scenarios:**
- Given data exists for multiple models, When viewing the model breakdown tab, Then each model appears with token and request totals
- Given filters are set, When viewing model data, Then only the selected server's models are shown

### User Story 5 — Server-Scoped Filtering (Priority: P2)

As an operator of multiple vLLM instances, I want to filter the dashboard by server so I can focus on a single machine.

**Why this priority:** Useful for multi-server setups, but the full-server view is sufficient for single-machine installations.

**Independent Test:** Select a specific server from the filter, verify all charts update to show only that server's data.

**Acceptance Scenarios:**
- Given a server filter is selected, When viewing any chart, Then only data for that server is displayed
- Given no server filter is set, When viewing charts, Then all servers' data is shown aggregated

### User Story 6 — Date Range Controls (Priority: P2)

As an operator, I want to select a date range using calendar-aligned periods (Today, This week, This month, This year, All) or a custom start/end date, so I can focus on specific time windows.

**Why this priority:** Essential for data exploration, but the dashboard is still functional with defaults.

**Independent Test:** Select each preset and verify the displayed data corresponds to the correct period.

**Acceptance Scenarios:**
- Given a calendar preset is selected, When viewing charts, Then data is scoped to that period
- Given "Yesterday" is selected, When viewing charts, Then only the previous day's data is shown
- Given "Custom..." is selected, When date inputs appear, Then the user can pick any start/end date
- Given a local timezone is configured, When checking date boundaries, Then data from 00:00 local time is included (not UTC) using shifted date filtering

## Edge Cases

- What happens when the database is empty or doesn't exist? Dashboard should show a clear informational message, not crash.
- What happens when a chart has only one data point? Line charts should render a single point marker.
- What happens when there are no generation throughput rates to compute? The throughput chart should show an empty state, not an error.
- What happens when the dashboard starts and no config.yaml is found? Should fail gracefully with a clear message.
- What happens with very large datasets (years of daily_stats)? Charts should remain responsive via server-side aggregation.

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide a dashboard command that launches a visual interface for vLLM metrics
- **FR-002**: Dashboard MUST display total tokens (prompt + generation + cached), completed requests, and prefix cache hit rate as top-level metric cards
- **FR-003**: Dashboard MUST show token volume over time with per-day breakdown by prompt, generation, and cached tokens
- **FR-004**: Dashboard MUST show generation throughput (tok/s) as a time-series chart
- **FR-005**: Dashboard MUST display average concurrent running and waiting requests over time
- **FR-006**: Dashboard MUST display KV cache usage percentage over time
- **FR-007**: Dashboard MUST show latency metrics (TTFT, ITL/TPOT, E2E) as time-series charts
- **FR-008**: Dashboard MUST display a per-model breakdown table with token counts, requests, preemptions, and average latencies
- **FR-009**: Dashboard MUST provide a server filter to scope all charts to a single server
- **FR-010**: Dashboard MUST show server online/offline status in a sidebar
- **FR-011**: Dashboard MUST use NVIDIA color scheme (dark background #0d1117 or similar, NVIDIA green #76b900 accent)
- **FR-012**: Dashboard SHOULD show the last N snapshots in a raw data table (configurable, default 50)
- **FR-013**: Dashboard MUST handle empty database gracefully with an informative message
- **FR-014**: Dashboard MUST integrate as a `vllm-metrics dashboard` subcommand

### Key Entities

- **Dashboard**: The visual interface presenting all metrics. Has multiple tabs/panels grouping related metrics.
- **Metric Card**: A top-level KPI showing a single key number (total tokens, requests, etc.) with label.
- **Time-Series Chart**: A chart showing a metric's value over time (daily aggregation or per-snapshot).
- **Server Status Indicator**: A sidebar element showing each server's online/offline state.
- **Server Filter**: A dropdown or selector that scopes the entire dashboard to one server's data.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Dashboard loads in under 5 seconds with 30 days of daily_stats data
- **SC-002**: All P1 stories (1-3) are implemented and pass acceptance scenarios
- **SC-003**: Dashboard uses the NVIDIA green (#76b900) color scheme consistently across all panels
- **SC-004**: The `vllm-metrics dashboard` command starts the dashboard without additional CLI flags

## Assumptions

- User has streamlit installed (documented in README as optional dependency)
- SQLite database exists at the configured path with at least some data
- Dashboard is launched on the same machine as the database (local access)
- No authentication or multi-user support required for v1
- Dashboard is not intended for public internet exposure
