from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.execution.bithumb_order_intent import build_bithumb_entry_plan, normalize_bithumb_market


def _write_manual_summary(path: Path) -> None:
    payload = {
        "run_id": "1h:test",
        "candle_close_utc": "2026-04-16T12:00:00Z",
        "manual_brief": {
            "headline": "Actionable BUY candidates exist.",
            "summary": {"buy_count": 1, "hold_count": 1, "no_buy_count": 0},
            "notes": [],
            "watchlist": [
                {
                    "symbol": "BTC",
                    "rank": 1,
                    "action": "BUY",
                    "reference_price_krw": 150000000.0,
                    "suggested_stop_price_krw": 145000000.0,
                    "suggested_take_profit_price_krw": 160000000.0,
                    "risk_reward_ratio": 2.0,
                    "final_decision": "SCHEDULED",
                    "action_reason": "Scheduled by the baseline scanner.",
                },
                {
                    "symbol": "ETH",
                    "rank": 2,
                    "action": "HOLD",
                    "reference_price_krw": 5000000.0,
                    "final_decision": "CANCELED:MAX_CONCURRENT",
                    "action_reason": "Operational capacity blocked entry.",
                },
            ],
        },
        "manual_recommendations": [],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_normalize_bithumb_market() -> None:
    assert normalize_bithumb_market("BTC") == "KRW-BTC"
    assert normalize_bithumb_market("KRW-BTC") == "KRW-BTC"
    assert normalize_bithumb_market("btc_krw") == "KRW-BTC"


def test_build_bithumb_entry_plan_filters_buy_rows() -> None:
    payload = {
        "run_id": "1h:test",
        "candle_close_utc": "2026-04-16T12:00:00Z",
        "summary_path": "logs/hourly_run_test.json",
        "manual_brief": {
            "watchlist": [
                {"symbol": "BTC", "rank": 1, "action": "BUY", "final_decision": "SCHEDULED", "action_reason": "ok"},
                {"symbol": "ETH", "rank": 2, "action": "HOLD", "final_decision": "CANCELED:MAX_CONCURRENT"},
            ]
        },
    }
    plan = build_bithumb_entry_plan(payload, notional_krw=120000.0, max_orders=2, strategy_track="operating")
    assert plan["intent_count"] == 1
    assert plan["order_intents"][0]["market"] == "KRW-BTC"
    assert plan["order_intents"][0]["quote_amount_krw"] == 120000.0
    assert plan["strategy_track"] == "operating"
    assert plan["skipped_watchlist_rows"][0]["reason"] == "non_buy_action"


def test_build_bithumb_entry_plan_prefers_attack_upside_candidates() -> None:
    payload = {
        "run_id": "1h:test",
        "candle_close_utc": "2026-04-16T12:00:00Z",
        "summary_path": "logs/hourly_run_test.json",
        "manual_brief": {
            "watchlist": [
                {
                    "symbol": "BTC",
                    "rank": 2,
                    "action": "BUY",
                    "reference_price_krw": 100.0,
                    "suggested_stop_price_krw": 95.0,
                    "suggested_take_profit_price_krw": 130.0,
                    "risk_reward_ratio": 6.0,
                    "final_decision": "SCHEDULED",
                    "action_reason": "higher upside",
                },
                {
                    "symbol": "ETH",
                    "rank": 1,
                    "action": "BUY",
                    "reference_price_krw": 100.0,
                    "suggested_stop_price_krw": 98.0,
                    "suggested_take_profit_price_krw": 110.0,
                    "risk_reward_ratio": 5.0,
                    "final_decision": "SCHEDULED",
                    "action_reason": "tighter stop",
                },
            ]
        },
    }

    plan = build_bithumb_entry_plan(payload, notional_krw=120000.0, max_orders=1, strategy_track="attack")

    assert plan["intent_count"] == 1
    assert plan["order_intents"][0]["symbol"] == "BTC"
    assert plan["order_intents"][0]["candidate_metrics"]["upside_pct"] == 0.3
    assert plan["order_intents"][0]["track_rationale"].startswith("attack priority:")


def test_build_bithumb_entry_plan_prefers_operating_tighter_stop_candidates() -> None:
    payload = {
        "run_id": "1h:test",
        "candle_close_utc": "2026-04-16T12:00:00Z",
        "summary_path": "logs/hourly_run_test.json",
        "manual_brief": {
            "watchlist": [
                {
                    "symbol": "BTC",
                    "rank": 2,
                    "action": "BUY",
                    "reference_price_krw": 100.0,
                    "suggested_stop_price_krw": 95.0,
                    "suggested_take_profit_price_krw": 130.0,
                    "risk_reward_ratio": 6.0,
                    "final_decision": "SCHEDULED",
                    "action_reason": "higher upside",
                },
                {
                    "symbol": "ETH",
                    "rank": 1,
                    "action": "BUY",
                    "reference_price_krw": 100.0,
                    "suggested_stop_price_krw": 98.0,
                    "suggested_take_profit_price_krw": 110.0,
                    "risk_reward_ratio": 5.0,
                    "final_decision": "SCHEDULED",
                    "action_reason": "tighter stop",
                },
            ]
        },
    }

    plan = build_bithumb_entry_plan(payload, notional_krw=120000.0, max_orders=1, strategy_track="operating")

    assert plan["intent_count"] == 1
    assert plan["order_intents"][0]["symbol"] == "ETH"
    assert plan["order_intents"][0]["candidate_metrics"]["stop_loss_pct"] == 0.02
    assert plan["order_intents"][0]["track_rationale"].startswith("operating priority:")


def test_build_bithumb_execution_plan_script_outputs_json(tmp_path: Path) -> None:
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    summary_path = logs_dir / "hourly_run_test.json"
    _write_manual_summary(summary_path)

    cmd = [
        sys.executable,
        str(Path("scripts/build_bithumb_execution_plan.py")),
        "--logs-dir",
        str(logs_dir),
        "--format",
        "json",
        "--notional-krw",
        "250000",
        "--max-orders",
        "1",
        "--track",
        "attack",
    ]
    result = subprocess.run(cmd, cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout)
    assert payload["intent_count"] == 1
    assert payload["order_intents"][0]["market"] == "KRW-BTC"
    assert payload["order_intents"][0]["quote_amount_krw"] == 250000.0
    assert payload["strategy_track"] == "attack"
