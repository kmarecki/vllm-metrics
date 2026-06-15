# Feature Specification: Daily Stats Tab

**Feature Branch**: 002-daily-stats
**Created**: 2026-06-16
**Status**: Draft
**Input**: User description: "add a new tab showing per-calendar-day stats matching report's DAILY TREND section, using local timezone"

## User Scenarios & Testing

### User Story 1 — View Daily Usage Stats (Priority: P1)

As an operator, I want to see per-calendar-day usage stats in the dashboard — matching what the report command shows in its DAILY TREND section — so I can track daily token production, request volume, and concurrent usage at a glance.

**Why this priority:** This surface data already computed by the report command for CLI users; dashboard users need the same visibility.

**Independent Test:** Select a date range, verify the daily stats table shows prompt tokens, gen tokens, completed requests per local calendar day, sorted descending by date.

**Acceptance Scenarios:**
- Given the dashboard is launched, When the Daily Stats tab is selected, Then a table shows each calendar day with total tokens, prompt, gen, and requests
- Given data exists for multiple servers and models on the same date, When viewing Daily Stats, Then values are aggregated per day (summed across servers/models)
- Given a local timezone is configured, When checking date boundaries, Then each calendar day uses local timezone dates (shifted from UTC)
- Given the date range is set to a specific period, When viewing Daily Stats, Then only days within that range are shown

### User Story 2 — Daily Token Bar Chart (Priority: P2)

As an operator, I want to see a visual bar chart of daily token production so I can spot trends and anomalies at a glance.

**Why this priority:** Complements the table with a visual overview; table alone is sufficient for raw data.

**Independent Test:** Verify the bar chart shows prompt and generation token bars grouped by date, matching the table values.

**Acceptance Scenarios:**
- Given daily data exists, When viewing Daily Stats, Then a grouped bar chart shows prompt and gen tokens per day
- Given only one day of data, When viewing Daily Stats, Then the chart renders a single pair of bars

## Edge Cases

- What happens when daily data has multiple (server, model) rows per date? Data is aggregated into a single row per date.
- What happens when the daily summary is empty? The tab shows an informative message, not a crash.
- What happens when a server was offline for a whole day? That day still shows data for other servers; no special handling needed.

## Requirements

### Functional Requirements

- **FR-001**: Dashboard MUST display a new "Daily Stats" tab showing per-calendar-day stats
- **FR-002**: Daily Stats MUST show date (local timezone), total tokens, prompt tokens, generation tokens, and completed requests per day
- **FR-003**: Daily Stats MUST aggregate across all servers and models per date (one row per day)
- **FR-004**: Daily Stats MUST sort rows by date descending (most recent first)
- **FR-005**: Daily Stats MUST include avg running and avg waiting concurrent averages per day
- **FR-006**: Daily Stats SHOULD show a grouped bar chart of daily prompt and gen tokens
- **FR-007**: Daily Stats MUST use the same timezone-shifted date boundaries as the rest of the dashboard
- **FR-008**: Daily Stats MUST respect the selected date range filter
- **FR-009**: Daily Stats MUST handle empty data gracefully with an info message

### Key Entities

- **Daily Stats Tab**: A 5th tab in the dashboard displaying per-calendar-day aggregated stats
- **Calendar Day**: A single day in the configured local timezone, aggregated across all servers and models

## Success Criteria

### Measurable Outcomes

- **SC-001**: Daily Stats tab renders data matching report command's DAILY TREND for the same period
- **SC-002**: Daily Stats uses existing data layer (load_raw_summary) — no new DB queries needed
- **SC-003**: All 9 FRs implemented and acceptance scenarios pass

## Assumptions

- Existing `load_raw_summary()` function already returns timezone-aware per-day data
- Same data layer used by the report command's DAILY TREND section
- No new database tables or queries needed
