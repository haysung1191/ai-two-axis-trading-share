from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.execution.paper_execution_ledger import apply_exit_snapshot_to_paper_ledger


def _open_ledger() -> dict:
    return {
        "positions": [
            {
                "position_id": "paper-pos-1",
                "opened_from_order_id": "paper-order-1",
                "run_id": "1h:open",
                "venue": "bithumb",
                "market": "KRW-BTC",
                "symbol": "BTC",
                "status": "OPEN",
                "strategy_track": "operating",
                "entry_price_krw": 150000000.0,
                "quote_amount_krw": 250000.0,
                "qty": 250000.0 / 150000000.0,
                "suggested_stop_price_krw": 145000000.0,
                "suggested_take_profit_price_krw": 160000000.0,
                "time_exit_utc": None,
                "opened_at": "2026-04-16T12:00:00Z",
            }
        ],
        "closed_positions": [],
        "exit_fills": [],
        "orders": [],
        "fills": [],
        "rejections": [],
    }


def test_apply_exit_snapshot_to_paper_ledger_closes_on_take_profit() -> None:
    updated = apply_exit_snapshot_to_paper_ledger(
        _open_ledger(),
        {
            "run_id": "1h:close",
            "candle_close_utc": "2026-04-16T13:00:00Z",
            "market_ohlc": {
                "KRW-BTC": {"open": 151000000.0, "high": 161000000.0, "low": 149000000.0, "close": 160500000.0}
            },
            "standard_check_order_reference": ["practical", "research", "contract", "brief"],
        },
    )
    assert updated["positions"][0]["status"] == "CLOSED"
    assert updated["positions"][0]["exit_reason"] == "TP"
    assert updated["last_exit_summary"]["closed_count"] == 1
    assert updated["last_exit_summary"]["candle_close_utc"] == "2026-04-16T13:00:00Z"
    assert updated["closed_positions"][0]["exit_price_krw"] == 160000000.0


def test_apply_exit_snapshot_to_paper_ledger_closes_on_time_exit() -> None:
    ledger = _open_ledger()
    ledger["positions"][0]["time_exit_utc"] = "2026-04-16T13:00:00Z"
    updated = apply_exit_snapshot_to_paper_ledger(
        ledger,
        {
            "run_id": "1h:close",
            "candle_close_utc": "2026-04-16T13:00:00Z",
            "market_ohlc": {
                "KRW-BTC": {"open": 151000000.0, "high": 152000000.0, "low": 149500000.0, "close": 151500000.0}
            },
        },
    )
    assert updated["positions"][0]["status"] == "CLOSED"
    assert updated["positions"][0]["exit_reason"] == "TIME"
    assert updated["closed_positions"][0]["exit_price_krw"] == 151500000.0


def test_apply_exit_snapshot_to_paper_ledger_skips_same_candle_entry() -> None:
    updated = apply_exit_snapshot_to_paper_ledger(
        _open_ledger(),
        {
            "run_id": "1h:close",
            "candle_close_utc": "2026-04-16T12:00:00Z",
            "market_ohlc": {
                "KRW-BTC": {"open": 151000000.0, "high": 161000000.0, "low": 149000000.0, "close": 160500000.0}
            },
        },
    )
    assert updated["positions"][0]["status"] == "OPEN"
    assert updated["last_exit_summary"]["closed_count"] == 0
    assert updated["last_exit_summary"]["open_count"] == 1
    assert updated["closed_positions"] == []
    assert updated["exit_fills"] == []


def test_apply_exit_snapshot_to_paper_ledger_is_idempotent_on_same_run() -> None:
    payload = {
        "run_id": "1h:close",
        "candle_close_utc": "2026-04-16T13:00:00Z",
        "market_ohlc": {
            "KRW-BTC": {"open": 151000000.0, "high": 161000000.0, "low": 149000000.0, "close": 160500000.0}
        },
    }
    first = apply_exit_snapshot_to_paper_ledger(_open_ledger(), payload)
    second = apply_exit_snapshot_to_paper_ledger(first, payload)

    assert second["last_exit_summary"]["closed_count"] == 0
    assert second["last_exit_summary"]["candle_close_utc"] == "2026-04-16T13:00:00Z"
    assert second["last_exit_summary"]["open_count"] == 0
    assert second["last_exit_summary"]["duplicate_run"] is True
    assert len(second["closed_positions"]) == 1
    assert len(second["exit_fills"]) == 1


def test_apply_bithumb_exit_snapshot_paper_script_outputs_json(tmp_path: Path) -> None:
    ledger_path = tmp_path / "paper_ledger.json"
    exit_path = tmp_path / "exit_snapshot.json"
    ledger_path.write_text(json.dumps(_open_ledger(), ensure_ascii=False, indent=2), encoding="utf-8")
    exit_path.write_text(
        json.dumps(
            {
                "run_id": "1h:close",
                "candle_close_utc": "2026-04-16T13:00:00Z",
                "market_ohlc": {
                    "KRW-BTC": {
                        "open": 151000000.0,
                        "high": 161000000.0,
                        "low": 149000000.0,
                        "close": 160500000.0,
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        str(Path("scripts/apply_bithumb_exit_snapshot_paper.py")),
        "--exit-json",
        str(exit_path),
        "--ledger-json",
        str(ledger_path),
        "--format",
        "json",
    ]
    result = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    assert payload["last_exit_summary"]["closed_count"] == 1
    assert payload["closed_positions"][0]["exit_reason"] == "TP"
    saved = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert saved["positions"][0]["status"] == "CLOSED"


def test_apply_bithumb_exit_snapshot_paper_script_accepts_utf8_bom(tmp_path: Path) -> None:
    ledger_path = tmp_path / "paper_ledger.json"
    exit_path = tmp_path / "exit_snapshot_bom.json"
    ledger_path.write_text(json.dumps(_open_ledger(), ensure_ascii=False, indent=2), encoding="utf-8")
    exit_path.write_text(
        json.dumps(
            {
                "run_id": "1h:close",
                "candle_close_utc": "2026-04-16T13:00:00Z",
                "market_ohlc": {
                    "KRW-BTC": {
                        "open": 151000000.0,
                        "high": 161000000.0,
                        "low": 149000000.0,
                        "close": 160500000.0,
                    }
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8-sig",
    )

    cmd = [
        sys.executable,
        str(Path("scripts/apply_bithumb_exit_snapshot_paper.py")),
        "--exit-json",
        str(exit_path),
        "--ledger-json",
        str(ledger_path),
        "--format",
        "json",
    ]
    result = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    assert payload["last_exit_summary"]["closed_count"] == 1
