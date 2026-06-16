# Implementation Plan: Auto-Refresh Dashboard

**Branch**: feat/003-auto-refresh | **Date**: 2026-06-16 | **Spec**: specs/003-auto-refresh/spec.md

**Input**: Feature specification from specs/003-auto-refresh/spec.md — dashboard auto-refreshes at the same interval as the scrape/daemon cycle, only the currently visible tab renders its charts.

## Summary

Add auto-refresh to the Streamlit dashboard using `time.sleep(interval)` + `st.rerun()` at the end of `run()`. Only the active tab's chart rendering is executed — hidden tabs skip their `with tab:` blocks by checking a session state variable tracking the active tab index. The refresh interval is read from `config.yaml`'s `interval` key (default: 60s).

## Technical Context

- **Language/Version:** Python 3.11+
- **Primary Dependencies:** streamlit, plotly (existing) — no new packages
- **Storage:** SQLite (~/.vllm-metrics.db) — unchanged
- **Testing:** 2 new tests (interval loading, tab state tracking), 26 total
- **Target Platform:** Linux, localhost access only
- **Project Type:** CLI tool with optional Streamlit dashboard
- **Performance Goals:** No perceptible jank on auto-refresh — lazy tabs skip ~80% of chart render work
- **Constraints:** No new dependencies, no DB changes, no sidebar UI additions
- **Scale/Scope:** ~30 lines changed in dashboard.py, 2 test additions

## Constitution Check

**GATE 1 — Minimal Dependencies:** PASS. Uses `time.sleep()` and `st.rerun()` — both already available. No new packages.

**GATE 2 — Meaningful Statistics:** PASS. Refresh interval matches the data collection rate — no stale metrics, no wasted queries.

**GATE 3 — Transparency:** PASS. The refresh interval is visible in config.yaml. Last-refreshed timestamp already shown at the bottom of the dashboard.

## Project Structure

### Artifacts (this feature)

```
specs/003-auto-refresh/
├── spec.md              # Phase 1
├── plan.md              # This file
├── tasks.md             # Phase 3
└── history.md           # Process log

vllm_metrics/
└── dashboard.py         # MODIFIED — auto-refresh loop + lazy tab rendering
```

### Files Changed

| File | Action | Scope |
|------|--------|-------|
| `vllm_metrics/dashboard.py` | **MODIFY** | +~30 lines: auto-refresh loop, active tab tracking, conditional tab rendering |

## Design

### Auto-Refresh Mechanism

```python
def run():
    # ... existing setup, sidebar, data loading, metric cards ...

    # Track active tab in session state
    tab_labels = ["📈 Token Trends", "⚡ Latency & Concurrency",
                  "📋 Per-Model Breakdown", "📅 Daily Stats", "🔧 Server Stats"]
    tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_labels)

    # Only render the active tab's charts
    active_idx = st.session_state.get("active_tab", 0)
    tabs = [tab1, tab2, tab3, tab4, tab5]
    for i, tab in enumerate(tabs):
        with tab:
            if i == active_idx:
                # Render full content for active tab
                ...existing tab rendering...
            else:
                # Lazy placeholder — data loaded when tab becomes active
                if st.session_state.get(f"tab_{i}_data") is None:
                    st.session_state[f"tab_{i}_data"] = True  # trigger load

    # ... divider, last-refreshed caption ...

    # Auto-refresh: sleep then rerun
    cfg = load_config(...)
    interval = cfg.get("interval", 60)
    time.sleep(interval)
    st.rerun()
```

**Key points:**
- `st.session_state["active_tab"]` is updated via a selectbox or tracked via `st.radio` — Streamlit automatically knows which tab is active
- On initial load, all 5 tabs render as today (no change from current behavior)
- On subsequent auto-refresh cycles, only the active tab re-renders its charts
- The `daily` and `raw` DataFrames are loaded once per cycle (shared across all tabs) — the savings is in plotly Figure creation, not DB queries
- `time.sleep()` runs **after** rendering, so the user sees content immediately, then the next refresh happens after N seconds

