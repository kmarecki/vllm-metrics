# Quickstart: vLLM Dashboard Validation

## Install
```bash
pip install streamlit plotly
```

## Launch
```bash
./vllm-metrics dashboard
```
Opens a browser tab at `http://localhost:8501` (or next available port).

## Validation Scenarios

### Smoke test
1. Run `./vllm-metrics dashboard`
2. Verify the app starts without errors and a browser window opens
3. Verify all tabs render (Token Trends, Latency & Concurrency, Per-Model, Server Stats)

### Empty DB test
1. Point to a fresh/empty database
2. Verify dashboard shows "No daily stats data yet" message, not a crash

### Server filter test
1. With data from ≥2 servers, switch between "All" and individual servers
2. Verify charts update to show only the selected server's data

### Offline server test
1. Stop a vLLM server or wait 5+ minutes since last scrape
2. Verify the sidebar shows it as offline (red dot)

## Expected Metrics Match
Compare dashboard values against the `./vllm-metrics report` command output for the
same date range — token counts, latency averages, and concurrency should align.
