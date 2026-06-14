# Data Model: Dashboard Queries

All dashboard queries read from the existing SQLite database (`~/.vllm-metrics.db`).
No new tables are created — the dashboard is a read-only consumer.

## Tables Used

### `servers`
| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER PK | Lookup key |
| name | TEXT | Display name in sidebar/filter |
| url | TEXT | Display only |
| last_seen | REAL (unix ts) | Online/offline detection |

### `models`
| Column | Type | Purpose |
|--------|------|---------|
| id | INTEGER PK | Lookup key |
| server_id | INTEGER FK → servers | Scoping |
| model_name | TEXT | Per-model breakdown |

### `daily_stats`
| Column | Type | Purpose |
|--------|------|---------|
| date | TEXT (YYYY-MM-DD) | X-axis for time-series charts |
| server_id, model_id | INTEGER FK | Scoping |
| prompt_tokens, generation_tokens, prompt_tokens_cached | REAL | Token volume bars |
| completed_requests, preemptions | REAL | Request counts |
| avg_running, max_running, avg_waiting | REAL | Concurrency charts |
| avg_kv_cache_pct | REAL | KV cache area chart |
| avg_ttft_ms, avg_itl_ms, avg_e2e_s, avg_queue_s | REAL | Latency charts |

### `raw_snapshots`
| Column | Type | Purpose |
|--------|------|---------|
| timestamp | REAL (unix ts) | X-axis for per-snapshot charts |
| server_id, model_id | INTEGER FK | Scoping |
| num_requests_running, num_requests_waiting | REAL | Latest snapshot display |
| kv_cache_usage_perc | REAL | Latest display |
| generation_tokens_total | REAL | Throughput rate computation |

## Key Queries

### Q1: Daily aggregated data (from raw_snapshots, primary source)

The dashboard queries `raw_snapshots` first with timezone-shifted date aggregation.
If `raw_snapshots` is empty, falls back to `daily_stats`.

```sql
SELECT DATE(r.timestring, '+{offset_s} seconds') AS date,
       s.name AS server, m.model_name AS model,
       SUM(r.prompt_tokens_total)        AS prompt_tokens,
       SUM(r.generation_tokens_total)    AS generation_tokens,
       SUM(r.prompt_tokens_cached_total) AS prompt_tokens_cached,
       SUM(r.request_success_total)      AS completed_requests,
       SUM(r.num_preemptions_total)      AS preemptions,
       AVG(r.num_requests_running)       AS avg_running,
       MAX(r.num_requests_running)       AS max_running,
       AVG(r.num_requests_waiting)       AS avg_waiting,
       AVG(r.kv_cache_usage_perc)        AS avg_kv_cache_pct,
       AVG(r.ttft_sum / NULLIF(r.ttft_count, 0)) * 1000 AS avg_ttft_ms,
       AVG(r.itl_sum / NULLIF(r.itl_count, 0)) * 1000   AS avg_itl_ms,
       AVG(r.e2e_sum / NULLIF(r.e2e_count, 0))          AS avg_e2e_s,
       AVG(r.queue_sum / NULLIF(r.queue_count, 0))      AS avg_queue_s,
       COUNT(*)                                          AS num_snapshots
FROM raw_snapshots r
JOIN servers s ON r.server_id = s.id
LEFT JOIN models m ON r.model_id = m.id
[WHERE r.timestamp >= :since_ts AND r.timestamp < :until_ts]
GROUP BY DATE(r.timestring, '+{offset_s} seconds'), s.name, m.model_name
HAVING m.model_name IS NOT NULL
ORDER BY date, s.name, m.model_name
```

**Timezone shift**: `offset_s` converts UTC dates to local dates (e.g., +7200 for CEST).
The WHERE clause uses Unix timestamps (`r.timestamp`) for correct local-day boundaries.

### Q2: Global totals (FR-002)

```sql
SELECT SUM(prompt_tokens), SUM(generation_tokens),
       SUM(prompt_tokens_cached), SUM(completed_requests)
FROM daily_stats d
JOIN servers s ON d.server_id = s.id
[WHERE s.name = :server]
```

### Q3: Token volume over time (FR-003)
```sql
SELECT date, SUM(prompt_tokens), SUM(generation_tokens),
       SUM(prompt_tokens_cached)
FROM daily_stats d JOIN servers s ON d.server_id = s.id
[WHERE s.name = :server]
GROUP BY date ORDER BY date
```

### Q4: Generation throughput (FR-004, from raw_snapshots)
Computed in Python: for each (server, model) group, walk consecutive snapshots
where `generation_tokens_total` > 0, compute rate = delta / dt, filter to
sane range (0.1–10000 tok/s). X-axis timestamps converted to local timezone
for display.

### Q5: Concurrency over time (FR-005)
```sql
SELECT date, AVG(avg_running), AVG(avg_waiting), MAX(max_running)
FROM daily_stats d JOIN servers s ON d.server_id = s.id
[WHERE s.name = :server]
GROUP BY date ORDER BY date
```

### Q6: Latency metrics (FR-007)
```sql
SELECT date, AVG(avg_ttft_ms), AVG(avg_itl_ms), AVG(avg_e2e_s)
FROM daily_stats d JOIN servers s ON d.server_id = s.id
[WHERE s.name = :server]
GROUP BY date ORDER BY date
```

### Q7: Server status (FR-010)
```sql
SELECT name, last_seen FROM servers ORDER BY name
```
Offline if `last_seen` is NULL or `(now - last_seen) > 300` seconds.

### Q8: Per-model breakdown (FR-008)
```sql
SELECT s.name AS server, m.model_name AS model,
       SUM(prompt_tokens), SUM(generation_tokens),
       SUM(completed_requests), SUM(preemptions),
       AVG(avg_ttft_ms), AVG(avg_itl_ms)
FROM daily_stats d
JOIN servers s ON d.server_id = s.id
LEFT JOIN models m ON d.model_id = m.id
[WHERE s.name = :server]
GROUP BY s.name, m.model_name
```

## Data Flow

```
SQLite DB ← query ← dashboard.py ← streamlit run
                           ↑
                    config.yaml (db path)
                    config.yaml timezone (for local date boundaries)
```

Dashboard connects to the same `~/.vllm-metrics.db` that the daemon writes to.
No write operations — all queries are SELECT.

**Query strategy**: Dashboard mirrors the report command — queries `raw_snapshots`
first (with timezone-shifted GROUP BY), falls back to `daily_stats` if empty.
The gen throughput chart loads all snapshots in the selected date range (no LIMIT)
to allow panning across the full period. Per-snapshot timestamps are converted
from UTC to the configured local timezone for display.
