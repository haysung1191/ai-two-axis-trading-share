from __future__ import annotations

import sqlite3

import jobs.hourly_job as hj
from src.config import AppConfig


def test_hourly_job_marks_skipped_when_closed_candle_missing(tmp_path, monkeypatch) -> None:
    interval_ms = 3600000
    close_ts_ms = 10 * interval_ms
    run_id = f"1h:{close_ts_ms}"

    db_path = tmp_path / "state.db"
    cfg = AppConfig(
        db_path=str(db_path),
        log_level="INFO",
        config_path="(test)",
        app_env="test",
        exchange={},
        strategy={"interval_ms": interval_ms},
        scanner={},
        email={"enabled": False},
        smtp={},
    )

    class FakeClient:
        def close(self) -> None:
            pass

        def fetch_1h_candles(self, symbol: str):
            # Only the in-progress candle exists; the closed candle at close-interval is missing.
            return [(close_ts_ms, 1.0, 1.0, 1.0, 1.0, 1.0)]

        @staticmethod
        def diagnose_1h_semantics(a, b):
            return {"ok": True, "last_changed": False}

        def list_krw_tickers_by_quote_volume(self, *args, **kwargs):
            raise AssertionError("should not be called when skipping early")

    monkeypatch.setattr(hj, "load_config", lambda: cfg)
    monkeypatch.setattr(hj, "setup_logging", lambda level: None)
    monkeypatch.setattr(hj, "BithumbPublicClient", lambda: FakeClient())
    monkeypatch.setattr(hj, "now_utc_ms", lambda: close_ts_ms + 12345)
    monkeypatch.setattr(hj, "latest_closed_candle_close_ts_ms", lambda now_ms, interval: close_ts_ms)
    monkeypatch.setenv("HOURLY_LOCK_PATH", str(tmp_path / "hourly.lock"))

    rc = hj.main()
    assert rc == 0

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT run_id, status, error FROM runs WHERE run_id=?", (run_id,)).fetchone()
        assert row is not None
        assert row["status"] == "SKIPPED"
        assert "missing_closed_candle" in str(row["error"])

        sig_n = int(conn.execute("SELECT COUNT(*) AS n FROM signals").fetchone()["n"])
        ord_n = int(conn.execute("SELECT COUNT(*) AS n FROM paper_orders").fetchone()["n"])
        assert sig_n == 0
        assert ord_n == 0
    finally:
        conn.close()

