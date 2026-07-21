from __future__ import annotations

from src.manual.briefing import build_hourly_manual_brief


def test_hourly_manual_brief_counts_and_headline() -> None:
    brief = build_hourly_manual_brief(
        run_id="1h:1",
        candle_close_utc="2026-03-22T10:00:00+00:00",
        signals=[
            {
                "symbol": "BTC",
                "rank": 1,
                "action": "BUY",
                "policy_materiality": "entry_reversal",
                "scheduled_due_to_policy": True,
                "near_miss_after_policy": False,
                "reference_price_krw": 100.0,
                "suggested_stop_price_krw": 95.0,
                "suggested_take_profit_price_krw": 110.0,
                "final_decision": "SCHEDULED",
                "action_reason": "Policy uplift moved this candidate inside the active entry cutoff.",
            },
            {
                "symbol": "ETH",
                "rank": 2,
                "action": "HOLD",
                "policy_materiality": "near_miss",
                "scheduled_due_to_policy": False,
                "near_miss_after_policy": True,
                "blocked_reason": "MAX_CONCURRENT",
                "reference_price_krw": 200.0,
                "suggested_stop_price_krw": 190.0,
                "suggested_take_profit_price_krw": 220.0,
                "final_decision": "CANCELED:MAX_CONCURRENT",
                "action_reason": "Boosted candidate remained a near miss after policy but capacity timing blocked entry.",
            },
        ],
    )

    assert brief["summary"]["buy_count"] == 1
    assert brief["summary"]["hold_count"] == 1
    assert brief["summary"]["scheduled_due_to_policy_count"] == 1
    assert brief["summary"]["near_miss_after_policy_count"] == 1
    assert "Policy created at least one actionable entry reversal" in brief["headline"]
    assert brief["watchlist"][0]["symbol"] == "BTC"


def test_hourly_manual_brief_reports_guardrail_dominated_run() -> None:
    brief = build_hourly_manual_brief(
        run_id="1h:2",
        candle_close_utc="2026-03-22T11:00:00+00:00",
        signals=[
            {
                "symbol": "XRP",
                "rank": 1,
                "action": "NO_BUY",
                "policy_materiality": "none",
                "scheduled_due_to_policy": False,
                "near_miss_after_policy": False,
                "blocked_reason": "MARKET_DOWNTREND",
                "final_decision": "CANCELED:MARKET_DOWNTREND",
                "action_reason": "Market regime filter blocked new long exposure.",
            }
        ],
    )

    assert brief["summary"]["no_buy_count"] == 1
    assert brief["summary"]["scheduled_due_to_policy_count"] == 0
    assert "No actionable BUY candidates" in brief["headline"]
    assert any("MARKET_DOWNTREND" in note for note in brief["notes"])
