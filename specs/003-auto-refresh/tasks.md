# Tasks: Auto-Refresh Dashboard (003-auto-refresh)

**Input**: specs/003-auto-refresh/plan.md, spec.md
**Prerequisites**: plan.md, spec.md — both committed
**TDD**: Enabled

**Format**: `T### [P?] [Story] Description — file/path`

---

## Phase 4a: Implementation

### Tests

- [X] T001 [TEST] [US1] Write test for interval config parsing — 0 = disabled, positive = enabled — tests/test_dashboard.py

### Implementation

- [X] T003 [US1] Read interval from config.yaml in run() — vllm_metrics/dashboard.py
- [X] T004 [US1] Add CSS-styled horizontal radio as tab bar, replacing st.tabs() — vllm_metrics/dashboard.py
- [X] T005 [US1] Reorganize per-tab rendering into if/elif branches based on active_tab radio value — vllm_metrics/dashboard.py
- [X] T006 [US1] Wrap load_raw_summary and load_latest_snapshots with st.cache_data(ttl=interval) — vllm_metrics/dashboard.py
- [X] T007 [US1] Add time.sleep(interval) + st.rerun() at end of run() — vllm_metrics/dashboard.py

**Checkpoint**: Dashboard auto-refreshes at config interval; only active tab renders charts; tab switch is instant (cached data).

---

## Summary

| # | Phase | Tasks | Tests |
|---|-------|-------|-------|
| 4a | Implementation | 5 | 2 |
| **Total** | | **5** | **2** |

## Dependencies & Execution Order

- **Phase 4a**: T001-T002 (tests RED), then T003-T007 (GREEN)
- T003 (interval) feeds T006 (cache TTL) and T007 (sleep duration)

## Verification

- Run `pytest tests/test_dashboard.py -v` — all 26+ tests pass
- Dashboard shows horizontal radio tab bar styled in NVIDIA green
- Only active tab renders charts — switching tabs is instant (no DB re-query)
- Auto-refresh fires every `interval` seconds
- Setting `interval: 0` in config.yaml disables auto-refresh
