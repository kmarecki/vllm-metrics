# Close: Daily Stats Tab

**Feature**: 002-daily-stats
**Date**: 2026-06-16
**Branch**: feat/002-daily-stats

## Spec Health Score

**100%** — All requirements fulfilled.

| Category | Count |
|----------|-------|
| ✅ Resolved | 9 |
| ⚠️ Acknowledged | 0 |
| ❌ Not Done | 0 |

## Intent Alignment

✅ Fully aligned — implementation matches spec for all 9 FRs.

## Artifact State

| Artifact | Status |
|----------|--------|
| spec.md | ✅ Created |
| plan.md | ✅ Created |
| tasks.md | ✅ All 5 tasks complete |
| history.md | ✅ Complete |

## Key Decisions

- **Reused existing data layer**: `load_raw_summary()` already returns timezone-shifted per-day data — no new DB queries
- **Added as 5th tab**: Inserted between Per-Model Breakdown and Server Stats tabs
- **Aggregation per local date**: Groupby across (server, model), summed for tokens/requests, averaged for concurrent metrics
- **Table + chart**: Table shows per-day rows sorted descending; bar chart shows prompt vs gen tokens grouped per day

## Metrics

- **Files modified**: 2 (vllm_metrics/dashboard.py, tests/test_dashboard.py)
- **Tests**: 24/24 passing (22 existing + 2 new)
- **Dashboard lines added**: ~75 LOC
- **New functions**: 1 (_build_tab_daily_stats)

## Close (Reopened — 2026-06-16)

### Spec Health Score

**100%** — All requirements fulfilled (unchanged from original close).

| Category | Count |
|----------|-------|
| ✅ Resolved | 9 |
| ⚠️ Acknowledged | 0 |
| ❌ Not Done | 0 |

**Previous health**: 100% → **Current health**: 100%

### Scoped Changes

- **BUG-001** (critical, resolved): `_si()` helper refactored during review Q1 fix called `pd.notna()` on a pandas Series, raising `ValueError: truth value of a Series is ambiguous`. Reverted to original `.fillna(0).astype(int)` pattern. 2-line regression, fixed in 2 lines.

### Artifact State (Reopened)

| Artifact | Status |
|----------|--------|
| bugs.md | ✅ Created (BUG-001 resolved) |
| tasks.md | ✅ BF-001 added and complete |
| review.md | ✅ All findings fixed (Q1, Q2) |
| history.md | ✅ Bugfix logged |
| close.md | ✅ Updated (this section) |

### Key Decisions

- **Bug log before revert**: BUG-001 logged in bugs.md for traceability even though the fix was a direct revert of the problematic refactor
- **Tests strengthened**: Q2 finding turned `test_daily_stats_empty` (callable-only) into `test_daily_stats_multiple_dates` — verifies multi-date aggregation, descending sort, and Total Tokens = prompt + gen

### Metrics (Reopened)

- **New bugs**: 1 (BUG-001, critical — resolved)
- **Tests**: 24/24 passing (no new tests needed for revert)
- **Files changed in bugfix**: 4 (dashboard.py fix, bugs.md, history.md, tasks.md)

