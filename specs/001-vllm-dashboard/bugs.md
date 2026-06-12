# Bug Report: vLLM Dashboard

**Feature**: specs/001-vllm-dashboard/
**Created**: 2026-06-12
**Status**: Open

## Bug Log

### BUG-001: SQLite thread safety — check_same_thread=False not set

- **Severity**: critical
- **Area**: vllm_metrics/dashboard.py — DB connection via `@st.cache_resource`
- **Description**: Streamlit runs each interaction in a new thread. The SQLite connection created in one thread via `@st.cache_resource` is reused in another thread, causing `sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread.`
- **Steps to Reproduce**:
  1. Run `./vllm-metrics dashboard`
  2. Wait for the dashboard to load (first render works because cache_resource creates the conn)
  3. Interact with the dashboard (change filter, select tab) — Streamlit reruns in a new thread
  4. Error appears: `ProgrammingError: SQLite objects created in a thread can only be used in that same thread.`
- **Actual Result**: Dashboard crashes on any interaction after initial load
- **Expected Result**: Dashboard should work across Streamlit's thread-switching reruns
- **Requires Clarification**: [x] no / [ ] yes
- **Plan Ref**: 
- **Status**: open

---

## Summary

| Bug ID | Severity | Area | Status | Needs Clarification |
|--------|----------|------|--------|---------------------|
| BUG-001 | critical | DB connection | open | no |

**Total Bugs**: 1
**Open**: 1
**In Progress**: 0
**Resolved**: 0
**Verified**: 0
