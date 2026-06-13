# Tasks: vLLM Dashboard (001-vllm-dashboard)

**Input**: specs/001-vllm-dashboard/plan.md, spec.md, data-model.md, research.md
**Prerequisites**: plan.md, spec.md — both committed
**TDD**: Enabled — test tasks written before implementation tasks (marked [TEST])

**Format**: `T### [P?] [Story] Description — file/path`

- **P**: Can run in parallel (no file conflicts)
- **US**: User story reference
- **FR**: Functional requirement reference

---

## Phase 4a: Setup — Test Infrastructure

**Purpose**: Create the test framework so all subsequent phases use TDD.

- [ ] T001 [P] [Setup] Create `tests/__init__.py` and `tests/conftest.py` with pytest config, DB fixtures (in-memory SQLite with schema), and shared helpers — tests/conftest.py
- [ ] T002 [TEST] [Setup] Write test for formatting helpers (fmt_number, fmt_ms, fmt_s, fmt_pct, fmt_decimal) — tests/test_dashboard.py
- [ ] T003 [Setup] Implement formatting helpers in vllm_metrics/dashboard.py

**Checkpoint**: Test framework ready, formatting helpers covered.

---

## Phase 4b: Core Infrastructure

**Purpose**: Dashboard file, CLI subcommand, and data layer that all tabs depend on.

### Tests

- [ ] T004 [TEST] [Setup] Write test for `load_servers()` — returns correct columns, handles empty table — tests/test_dashboard.py
- [ ] T005 [TEST] [Setup] Write test for `load_daily_summary()` — returns aggregated data, respects date filter — tests/test_dashboard.py
- [ ] T006 [TEST] [Setup] Write test for `load_latest_snapshots()` — returns correct columns, respects limit — tests/test_dashboard.py
- [ ] T007 [TEST] [Setup] Write test for gen throughput computation (consecutive snapshots, sane rate filtering, empty edge case) — tests/test_dashboard.py

### Implementation

- [ ] T008 [P] [Setup] Create `vllm_metrics/dashboard.py` with DB connection (get_conn cached), config loader, formatting helpers (fmt_number, fmt_ms, fmt_s, fmt_pct, fmt_decimal), NVIDIA CSS injection — vllm_metrics/dashboard.py
- [ ] T009 [P] [Setup] Implement data layer: `load_servers()`, `load_daily_summary()`, `load_latest_snapshots()` — vllm_metrics/dashboard.py
- [ ] T010 [P] [Setup] Wire `vllm-metrics dashboard` subcommand in CLI — add `dashboard` parser entry, `cmd_dashboard` function that spawns `streamlit run` — vllm-metrics
- [ ] T010b [P] [Setup] Add ImportError handling in cmd_dashboard — if streamlit not installed, print clear message with `pip install streamlit plotly` hint — vllm-metrics

**Checkpoint**: `vllm-metrics dashboard` launches, DB connection works, all query functions tested.

---

## Phase 4c: Token Trends Tab (User Story 1 — US1, FR-001/002/003/004)

**Purpose**: Global metric cards and token volume/throughput charts — the primary dashboard view.

### Tests

- [ ] T011 [TEST] [US1] Write test for global totals aggregation — verifies summed prompt/gen/cached/requests match expected values — tests/test_dashboard.py
- [ ] T012 [TEST] [US1] Write test for token volume daily aggregation — verifies group-by-date sums — tests/test_dashboard.py

### Implementation

- [ ] T013 [US1] Build sidebar: server list, online/offline status indicators, date range selector — vllm_metrics/dashboard.py
- [ ] T014 [US1] Build top-level metric cards row: total tokens, prompt, gen, requests, cache hit rate — vllm_metrics/dashboard.py
- [ ] T015 [US1] Build token trends tab: daily token volume bar chart (prompt + gen + cached), generation throughput line chart — vllm_metrics/dashboard.py

**Checkpoint**: Token Trends tab renders with real data, metrics match report command output.

---

## Phase 4d: Latency & Concurrency Tab (User Story 2 — US2, FR-005/006/007)

**Purpose**: Performance monitoring — concurrency, KV cache, and latency charts.

