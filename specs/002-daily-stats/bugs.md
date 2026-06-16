# Bug Report: Daily Stats Tab (002-daily-stats)

**Feature**: specs/002-daily-stats/
**Created**: 2026-06-16

## Bug Log

### BUG-001: _si() helper called with pandas Series instead of scalar

- **Severity**: critical
- **Area**: vllm_metrics/dashboard.py — `_build_tab_daily_stats()`, `_si()` helper
- **Description**: The `_si()` helper refactored from `fillna(0).astype(int)` during review finding Q1 fix. `_si()` calls `pd.notna(val)` and `int(val)` expecting a scalar, but `display["prompt_tokens"]` is a pandas Series. This raises `ValueError: The truth value of a Series is ambiguous`.
- **Fix**: Reverted to original `display["prompt_tokens"].fillna(0).astype(int)` pattern which works correctly on pandas Series.
- **Plan Ref**: Review Q1 fix introduced the bug; direct revert fixes it.
- **Status**: resolved

---

## Summary

| Bug ID | Severity | Area | Status |
|--------|----------|------|--------|
| BUG-001 | critical | _build_tab_daily_stats _si() helper | resolved |

**Total Bugs**: 1
**Open**: 0
**Resolved**: 1
