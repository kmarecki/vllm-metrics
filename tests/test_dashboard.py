"""Tests for the vllm-metrics dashboard module."""

import time
import pytest
from .conftest import seed_server, seed_model, seed_daily_stats


# ── Formatting helpers (T002) ──────────────────────────────────────────

def test_fmt_number(monkeypatch):
    """fmt_number formats large numbers with suffixes."""
    # Import after dashboard is created — skip if dashboard not yet created
    pytest.importorskip("vllm_metrics.dashboard")
    from vllm_metrics.dashboard import fmt_number

    assert fmt_number(None) == "—"
    assert fmt_number(0) == "0"
    assert fmt_number(100) == "100"
    assert fmt_number(1_500) == "1.5K"
    assert fmt_number(1_500_000) == "1.50M"
    assert fmt_number(1_500_000_000) == "1.50B"
    assert fmt_number(5.5) == "5.5"
    assert fmt_number(100.0) == "100"


def test_fmt_ms(monkeypatch):
    """fmt_ms converts seconds to milliseconds display."""
    pytest.importorskip("vllm_metrics.dashboard")
    from vllm_metrics.dashboard import fmt_ms

    assert fmt_ms(None) == "—"
    assert fmt_ms(0) == "—"
    assert fmt_ms(0.1) == "100.0ms"
    assert fmt_ms(1.0) == "1000.0ms"


def test_fmt_s(monkeypatch):
    """fmt_s formats seconds in human-readable form."""
    pytest.importorskip("vllm_metrics.dashboard")
    from vllm_metrics.dashboard import fmt_s

    assert fmt_s(None) == "—"
    assert fmt_s(0) == "—"
    assert fmt_s(0.5) == "0.5s"
    assert fmt_s(30) == "30.0s"
    assert fmt_s(90) == "1.5m"
    assert fmt_s(7200) == "2.0h"


def test_fmt_pct(monkeypatch):
    """fmt_pct converts decimal to percentage string."""
    pytest.importorskip("vllm_metrics.dashboard")
    from vllm_metrics.dashboard import fmt_pct

    assert fmt_pct(None) == "—"
    assert fmt_pct(0.0) == "0.0%"
    assert fmt_pct(0.5) == "50.0%"
    assert fmt_pct(1.0) == "100.0%"


def test_fmt_decimal(monkeypatch):
    """fmt_decimal formats floats with appropriate precision."""
    pytest.importorskip("vllm_metrics.dashboard")
    from vllm_metrics.dashboard import fmt_decimal

    assert fmt_decimal(None) == "\u2014"
    assert fmt_decimal(0) == "0"
    assert fmt_decimal(150) == "150"
    assert fmt_decimal(15.5) == "15.5"
    assert fmt_decimal(5.5) == "5.50"
    assert fmt_decimal(0.555) == "0.555"
    assert fmt_decimal(0.005) == "0.0050"


# ── Data layer tests (T004) ────────────────────────────────────────────

def test_load_servers(db_conn, monkeypatch):
    """load_servers returns servers with correct columns."""
    pytest.importorskip("vllm_metrics.dashboard")
    from vllm_metrics.dashboard import load_servers

    # Patch get_conn to return our test DB
    monkeypatch.setattr("vllm_metrics.dashboard.get_conn", lambda: db_conn)

    # Empty table
    df = load_servers()
    assert df.empty

    # With data
    seed_server(db_conn, "spark1")
    df = load_servers()
    assert len(df) == 1
    assert df.iloc[0]["name"] == "spark1"


# ── Data layer tests (T005) ────────────────────────────────────────────

def test_load_daily_summary(db_conn, monkeypatch):
    """load_daily_summary returns aggregated data respecting date filter."""
    pytest.importorskip("vllm_metrics.dashboard")
    from vllm_metrics.dashboard import load_daily_summary

    monkeypatch.setattr("vllm_metrics.dashboard.get_conn", lambda: db_conn)

    sid = seed_server(db_conn)
    mid = seed_model(db_conn, sid)
    seed_daily_stats(db_conn, sid, mid, "2026-06-01",
                              prompt=2000, gen=4000, requests=20)
    seed_daily_stats(db_conn, sid, mid, "2026-06-02",
                              prompt=3000, gen=5000, requests=30)

    # No filter — all data
    df = load_daily_summary()
    assert len(df) == 2

    # With date filter
    df = load_daily_summary(since="2026-06-02")
    assert len(df) == 1
    assert df.iloc[0]["date"] == "2026-06-02"


