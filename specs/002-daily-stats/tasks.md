# Tasks: Daily Stats Tab (002-daily-stats)

**Input**: specs/002-daily-stats/plan.md, spec.md
**Prerequisites**: plan.md, spec.md — both committed
**TDD**: Enabled — test tasks written before implementation tasks (marked [TEST])

**Format**: `T### [P?] [Story] Description — file/path`

---

## Phase 4a: Implementation

### Tests

- [X] T001 [TEST] [US1] Write test for daily stats aggregation across servers/models per local date — tests/test_dashboard.py
- [X] T002 [TEST] [US1] Write test for empty data handling in daily stats tab — tests/test_dashboard.py

### Implementation

- [X] T003 [US1] Add `_build_tab_daily_stats(daily)` function — renders table sorted by date desc with per-calendar-day totals — vllm_metrics/dashboard.py
- [X] T004 [US1] Wire 5th "Daily Stats" tab into dashboard's `run()` function — vllm_metrics/dashboard.py
- [X] T005 [P] [US1] Add bar chart of daily prompt + gen token totals — vllm_metrics/dashboard.py

### Bugfix Tasks

- [X] BF-001 [BUG-001] Revert _si() helper to original .fillna(0).astype(int) pattern — vllm_metrics/dashboard.py

**Checkpoint**: Daily Stats tab renders with table and chart, T001-T002 passing.

---

## Summary

| # | Phase | Tasks | Tests |
|---|-------|-------|-------|
| 4a | Implementation | 3 | 2 |
| **Total** | | **3** | **2** |

## Dependencies & Execution Order

- **Phase 4a**: All tasks within phase — T001-T002 (tests RED), then T003-T005 (GREEN)
- T003 and T004 can be done together; T005 is a logical extension of T003

## Verification

- Run `pytest tests/test_dashboard.py -v` — all 24 tests must pass
- All 9 FRs from spec must be covered by tests or code