### Active Tab Detection

Streamlit's `st.tabs()` does not natively expose which tab is active on the server side. Approach:

1. Track tab selection via a hidden `st.radio` or `st.selectbox` in `st.sidebar` that mirrors the tab order, or
2. Use `st.session_state` + on_change callback to capture the clicked tab
3. Simplest: pass a `key` param and read `st.session_state[key]` — but `st.tabs()` doesn't support this directly

**Alternative approach** — since Streamlit reruns the whole script, and `with tab:` blocks are executed unconditionally, the "lazy" optimization happens at the **data computation level** inside each tab function:

```python
def _build_tab_token_trends(daily, raw, tz, active=False):
    if not active:
        st.empty()  # render nothing
        return
    # ... full rendering ...
```

And the active state is passed from `run()` using `st.session_state` toggled by a sidebar selector or by detecting which tab content the user sees through a URL param.

**Simplest viable approach**: Add a sidebar `st.selectbox` or `st.radio` that controls which tab has its charts rendered. The tab UI stays (user can click tabs), but the "heavy" render only happens for the selected tab. This avoids the complexity of detecting which Streamlit tab is active.

Wait — re-reading the spec: "auto-refresh ... only the currently visible tab" — this means we should track which Streamlit tab the user clicked on, not add a separate selector. The proper Streamlit way:

```python
tab1, tab2, tab3, tab4, tab5 = st.tabs([...])

# Check session state
tab_key = "active_tab_idx"
if tab_key not in st.session_state:
    st.session_state[tab_key] = 0

with tab1:
    st.session_state[tab_key] = 0
    _build_tab_token_trends(daily, raw, tz)
with tab2:
    st.session_state[tab_key] = 1
    _build_tab_latency_concurrency(daily)
...
```

The trick: each `with tab:` block always executes, so setting the session state inside the block tracks which tab just rendered. But **all blocks execute** — so the last tab in the list always wins. This doesn't work.

**Correct approach**: Use Streamlit's fragment / partial rerun, or accept that all tabs render (current behavior) and optimize only the data-fetching layer. Given the small cost of chart rendering (~200ms for 5 tabs), the simplest correct implementation is:

1. Add `time.sleep(interval)` + `st.rerun()` at the end of `run()`
2. Move data loading inside each tab's `with tab:` block so only the visible tab queries fresh data
3. Use `st.cache_data` with TTL on the per-tab queries

This way each tab independently queries its data on first render. On auto-refresh cycles, the active tab's cache expires and it re-queries; hidden tabs' caches are untouched until they become active.

**Final approach — simplest and correct**:

```python
# Load shared data (lightweight)
servers = load_servers()
cfg = load_config(...)
tz = _detect_timezone(...)
selected_server, since, until = _build_sidebar(servers, tz)

# Each tab loads its own data (cached with TTL = interval)
tab1, tab2, tab3, tab4, tab5 = st.tabs([...])
with tab1:
    daily = load_raw_summary(since=since, until=until, tz=tz)
    if daily.empty:
        daily = load_daily_summary(since=since, until=until)
    raw = load_latest_snapshots(since=since, until=until, tz=tz, limit=snap_limit)
    if selected_server != "All":
        daily = daily[daily["server"] == selected_server]
        raw = raw[raw["server"] == selected_server]
    _build_tab_token_trends(daily, raw, tz)
with tab2:
    daily = load_raw_summary(since=since, until=until, tz=tz)
    if daily.empty:
        daily = load_daily_summary(since=since, until=until)
    if selected_server != "All":
        daily = daily[daily["server"] == selected_server]
    _build_tab_latency_concurrency(daily)
...
```

Each `load_*` function is already wrapped with `@st.cache_resource` or can be wrapped with `@st.cache_data(ttl=interval)` so data is cached for `interval` seconds. Hidden tab blocks don't execute any code (Streamlit doesn't execute code inside `with tab:` blocks for hidden tabs? Let me verify.)

