from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from scripts.manual_trade_brief import load_manual_brief, render_text_brief


def _write_summary(path: Path) -> None:
    payload = {
        "run_id": "1h:123",
        "candle_close_utc": "2026-03-22T12:00:00+00:00",
        "manual_brief": {
            "headline": "Policy created at least one actionable entry reversal in this run.",
            "summary": {
                "buy_count": 1,
                "hold_count": 1,
                "no_buy_count": 0,
                "scheduled_due_to_policy_count": 1,
                "near_miss_after_policy_count": 1,
            },
            "notes": [
                "Primary blockers: MAX_CONCURRENT x1",
                "Policy changed admission for at least one scheduled candidate.",
            ],
            "watchlist": [
                {
                    "symbol": "BTC",
                    "rank": 1,
                    "action": "BUY",
                    "reference_price_krw": 100.0,
                    "suggested_stop_price_krw": 95.0,
                    "suggested_take_profit_price_krw": 110.0,
                    "risk_reward_ratio": 2.0,
                    "final_decision": "SCHEDULED",
                    "action_reason": "Policy uplift moved this candidate inside the active entry cutoff.",
                }
            ],
        },
        "manual_recommendations": [],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_load_manual_brief_uses_latest_file(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    older = logs_dir / "hourly_run_1h_1.json"
    newer = logs_dir / "hourly_run_1h_2.json"
    _write_summary(older)
    _write_summary(newer)
    os.utime(older, (1, 1))
    os.utime(newer, (2, 2))

    payload = load_manual_brief(logs_dir)

    assert payload["run_id"] == "1h:123"
    assert payload["summary_path"].endswith("hourly_run_1h_2.json")
    assert payload["source_metadata"]["source_kind"] == "hourly_run"


def test_load_manual_brief_accepts_utf8_bom_summary(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    path = logs_dir / "hourly_run_bom.json"
    payload = {
        "run_id": "1h:bom",
        "candle_close_utc": "2026-03-22T12:00:00+00:00",
        "manual_brief": {
            "headline": "BOM-safe payload.",
            "summary": {"buy_count": 1, "hold_count": 0, "no_buy_count": 0},
            "notes": [],
            "watchlist": [],
        },
        "manual_recommendations": [],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8-sig")

    loaded = load_manual_brief(logs_dir)

    assert loaded["run_id"] == "1h:bom"
    assert loaded["source_metadata"]["source_kind"] == "hourly_run"


def test_render_text_brief_contains_watchlist() -> None:
    payload = {
        "summary_path": "logs/hourly_run_1h_123.json",
        "run_id": "1h:123",
        "candle_close_utc": "2026-03-22T12:00:00+00:00",
        "manual_brief": {
            "headline": "Policy created at least one actionable entry reversal in this run.",
            "summary": {
                "buy_count": 1,
                "hold_count": 0,
                "no_buy_count": 0,
                "scheduled_due_to_policy_count": 1,
                "near_miss_after_policy_count": 0,
            },
            "notes": ["Policy changed admission for at least one scheduled candidate."],
            "watchlist": [
                {
                    "symbol": "BTC",
                    "rank": 1,
                    "action": "BUY",
                    "reference_price_krw": 100.0,
                    "suggested_stop_price_krw": 95.0,
                    "suggested_take_profit_price_krw": 110.0,
                    "risk_reward_ratio": 2.0,
                    "final_decision": "SCHEDULED",
                    "action_reason": "Policy uplift moved this candidate inside the active entry cutoff.",
                }
            ],
        },
        "manual_recommendations": [],
    }

    rendered = render_text_brief(payload)

    assert "headline: Policy created at least one actionable entry reversal in this run." in rendered
    assert "BTC | action=BUY | rank=1" in rendered
    assert "note: Policy uplift moved this candidate inside the active entry cutoff." in rendered


def test_load_manual_brief_falls_back_to_legacy_signals(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    legacy = logs_dir / "hourly_run_1h_legacy.json"
    legacy.write_text(
        json.dumps(
            {
                "run_id": "1h:legacy",
                "candle_close_utc": "2026-03-22T13:00:00+00:00",
                "signals": [
                    {
                        "symbol": "BTC",
                        "rank": 1,
                        "blocked_reason": None,
                        "scheduled_due_to_policy": False,
                        "near_miss_after_policy": False,
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    payload = load_manual_brief(logs_dir)

    assert payload["manual_brief"]["summary"]["buy_count"] == 1
    assert payload["manual_recommendations"][0]["action"] == "BUY"
    assert payload["source_metadata"]["source_kind"] == "legacy_signals"


def test_load_manual_brief_enriches_legacy_signals_from_state_db(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    legacy = logs_dir / "hourly_run_1h_legacy.json"
    legacy.write_text(
        json.dumps(
            {
                "run_id": "1h:legacy",
                "candle_close_utc": "2026-03-22T13:00:00+00:00",
                "signals": [
                    {
                        "symbol": "BTC",
                        "rank": 1,
                        "blocked_reason": None,
                        "scheduled_due_to_policy": False,
                        "near_miss_after_policy": False,
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    conn = sqlite3.connect(str(tmp_path / "state.db"))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE signals (
            id INTEGER PRIMARY KEY,
            run_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            score REAL NOT NULL,
            rank INTEGER NOT NULL,
            signal_close_ts_ms INTEGER NOT NULL,
            features_json TEXT NOT NULL,
            suggested_stop_dist REAL NOT NULL,
            suggested_tp_dist REAL NOT NULL,
            suggested_time_exit_ts_ms INTEGER NOT NULL,
            blocked_reason TEXT
        )
        """
    )
    cur.execute(
        """
        INSERT INTO signals (
            run_id, symbol, score, rank, signal_close_ts_ms, features_json,
            suggested_stop_dist, suggested_tp_dist, suggested_time_exit_ts_ms, blocked_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "1h:legacy",
            "BTC",
            1.1,
            1,
            1770000000000,
            json.dumps({"close": 100000.0}),
            5000.0,
            10000.0,
            1770003600000,
            None,
        ),
    )
    conn.commit()
    conn.close()

    payload = load_manual_brief(logs_dir)
    row = payload["manual_recommendations"][0]

    assert row["reference_price_krw"] == 100000.0
    assert row["suggested_stop_price_krw"] == 95000.0
    assert row["suggested_take_profit_price_krw"] == 110000.0
    assert row["risk_reward_ratio"] == 2.0
    assert row["time_exit_utc"] == "2026-02-02T03:40:00Z"


def test_load_manual_brief_falls_back_to_latest_symbol_snapshot(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    legacy = logs_dir / "hourly_run_1h_legacy.json"
    legacy.write_text(
        json.dumps(
            {
                "run_id": "1h:legacy",
                "candle_close_utc": "2026-03-22T13:00:00+00:00",
                "signals": [
                    {
                        "symbol": "BTC",
                        "rank": 1,
                        "blocked_reason": None,
                        "scheduled_due_to_policy": False,
                        "near_miss_after_policy": False,
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    conn = sqlite3.connect(str(tmp_path / "state.db"))
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE signals (
            id INTEGER PRIMARY KEY,
            run_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            score REAL NOT NULL,
            rank INTEGER NOT NULL,
            signal_close_ts_ms INTEGER NOT NULL,
            features_json TEXT NOT NULL,
            suggested_stop_dist REAL NOT NULL,
            suggested_tp_dist REAL NOT NULL,
            suggested_time_exit_ts_ms INTEGER NOT NULL,
            blocked_reason TEXT
        )
        """
    )
    cur.execute(
        """
        INSERT INTO signals (
            run_id, symbol, score, rank, signal_close_ts_ms, features_json,
            suggested_stop_dist, suggested_tp_dist, suggested_time_exit_ts_ms, blocked_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "1h:other",
            "BTC",
            1.2,
            2,
            1770007200000,
            json.dumps({"close": 120000.0}),
            6000.0,
            18000.0,
            1770010800000,
            None,
        ),
    )
    conn.commit()
    conn.close()

    payload = load_manual_brief(logs_dir)
    row = payload["manual_recommendations"][0]

    assert row["reference_price_krw"] is None
    assert row["suggested_stop_price_krw"] is None
    assert row["suggested_take_profit_price_krw"] is None
    assert row["risk_reward_ratio"] is None


def test_load_manual_brief_prefers_newest_candle_close_over_mtime(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    older_candle = logs_dir / "hourly_run_1h_oldtouch.json"
    newer_candle = logs_dir / "hourly_run_1h_newcandle.json"
    older_candle.write_text(
        json.dumps(
            {
                "run_id": "1h:oldtouch",
                "candle_close_utc": "1970-01-01T10:00:00+00:00",
                "signals": [{"symbol": "BTC", "rank": 1, "blocked_reason": None}],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    newer_candle.write_text(
        json.dumps(
            {
                "run_id": "1h:newcandle",
                "candle_close_utc": "2026-03-22T12:00:00+00:00",
                "signals": [{"symbol": "ETH", "rank": 1, "blocked_reason": None}],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    os.utime(older_candle, (10, 10))
    os.utime(newer_candle, (1, 1))

    payload = load_manual_brief(logs_dir)

    assert payload["run_id"] == "1h:newcandle"


def test_load_manual_brief_prefers_manual_snapshot_for_same_run_id(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    manual_snapshot = logs_dir / "manual_snapshot_1h_123.json"
    hourly_run = logs_dir / "hourly_run_1h_123.json"
    _write_summary(hourly_run)
    _write_summary(manual_snapshot)

    payload = load_manual_brief(logs_dir, run_id="1h:123")

    assert payload["summary_path"].endswith("manual_snapshot_1h_123.json")
    assert payload["source_metadata"]["source_kind"] == "manual_snapshot"
