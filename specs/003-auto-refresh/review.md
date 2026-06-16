# Pre-Implement Review: 003-auto-refresh

**Mode**: Pre-implement (cross-artifact consistency check)

## Findings

| ID | Category | Severity | Location | Summary | Recommendation |
|----|----------|----------|----------|---------|----------------|
| A1 | Drift | HIGH | spec.md SC-004 vs plan.md | SC-004: "Auto-refresh can be disabled via sidebar control" — plan uses `interval: 0` in config.yaml, no sidebar control | Update spec: SC-004 → "Auto-refresh can be disabled by setting interval: 0 in config.yaml" |
| A2 | Overspecification | MEDIUM | spec.md FR-002 / FR-006 vs plan.md | "Hidden tabs MUST NOT fetch/refresh data" / "lazy data loading" — plan explains all `with tab:` blocks execute on every rerun (Streamlit constraint). Optimization is cache_data TTL, not truly skipping execution | Reconcile spec wording: change FR-002 to "Hidden tabs MUST NOT re-query the database" and FR-006 to "Tab data SHOULD be served from cache across refreshes" |
| A3 | Artifact contamination | LOW | plan.md L226-L229 | Raw tool call XML embedded in plan body (`<｜DSML｜tool_calls><｜DSML｜invoke ...>`) — leftover from prior implementation attempt | Clean up: remove the `<｜DSML｜tool_calls>` tags |
| A4 | Test feasibility | MEDIUM | tasks.md T002 | "Test for cache_data TTL applied to load data on tab switch" — `st.cache_data` TTL behavior can't be unit tested without Streamlit runtime | Replace T002 with a simpler test: "Verify interval config value is read correctly and passed to cache wrapper" |

## Coverage Summary

| Requirement | Has Task? | Task IDs | Notes |
|-------------|-----------|----------|-------|
| FR-001 | Yes | T003, T004 | auto-refresh at interval |
| FR-002 | Yes (partial) | T005 | cache_data TTL prevents re-queries on hidden tab reruns — not a true "skip" |
| FR-003 | Yes | T003 | interval from config.yaml |
| FR-004 | Yes | — | Preserved by Streamlit's built-in state persistence |
| FR-005 | Yes | — | Graceful on DB error (cached data served) |
| FR-006 | Partial | T005 | Cache TTL approximates lazy loading |
| SC-001 | Yes | T004 | sleep + rerun cycle |
| SC-002 | No | — | No task for "tab switch triggers fresh load" |
| SC-003 | No | — | No task for hidden tab staleness display |
| SC-004 | Yes | T003 | interval: 0 = disabled |

## Constitution Alignment

| Gate | Status |
|------|--------|
| Minimal Dependencies | ✅ PASS — no new packages |
| Meaningful Statistics | ✅ PASS — interval matches scrape rate |
| Transparency | ✅ PASS — interval in config.yaml |

## Metrics

- Total Requirements (FRs): 6
- Total Tasks: 5
- Coverage: ~80% (FR-002/FR-006 need spec reconciliation)
- Critical Issues: 0
- High: 1 (A1 — spec/plan drift)
- Medium: 2 (A2 spec overpromise, A4 test feasibility)
- Low: 1 (A3 artifact contamination)

## Recommendations

**Must fix before implement:**
1. (A1) Patch spec.md SC-004: "sidebar" → "config.yaml interval: 0"
2. (A2) Patch spec.md FR-002 and FR-006 to match plan's honest accounting of Streamlit's execution model — replace "MUST NOT fetch" with "MUST NOT re-query DB" and "SHOULD be lazy" with "SHOULD be served from cache"
3. (A3) Clean up the embedded tool call XML from plan.md
4. (A4) Replace T002 with a testable task

**Proceed**: After fixes, coverage is sufficient for implementation.
