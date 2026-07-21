from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

log = logging.getLogger(__name__)


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, isolation_level=None, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    return conn


def apply_migrations(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT (datetime('now')))"
    )
    cur = conn.execute("SELECT COALESCE(MAX(version), 0) AS v FROM schema_migrations")
    current = int(cur.fetchone()["v"])

    mig_dir = Path("migrations")
    migrations = []
    for p in sorted(mig_dir.glob("*.sql")):
        try:
            v = int(p.name.split("_", 1)[0])
        except Exception:
            continue
        migrations.append((v, p))

    for v, p in migrations:
        if v <= current:
            continue
        sql = p.read_text(encoding="utf-8")
        log.info("applying migration %s (%s)", v, p.as_posix())
        conn.executescript(sql)
        conn.execute("INSERT OR REPLACE INTO schema_migrations(version) VALUES (?)", (v,))


def begin_immediate(conn: sqlite3.Connection) -> None:
    conn.execute("BEGIN IMMEDIATE;")


def commit(conn: sqlite3.Connection) -> None:
    conn.execute("COMMIT;")


def rollback(conn: sqlite3.Connection) -> None:
    conn.execute("ROLLBACK;")