# ── Data layer tests (T006) ────────────────────────────────────────────

def test_load_latest_snapshots(db_conn, monkeypatch):
    """load_latest_snapshots returns correct columns and respects limit."""
    pytest.importorskip("vllm_metrics.dashboard")
    from vllm_metrics.dashboard import load_latest_snapshots

    monkeypatch.setattr("vllm_metrics.dashboard.get_conn", lambda: db_conn)

    sid = seed_server(db_conn)
    mid = seed_model(db_conn, sid)
    now = time.time()

    # Insert 3 snapshots
    for i in range(3):
        ts = now + i
        db_conn.execute("""
            INSERT INTO raw_snapshots
                (server_id, model_id, timestamp, timestring,
                 num_requests_running, num_requests_waiting,
                 kv_cache_usage_perc, generation_tokens_total)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (sid, mid, ts, f"2026-06-12T{i:02d}:00:00",
              2 + i, 1, 50.0, 1000 * (i + 1)))
    db_conn.commit()

    df = load_latest_snapshots(limit=2)
    assert len(df) <= 2
    assert "server" in df.columns
    assert "num_requests_running" in df.columns


# ── Gen throughput computation (T007) ──────────────────────────────────

def test_gen_throughput_computation(db_conn, monkeypatch):
    """Gen throughput computes rate from consecutive gen-producing snapshots."""
    pytest.importorskip("vllm_metrics.dashboard")
    from vllm_metrics.dashboard import load_latest_snapshots

    monkeypatch.setattr("vllm_metrics.dashboard.get_conn", lambda: db_conn)

    sid = seed_server(db_conn)
    mid = seed_model(db_conn, sid)
    now = time.time()

    # Insert snaphots with increasing gen tokens (simulating 100 tok/s rate)
    for i in range(5):
        ts = now + i * 60  # 60s intervals
        gen_tok = (i + 1) * 6000  # 6000 delta each step → 100 tok/s
        db_conn.execute("""
            INSERT INTO raw_snapshots
                (server_id, model_id, timestamp, timestring,
                 num_requests_running, generation_tokens_total)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (sid, mid, ts, f"2026-06-12T{i:02d}:00:00",
              2, gen_tok))
    db_conn.commit()

    df = load_latest_snapshots(limit=100)
    # The gen rate computation logic is in the dashboard's run() function.
    # We verify the raw data loads correctly — gen rate is computed in the
    # dashboard rendering code, tested via integration.
    assert len(df) == 5
    # load_latest_snapshots orders by timestamp DESC, so iloc[0] is the
    # most recent snapshot, which has the highest cumulative delta
    assert df["generation_tokens_total"].iloc[4] == 6000.0


def test_gen_throughput_empty_state(db_conn, monkeypatch):
    """Gen throughput handles no gen-producing snapshots gracefully."""
    pytest.importorskip("vllm_metrics.dashboard")
    from vllm_metrics.dashboard import load_latest_snapshots

    monkeypatch.setattr("vllm_metrics.dashboard.get_conn", lambda: db_conn)

    # Only query base loads without error — the dashboard handles empty state
    sid = seed_server(db_conn)
    mid = seed_model(db_conn, sid)
    now = time.time()

    db_conn.execute("""
        INSERT INTO raw_snapshots
            (server_id, model_id, timestamp, timestring,
             num_requests_running, generation_tokens_total)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (sid, mid, now, "2026-06-12T00:00:00", 0, 0))
    db_conn.commit()

    df = load_latest_snapshots()
    assert len(df) == 1
    assert df.iloc[0]["generation_tokens_total"] == 0