### Tests

- [ ] T016 [TEST] [US2] Write test for concurrency aggregation (avg_running, avg_waiting, max_running) — tests/test_dashboard.py
- [ ] T017 [TEST] [US2] Write test for latency metrics extraction (avg_ttft_ms, avg_itl_ms, avg_e2e_s) — tests/test_dashboard.py

### Implementation

- [ ] T018 [US2] Build concurrency charts: avg running + waiting line chart, peak running bar chart — vllm_metrics/dashboard.py
- [ ] T019 [US2] Build KV cache usage area chart — vllm_metrics/dashboard.py
- [ ] T020 [US2] Build latency metrics tab: TTFT, ITL, E2E time-series charts — vllm_metrics/dashboard.py

**Checkpoint**: Latency & Concurrency tab renders, values match report command.

---

## Phase 4e: Per-Model & Server Stats Tabs (User Story 3 — US3, FR-008/009/012)

**Purpose**: Per-model breakdown table/chart and server-level raw data view.

### Tests

- [ ] T021 [TEST] [US3] Write test for per-model breakdown query (group-by model, summed tokens) — tests/test_dashboard.py
- [ ] T022 [TEST] [US3] Write test for server filter scoping (all queries respect selected server) — tests/test_dashboard.py

### Implementation

- [ ] T023 [P] [US3] Build per-model breakdown tab: summary table + token distribution bar chart — vllm_metrics/dashboard.py
- [ ] T024 [P] [US3] Build server filter dropdown in sidebar, wire to all charts — vllm_metrics/dashboard.py
- [ ] T025 [US3] Build server stats tab: expandable server cards + raw snapshots table (last 50) — vllm_metrics/dashboard.py

**Checkpoint**: All four tabs render, server filter works.

---

## Phase 4f: Polish & Validation

**Purpose**: Edge case handling, README update, and final validation.

### Tests

- [ ] T026 [TEST] [Polish] Write test for empty database edge case (dashboard shows info message, not crash) — tests/test_dashboard.py
- [ ] T027 [TEST] [Polish] Write test for single-data-point edge case (line chart renders marker) — tests/test_dashboard.py

### Implementation

- [ ] T028 [Polish] Add empty DB / missing config graceful handling to dashboard.py — vllm_metrics/dashboard.py
- [ ] T029 [Polish] Update README with dashboard usage, optional dependencies, and screenshots (if available) — README.md
- [ ] T030 [Polish] Run quickstart.md validation scenarios, fix any issues

**Checkpoint**: All edge cases handled, README updated, validation passes.

---

## Summary

| # | Phase | Tasks | Tests | Files Created |
|--|-------|-------|-------|---------------|
| 4a | Test Infrastructure | 3 | 1 | tests/conftest.py, tests/test_dashboard.py |
| 4b | Core Infrastructure | 8 | 4 | vllm_metrics/dashboard.py (+ CLI edit) |
| 4c | Token Trends | 5 | 2 | — |
| 4d | Latency & Concurrency | 5 | 2 | — |
| 4e | Per-Model & Server Stats | 5 | 2 | — |
| 4f | Polish & Validation | 5 | 2 | README.md |
| **Total** | | **31** | **13** | **3 new, 2 modified** |

## Dependencies & Execution Order

### Bugfix Tasks

- [ ] BF-001 [BUG-001] Add `check_same_thread=False` to sqlite3.connect() in vllm_metrics/db.py — vllm_metrics/db.py
- [ ] BF-002 [BUG-002] Add raw_snapshots fallback to dashboard — add `load_raw_summary()`, modify `run()` to fall back when daily_stats returns empty — vllm_metrics/dashboard.py

### Phase Dependencies
- **4a**: No dependencies — start immediately
- **4b**: Depends on 4a (test framework) — BLOCKS all subsequent phases
- **4c, 4d, 4e**: All depend on 4b — can proceed in parallel after 4b completes
- **4f**: Depends on 4c, 4d, 4e — final phase

### Parallel Opportunities
- All [P] tasks within a phase can run in parallel
- 4c, 4d, 4e can proceed in parallel after 4b completes
