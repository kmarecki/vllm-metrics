"""pytest configuration and fixtures for vllm-metrics tests."""

import os
import sys
import pytest
import sqlite3

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture
def db_conn():
    """Create an in-memory SQLite database with the vllm-metrics schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _create_schema(conn)
    yield conn
    conn.close()


def _create_schema(conn):
    """Create the minimal schema needed for dashboard queries."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            url TEXT NOT NULL,
            notes TEXT DEFAULT '',
            added_at REAL NOT NULL,
            last_seen REAL
        );
        CREATE TABLE IF NOT EXISTS models (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL,
            model_name TEXT NOT NULL,
            first_seen REAL NOT NULL,
            last_seen REAL,
            FOREIGN KEY (server_id) REFERENCES servers(id),
            UNIQUE(server_id, model_name)
        );
        CREATE TABLE IF NOT EXISTS raw_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_id INTEGER NOT NULL,
            model_id INTEGER,
            timestamp REAL NOT NULL,
            timestring TEXT NOT NULL,
            prompt_tokens_total REAL DEFAULT 0,
            generation_tokens_total REAL DEFAULT 0,
            prompt_tokens_cached_total REAL DEFAULT 0,
            request_success_total REAL DEFAULT 0,
            num_preemptions_total REAL DEFAULT 0,
            num_requests_running REAL DEFAULT NULL,
            num_requests_waiting REAL DEFAULT NULL,
            kv_cache_usage_perc REAL DEFAULT NULL,
            ttft_count REAL DEFAULT NULL,
            ttft_sum REAL DEFAULT NULL,
            itl_count REAL DEFAULT NULL,
            itl_sum REAL DEFAULT NULL,
            e2e_count REAL DEFAULT NULL,
            e2e_sum REAL DEFAULT NULL,
            queue_sum REAL DEFAULT NULL,
            queue_count REAL DEFAULT NULL,
            FOREIGN KEY (server_id) REFERENCES servers(id),
            FOREIGN KEY (model_id) REFERENCES models(id)
        );
        CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            server_id INTEGER NOT NULL,
            model_id INTEGER,
            prompt_tokens REAL DEFAULT 0,
            generation_tokens REAL DEFAULT 0,
            prompt_tokens_cached REAL DEFAULT 0,
            completed_requests REAL DEFAULT 0,
            preemptions REAL DEFAULT 0,
            avg_running REAL DEFAULT NULL,
            min_running REAL DEFAULT NULL,
            max_running REAL DEFAULT NULL,
            avg_waiting REAL DEFAULT NULL,
            avg_kv_cache_pct REAL DEFAULT NULL,
            avg_ttft_ms REAL DEFAULT NULL,
            avg_itl_ms REAL DEFAULT NULL,
            avg_e2e_s REAL DEFAULT NULL,
            avg_queue_s REAL DEFAULT NULL,
            num_snapshots INTEGER DEFAULT 0,
            UNIQUE(date, server_id, model_id),
            FOREIGN KEY (server_id) REFERENCES servers(id),
            FOREIGN KEY (model_id) REFERENCES models(id)
        );
    """)
    conn.commit()


def seed_server(conn, name="spark1", url="http://192.168.1.198:8000",
                last_seen=None):
    """Insert a test server and return its id."""
    import time
    now = time.time()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO servers (name, url, notes, added_at, last_seen)"
        " VALUES (?, ?, '', ?, ?)",
        (name, url, now, last_seen or now),
    )
    conn.commit()
    cursor.execute("SELECT id FROM servers WHERE name = ?", (name,))
    return cursor.fetchone()["id"]


def seed_model(conn, server_id, model_name="deepseek-v4-flash"):
    """Insert a test model and return its id."""
    import time
    now = time.time()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO models (server_id, model_name, first_seen, last_seen)"
        " VALUES (?, ?, ?, ?)",
        (server_id, model_name, now, now),
    )
    conn.commit()
    cursor.execute(
        "SELECT id FROM models WHERE server_id = ? AND model_name = ?",
        (server_id, model_name),
    )
    return cursor.fetchone()["id"]


def seed_snapshot(conn, server_id, model_id, timestamp, timestring,
                  running=2, waiting=0, kv_cache=50.0,
                  prompt_delta=500, gen_delta=1000,
                  cached_delta=0, success_delta=5,
                  ttft_sum=0.0, ttft_count=0,
                  itl_sum=0.0, itl_count=0,
                  e2e_sum=0.0, e2e_count=0):
    """Insert a raw_snapshot row for testing."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO raw_snapshots
            (server_id, model_id, timestamp, timestring,
             num_requests_running, num_requests_waiting, kv_cache_usage_perc,
             prompt_tokens_total, generation_tokens_total,
             prompt_tokens_cached_total, request_success_total,
             ttft_sum, ttft_count, itl_sum, itl_count,
             e2e_sum, e2e_count)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (server_id, model_id, timestamp, timestring,
          running, waiting, kv_cache,
          prompt_delta, gen_delta, cached_delta, success_delta,
          ttft_sum, ttft_count, itl_sum, itl_count,
          e2e_sum, e2e_count))
    conn.commit()


def seed_daily_stats(conn, server_id, model_id, date_str,
                     prompt=1000, gen=2000, cached=500,
                     requests=10, preemptions=0,
                     avg_running=2.0, max_running=5.0, avg_waiting=0.5,
                     kv_cache=50.0, ttft_ms=100.0, itl_ms=20.0, e2e_s=5.0,
                     snapshots=24):
    """Insert a daily_stats row for testing."""
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR IGNORE INTO daily_stats
            (date, server_id, model_id,
             prompt_tokens, generation_tokens, prompt_tokens_cached,
             completed_requests, preemptions,
             avg_running, min_running, max_running, avg_waiting,
             avg_kv_cache_pct,
             avg_ttft_ms, avg_itl_ms, avg_e2e_s,
             num_snapshots)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (date_str, server_id, model_id,
          prompt, gen, cached,
          requests, preemptions,
          avg_running, 0.0, max_running, avg_waiting,
          kv_cache,
          ttft_ms, itl_ms, e2e_s,
          snapshots))
    conn.commit()
