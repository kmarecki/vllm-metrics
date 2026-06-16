# Tasks: Auto-Refresh Dashboard (003-auto-refresh)

**Input**: specs/003-auto-refresh/plan.md, spec.md
**Prerequisites**: plan.md, spec.md — both committed
**TDD**: Enabled — test tasks written before implementation tasks (marked [TEST])

**Format**: `T### [P?] [Story] Description — file/path`

---

## Phase 4a: Implementation

### Tests

- [ ] T001 [TEST] [US1] Write test for interval config parsing — 0 = disabled, positive = enabled — tests/test_dashboard.py
- [ ] T002 [TEST] [US2] Write test for cache_data TTL applied to load data on tab switch — tests/test_dashboard.py

### Implementation

- [ ] T003 [US1] Read interval from config.yaml and pass to auto-refresh loop — vllm_metrics/dashboard.py
- [ ] T004 [US1] Add time.sleep(interval) + st.rerun() at end of run() — vllm_metrics/dashboard.py
- [ ] T005 [US2] Wrap load_raw_summary, load_latest_snapshots with st.cache_data(ttl=interval) — vllm_metrics/dashboard.py

**Checkpoint**: Dashboard auto-refreshes at interval from config.yaml; DB queries cached per interval.

---

## Summary

| # | Phase | Tasks | Tests |
|---|-------|-------|-------|
| 4a | Implementation | 3 | 2 |
| **Total** | | **3** | **2** |

## Dependencies & Execution Order

- **Phase 4a**: T001-T002 (tests RED), then T003-T005 (GREEN)
- T003 feeds interval value to T004 and T005

## Verification

- Run `pytest tests/test_dashboard.py -v` — all 26 tests must pass
- Dashboard auto-refreshes at configured interval
- Setting interval=0 in config.yaml disables auto-refresh
- DB queries are cached: filter changes don't re-query until interval elapses