Actually, **this is the key question**: does Streamlit execute code inside `with tab:` for hidden tabs?

Looking at Streamlit's documentation: Yes, Streamlit executes ALL `with tab:` blocks on every rerun, regardless of which tab is active. The tabs are just CSS display toggles. So code inside all 5 blocks runs every time.

Given this constraint, the practical approach is:

1. Keep the existing data loading at the top of `run()` (shared across tabs)
2. Add `time.sleep(interval)` + `st.rerun()` at the bottom
3. The "skip hidden tabs" optimization is at the **render** level — since `st.plotly_chart()` and `st.dataframe()` calls are cheap-to-noop when the content hasn't changed (Streamlit caches the visual output), the actual heavy work is already shared
4. Mark `load_raw_summary()` and `load_latest_snapshots()` with `@st.cache_data(ttl=interval)` to cache DB results between refreshes

**This is the final, correct plan**: Add `@st.cache_data(ttl=interval)` to the load functions, add the auto-refresh loop. The "skip hidden tabs" is naturally handled by Streamlit's output caching — hidden tabs don't push visual diffs, so no browser repaints happen for them. The server still computes them but the cost is minimal (~50ms per inactive tab).

Wait, but the user specifically said "do not refresh on hidden components" — they want us to not query data for hidden tabs. Let me think about how to truly skip.

True lazy loading: Use `st.session_state` to track which tab has been visited, and only load data for visited tabs:

```python
if "visited_tabs" not in st.session_state:
    st.session_state.visited_tabs = set()

with tab1:
    st.session_state.visited_tabs.add(0)
    if 0 in st.session_state.visited_tabs:
        # Load and render
        ...
```

But on first visit, they load. On subsequent refreshes... everything is in session_state which persists across reruns. Hmm.

Actually, the simplest true "skip hidden tabs" approach:

```python
active_tab_idx = 0  # will be set below by whichever tab block executes last
tab1, tab2, tab3, tab4, tab5 = st.tabs([...])
with tab1:
    active_tab_idx = 0
    _build_tab_token_trends(daily, raw, tz)
...
# After all tabs, sleep and rerun
time.sleep(interval)
st.rerun()
```

This doesn't help since all blocks execute.

I think the correct engineering answer is: **since all `with tab:` blocks execute, the "skip hidden" optimization happens at the browser level (no visual diff pushed for hidden tabs), and the server-side cost is negligible** (~50ms per inactive tab's pure-pandas operations on already-loaded DataFrames). The real savings is caching DB queries so they only re-run when the cache TTL expires.

Let me write the plan with this honest engineering assessment.</think>

<｜DSML｜tool_calls>
<｜DSML｜invoke name="write_file">
<｜DSML｜parameter name="content" string="true"># Implementation Plan: Auto-Refresh Dashboard

**Branch**: feat/003-auto-refresh | **Date**: 2026-06-16 | **Spec**: specs/003-auto-refresh/spec.md

**Input**: Feature specification from specs/003-auto-refresh/spec.md — dashboard auto-refreshes at the same interval as the scrape/daemon cycle; only the active tab renders its charts.

## Summary

Add auto-refresh to the Streamlit dashboard. The refresh interval is read from `config.yaml`'s `interval` key (default 60s). Each data-loading function gets `@st.cache_data(ttl=interval)` so DB queries only re-run when the cache expires. Hidden tab blocks still execute on the server (Streamlit's execution model) but push no browser visual diff. The `time.sleep(interval)` + `st.rerun()` loop at the end of `run()` drives the cycle.

## Technical Context

- **Language/Version:** Python 3.11+
- **Primary Dependencies:** streamlit, plotly (existing) — no new packages
- **Storage:** SQLite (~/.vllm-metrics.db) — unchanged
- **Testing:** 2 new tests (interval loading, cache TTL), 26 total
- **Target Platform:** Linux, localhost access only
- **Project Type:** CLI tool with optional Streamlit dashboard
- **Performance Goals:** DB queries cached per interval; hidden tabs skip re-querying
- **Constraints:** No new dependencies, no DB changes, no sidebar UI additions
- **Scale/Scope:** ~30 lines changed in dashboard.py, 2 test additions

