# Pre-Implement Review: 001-vllm-dashboard

## Findings

| ID | Category | Severity | Location | Summary | Recommendation |
|----|----------|----------|----------|---------|----------------|
| F1 | Naming | MEDIUM | tasks.md (all phases) vs plan.md (Phase 4a-4d) | Tasks uses "Phase 3a-3f" but these are **implementation** phases — should be "Phase 4a-4f" per workflow (Phase 3 = Tasks, Phase 4 = Implement) | Rename task phases from 3a-3f to 4a-4f |
| F2 | Coverage Gap | MEDIUM | tasks.md — missing task | Plan says "ImportError at subcommand dispatch — clear error message suggesting pip install" but no task covers the graceful handling when streamlit is not installed | Add task to handle ImportError in cmd_dashboard and show pip install hint |
| F3 | Coverage Gap | LOW | tasks.md — single data point | T027 tests single-data-point rendering but no implementation task explicitly handles it (plotly renders single points naturally, so low risk) | Either add impl note or verify in T028 |
| F4 | Coverage Gap | LOW | tasks.md — large datasets | Plan says "at most 365 rows per chart" relying on daily aggregation, but no task explicitly validates performance with large datasets | Add a note or low-effort task for large-DB smoke test |
| F5 | Terminology | LOW | plan.md vs tasks.md phase naming | Plan calls phases "Phase 4a-4d" but tasks calls them "Phase 3a-3f" — internally inconsistent | Align on "Phase 4" prefix since Phase 3 is already the tasks phase itself |

## Coverage Summary

| Requirement | Has Tasks? | Task IDs |
|-------------|-----------|----------|
| FR-001 (dashboard command) | ✅ | T010 |
| FR-002 (metric cards) | ✅ | T014 |
| FR-003 (token volume over time) | ✅ | T015 |
| FR-004 (gen throughput) | ✅ | T007, T015 |
| FR-005 (concurrent running/waiting) | ✅ | T016, T018 |
| FR-006 (KV cache usage) | ✅ | T019 |
| FR-007 (latency metrics) | ✅ | T017, T020 |
| FR-008 (per-model breakdown) | ✅ | T021, T023 |
| FR-009 (server filter) | ✅ | T022, T024 |
| FR-010 (server status sidebar) | ✅ | T013 |
| FR-011 (NVIDIA color scheme) | ✅ | T008 |
| FR-012 (raw data table) | ✅ | T025 |
| FR-013 (empty DB handling) | ✅ | T026, T028 |
| FR-014 (vllm-metrics dashboard cmd) | ✅ | T010 |

**Coverage: 14/14 FRs (100%)**

## Constitution Alignment

- **Minimal Dependencies** ✅ — streamlit only imported on `dashboard` subcommand
- **Meaningful Statistics** ✅ — reuses same queries as report command
- **Transparency** ✅ — data-model.md documents all queries

## Metrics

- Total Requirements: 14
- Total Tasks: 30
- Coverage: 100%
- Ambiguity Count: 0
- Critical Issues: 0
- High Issues: 0
- Medium Issues: 2 (F1, F2)
- Low Issues: 2 (F3, F4, F5)

## Recommendation

**Proceed** — no critical or high issues. Two medium issues worth fixing before implementation:

1. **F1** (phase numbering) — quick rename in tasks.md
2. **F2** (missing streamlit import error task) — worth adding since it's a real UX gap

Want me to fix these before moving to implement?
