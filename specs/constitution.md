# vLLM Metrics Constitution

## Core Principles

### Data Persistence

Raw metric data MUST be preserved indefinitely. No automatic pruning of raw_snapshots.
Users explicitly opt-in to data reduction via the `prune` command.

### Meaningful Statistics

All aggregated metrics MUST exclude idle gaps. Concurrency averages compute over
active-only snapshots (num_requests_running > 0). Generation throughput MUST use
consecutive gen-producing snapshots, never time-window fallback.

### Transparency

Every reported metric MUST be traceable to its source. Server stats show "unavailable"
when last_seen is stale (>5min). Calculations MUST be documented inline.

### Minimal Dependencies

Core functionality (scrape, daemon) MUST work with stdlib + PyYAML. Optional features
(dashboard, visualization) MAY add dependencies but must fail gracefully when absent.

### Observability

The daemon MUST log every scrape cycle outcome (pass/fail/recovery). Error output
goes to stderr. Failed servers are silenced after first report until recovery.

## Governance

### Scope

This constitution governs all code in the vllm-metrics repository. Feature specifications
inherit these principles and MUST NOT contradict them.

### Amendments

Constitution amendments require an updated version number and a brief rationale.
Minor clarifications (patch version bump) are editorial. New principles (minor bump)
or incompatible changes (major bump) require user confirmation.

### Enforcement by Feature Skills

Phase skills BLOCK when their prerequisites are unmet. The `spec-kit-plan` skill
MUST verify that the plan aligns with this constitution's principles before
allowing implementation. The `spec-kit-summarize` skill MAY flag deviations from
constitution principles during close evaluation.

Version: 0.1.0 | Ratified: 2026-06-12 | Last Amended: 2026-06-12