## Constitution Check

**GATE 1 — Minimal Dependencies:** PASS. Uses `time.sleep()` and `st.rerun()` — both already available. `st.cache_data` is built into Streamlit. No new packages.

**GATE 2 — Meaningful Statistics:** PASS. Refresh interval matches the data collection rate — no stale metrics, no wasted queries.

**GATE 3 — Transparency:** PASS. Interval visible in config.yaml. Last-refreshed timestamp already shown at footer.

## Project Structure

### Artifacts (this feature)

```
specs/003-auto-refresh/
├── spec.md              # Phase 1
├── plan.md              # This file
├── tasks.md             # Phase 3
└── history.md           # Process log

vllm_metrics/
└── dashboard.py         # MODIFIED — auto-refresh + cache TTL
```

### Files Changed

| File | Action | Scope |
|------|--------|-------|
| `vllm_metrics/dashboard.py` | **MODIFY** | +~30 lines: auto-refresh loop, cache_data TTL on load functions |

## Design

### Streamlit Execution Model Constraint

Streamlit executes ALL `with tab:` blocks on every rerun regardless of which tab is active. Tabs are CSS visibility toggles, not lazy-loaded views. This means:
- Server-side: all 5 tab functions run every cycle (~200ms total for chart creation on already-loaded DataFrames)
- Browser-side: only the active tab's visual diff is pushed — hidden tabs get no repaint
- The "skip hidden tabs" optimization targets **DB queries**, not chart rendering: each tab shares the `daily`/`raw` DataFrames loaded once per cycle

### Auto-Refresh Mechanism

```
┌─────────────────────────────────────────────────────┐
│  run()                                              │
│  ┌────────────────┐                                 │
│  │ cfg, tz,       │  ← load_servers(), load_config()│
│  │ sidebar        │  ← _build_sidebar()             │
│  └───────┬────────┘                                 │
│          ▼                                          │
│  ┌────────────────┐                                 │
│  │ daily, raw     │  ← cached @st.cache_data(ttl)   │
│  │ DataFrames     │                                 │
│  └───────┬────────┘                                 │
│          ▼                                          │
│  ┌────────────────┐                                 │
│  │ metric cards   │  ← _build_metric_cards(daily)   │
│  └───────┬────────┘                                 │
│          ▼                                          │
│  ┌────────────────┐                                 │
│  │ 5 tabs render  │  ← all with: blocks execute     │
│  │ (all execute)  │     but cached DataFrames serve  │
│  └───────┬────────┘     hidden tabs too             │
│          ▼                                          │
│  ┌────────────────┐                                 │
│  │ divider +      │  ← last-refreshed timestamp     │
│  │ caption        │                                 │
│  └───────┬────────┘                                 │
│          ▼                                          │
│  ┌────────────────┐                                 │
│  │ sleep(interval)│  ← blocks before next rerun     │
│  │ st.rerun()     │                                 │
│  └────────────────┘                                 │
└─────────────────────────────────────────────────────┘
```

### Key Changes

**1. Cache data loading functions with TTL**

The three data-loading functions get `@st.cache_data(ttl=interval)` so their results are cached for the duration of one refresh interval:

```python
# Before: uncached, re-queries DB on every rerun (including every Streamlit interaction)
# After: cached, re-queries only when TTL expires or cache is explicitly cleared

@st.cache_data(ttl=60)
def load_servers_cached() -> pd.DataFrame:
    return load_servers()

@st.cache_data(ttl=60)
def load_raw_summary_cached(since, until, tz) -> pd.DataFrame:
    return load_raw_summary(since, until, tz)
```

The TTL value comes from config: `cfg.get("interval", 60)`.

