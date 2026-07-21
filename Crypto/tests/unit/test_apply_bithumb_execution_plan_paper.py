from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.execution.paper_execution_ledger import (
    apply_execution_plan_to_paper_ledger,
    load_paper_execution_ledger,
)


def test_apply_execution_plan_to_paper_ledger_opens_position() -> None:
    ledger = load_paper_execution_ledger(Path("C:/nonexistent/ledger.json"))
    updated = apply_execution_plan_to_paper_ledger(
        ledger,
        {
            "run_id": "1h:test",
            "candle_close_utc": "2026-04-16T12:00:00Z",
            "strategy_track": "operating",
            "order_intents": [
                {
                    "symbol": "BTC",
                    "market": "KRW-BTC",
                    "side": "buy",
                    "order_type": "market",
                    "quote_amount_krw": 250000.0,
                    "reference_price_krw": 150000000.0,
                }
            ],
            "standard_check_order_reference": ["practical", "research", "contract", "brief"],
        },
    )
    assert updated["last_apply_summary"]["applied_count"] == 1
    assert updated["orders"][0]["status"] == "FILLED_PAPER"
    assert updated["fills"][0]["fill_mode"] == "reference_price"
    assert updated["positions"][0]["status"] == "OPEN"
    assert updated["positions"][0]["market"] == "KRW-BTC"


def test_apply_execution_plan_to_paper_ledger_rejects_duplicate_open_market() -> None:
    ledger = {
        "positions": [{"market": "KRW-BTC", "status": "OPEN"}],
        "orders": [],
        "fills": [],
        "rejections": [],
    }
    updated = apply_execution_plan_to_paper_ledger(
        ledger,
        {
            "run_id": "1h:test",
            "candle_close_utc": "2026-04-16T12:00:00Z",
            "strategy_track": "operating",
            "order_intents": [{"symbol": "BTC", "market": "KRW-BTC", "quote_amount_krw": 250000.0}],
        },
    )
    assert updated["last_apply_summary"]["applied_count"] == 0
    assert updated["last_apply_summary"]["rejected_count"] == 1
    assert updated["rejections"][0]["reason"] == "existing_open_position"


def test_apply_execution_plan_to_paper_ledger_skips_duplicate_rerun() -> None:
    ledger = load_paper_execution_ledger(Path("C:/nonexistent/ledger.json"))
    plan_payload = {
        "run_id": "1h:test",
        "candle_close_utc": "2026-04-16T12:00:00Z",
        "strategy_track": "operating",
        "order_intents": [
            {
                "symbol": "BTC",
                "market": "KRW-BTC",
                "side": "buy",
                "order_type": "market",
                "quote_amount_krw": 250000.0,
                "reference_price_krw": 150000000.0,
            }
        ],
    }
    first = apply_execution_plan_to_paper_ledger(ledger, plan_payload)
    first["positions"][0]["status"] = "CLOSED"

    updated = apply_execution_plan_to_paper_ledger(first, plan_payload)

    assert updated["last_apply_summary"]["applied_count"] == 0
    assert updated["last_apply_summary"]["rejected_count"] == 0
    assert updated["last_apply_summary"]["duplicate_count"] == 1
    assert len(updated["orders"]) == 1
    assert len(updated["fills"]) == 1
    assert len(updated["positions"]) == 1