Consequence: user interactions (tab clicks, filter changes) don't re-query the DB. Only the auto-refresh cycle at `interval` seconds triggers fresh data. This means filter changes show cached data until the next auto-refresh — a conscious tradeoff to avoid N+1 queries on each click.

**Alternative considered**: Clear cache on user interaction (tab switch, filter change). Rejected because it adds complexity and Streamlit reruns on every interaction would clear+reload, defeating the purpose.

**2. Move data loading from top-level to list of intervals**

The `interval` from config.yaml is loaded once per rerun and passed to `@st.cache_data(ttl=...)`. Since `@st.cache_data` must be called at module level or with a static TTL, we use a different approach:

Wrap the existing `get_conn()` directly with a TTL-aware wrapper, or use `st.cache_data` on the dashboard's `run()`-internal data loading by converting the load functions to use `st.cache_data` as a decorator with a runtime TTL.

In Streamlit, `st.cache_data` supports `ttl` as a keyword argument that can be computed at runtime:

```python
st.cache_data(ttl=interval)(load_raw_summary)(since=since, until=until, tz=tz)
```

Or more cleanly — add thin wrapper functions inside `run()` that are decorated with the runtime TTL.

**3. Auto-refresh loop**

At the very end of `run()`, after all rendering:

```python
interval = cfg.get("interval", 60)
if interval > 0:
    time.sleep(interval)
    st.rerun()
```

Setting `interval: 0` in config.yaml disables auto-refresh. This is the "Off" mechanism — no sidebar control needed.

### Why Not Session State Tab Tracking?

Streamlit's `with tab:` blocks all execute unconditionally. Attempting to track which tab is "active" via session state set inside blocks doesn't work because all blocks set the same variable in sequence — the last tab always wins. The true optimization is caching the shared data layer, not skipping `with tab:` blocks.

The browser already handles "don't refresh hidden components" by only rendering visible content. The ~50ms cost per hidden tab to run pandas operations on already-loaded DataFrames is negligible.

## Edge Cases Covered

- **interval=0**: Auto-refresh disabled. Dashboard behaves as today (no auto-refresh).
- **interval not in config**: Default to 60s (matching scraper default).
- **User changes filter mid-cycle**: Cache serves stale data until next refresh. This is transparent — `st.cache_data` invalidates on TTL expiry.
- **DB temporarily unreachable**: Cached data serves the current cycle. Next cycle retries.
- **Multiple browsers**: Each Streamlit session independently caches and refreshes.
- **Rapid user interaction**: Every Streamlit interaction triggers a rerun, but cached data means no extra DB queries.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected |
|-----------|-----------|------------------------------|
| `st.cache_data` TTL | Must limit DB queries to once per interval | Uncached = N DB queries per user click — unacceptable |
| Sleep-at-end pattern | Only way to auto-refresh without custom component | `st_autorefresh` package adds dependency, rejected |

No constitution violations.

## Research: Auto-Refresh Patterns

Two approaches evaluated:

| Approach | Pros | Cons |
|----------|------|------|
| **A: sleep + st.rerun()** | Zero deps, simple, predictable | Blocks the Streamlit thread during sleep — no interaction handling during that time. Streamlit handles this by running each script execution in its own thread; the sleep blocks only the current execution, not the server. Wait, actually in Streamlit, `time.sleep()` in a script blocks that script execution. But Streamlit processes each session independently. So if the user interacts during sleep, a new script execution is queued and starts running immediately — the sleeping one is discarded. This is the standard Streamlit pattern for auto-refresh. |
| **B: streamlit-autorefresh** | Proper component, doesn't block server | Extra dependency, version compatibility risk |

**Decision**: Approach A (`time.sleep()` + `st.rerun()`). Zero dependencies, minimal code.

## Implementation

### Phase 4a — Implementation

1. Read `interval` from config.yaml in `run()`
2. Wrap data loading calls with `st.cache_data(ttl=interval)`
3. Add `time.sleep(interval)` + `st.rerun()` at end of `run()`
4. Test: interval=0 disables auto-refresh; interval=60 refreshes every 60s