def test_load_paper_execution_ledger_normalizes_legacy_duplicate_rows(tmp_path: Path) -> None:
    ledger_path = tmp_path / "legacy_paper_ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "orders": [
                    {"order_id": "paper-order-1h-test-01", "run_id": "1h:test"},
                    {"order_id": "paper-order-1h-test-01", "run_id": "1h:test"},
                ],
                "fills": [
                    {"fill_id": "paper-fill-1h-test-01", "order_id": "paper-order-1h-test-01"},
                    {"fill_id": "paper-fill-1h-test-01", "order_id": "paper-order-1h-test-01"},
                ],
                "positions": [
                    {
                        "position_id": "paper-pos-1h-test-01",
                        "opened_from_order_id": "paper-order-1h-test-01",
                        "status": "OPEN",
                        "market": "KRW-BTC",
                        "symbol": "BTC",
                        "opened_at": "2026-04-16T12:00:00Z",
                    },
                    {
                        "position_id": "paper-pos-1h-test-01",
                        "opened_from_order_id": "paper-order-1h-test-01",
                        "status": "CLOSED",
                        "market": "KRW-BTC",
                        "symbol": "BTC",
                        "opened_at": "2026-04-16T12:00:00Z",
                        "closed_at": "2026-04-16T13:00:00Z",
                        "exit_reason": "TP",
                    },
                ],
                "closed_positions": [
                    {"position_id": "paper-pos-1h-test-01", "exit_run_id": "1h:close"},
                    {"position_id": "paper-pos-1h-test-01", "exit_run_id": "1h:close"},
                ],
                "exit_fills": [
                    {"fill_id": "paper-exit-1h-close-01", "position_id": "paper-pos-1h-test-01"},
                    {"fill_id": "paper-exit-1h-close-01", "position_id": "paper-pos-1h-test-01"},
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    loaded = load_paper_execution_ledger(ledger_path)

    assert len(loaded["orders"]) == 1
    assert len(loaded["fills"]) == 1
    assert len(loaded["positions"]) == 1
    assert len(loaded["closed_positions"]) == 1
    assert len(loaded["exit_fills"]) == 1
    assert loaded["positions"][0]["status"] == "CLOSED"
    assert loaded["positions"][0]["exit_reason"] == "TP"


def test_apply_execution_plan_to_paper_ledger_skips_legacy_duplicate_order_id_without_dedupe_key() -> None:
    ledger = {
        "positions": [
            {
                "position_id": "paper-pos-1h-test-01",
                "opened_from_order_id": "paper-order-1h-test-01",
                "run_id": "1h:test",
                "market": "KRW-BTC",
                "symbol": "BTC",
                "status": "CLOSED",
                "opened_at": "2026-04-16T12:00:00Z",
                "closed_at": "2026-04-16T13:00:00Z",
            }
        ],
        "orders": [
            {
                "order_id": "paper-order-1h-test-01",
                "run_id": "1h:test",
                "market": "KRW-BTC",
                "symbol": "BTC",
                "status": "FILLED_PAPER",
            }
        ],
        "fills": [
            {
                "fill_id": "paper-fill-1h-test-01",
                "order_id": "paper-order-1h-test-01",
                "run_id": "1h:test",
            }
        ],
        "rejections": [],
    }
    updated = apply_execution_plan_to_paper_ledger(
        ledger,
        {
            "run_id": "1h:test",
            "candle_close_utc": "2026-04-16T12:00:00Z",
            "strategy_track": "operating",
            "order_intents": [
                {
                    "symbol": "BTC",
                    "market": "KRW-BTC",
                    "side": "buy",
                    "order_type": "market",
                    "quote_amount_krw": 250000.0,
                    "reference_price_krw": 150000000.0,
                }
            ],
        },
    )

    assert updated["last_apply_summary"]["applied_count"] == 0
    assert updated["last_apply_summary"]["duplicate_count"] == 1
    assert len(updated["orders"]) == 1
    assert len(updated["fills"]) == 1
    assert len(updated["positions"]) == 1


def test_apply_bithumb_execution_plan_paper_script_outputs_json(tmp_path: Path) -> None:
    plan_path = tmp_path / "execution_plan.json"
    ledger_path = tmp_path / "paper_ledger.json"
    plan_path.write_text(
        json.dumps(
            {
                "run_id": "1h:test",
                "candle_close_utc": "2026-04-16T12:00:00Z",
                "strategy_track": "attack",
                "order_intents": [
                    {
                        "symbol": "BTC",
                        "market": "KRW-BTC",
                        "side": "buy",
                        "order_type": "market",
                        "quote_amount_krw": 250000.0,
                        "reference_price_krw": 150000000.0,
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        str(Path("scripts/apply_bithumb_execution_plan_paper.py")),
        "--plan-json",
        str(plan_path),
        "--ledger-json",
        str(ledger_path),
        "--format",
        "json",
    ]
    result = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    assert payload["last_run_id"] == "1h:test"
    assert payload["last_apply_summary"]["applied_count"] == 1
    assert payload["positions"][0]["strategy_track"] == "attack"
    saved = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert saved["positions"][0]["market"] == "KRW-BTC"
