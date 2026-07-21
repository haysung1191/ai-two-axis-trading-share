from __future__ import annotations

from src.manual.watchlist import build_manual_watchlist


def test_manual_watchlist_splits_buy_and_monitor_candidates() -> None:
    payload = build_manual_watchlist(
        daily_summary={
            "generated_at": "2026-03-22T12:00:00Z",
            "strategy_snapshot": {"strategy_id": "mean_rev_approved"},
            "policy_snapshot": {"bundle_id": "policy_1"},
            "warnings": ["Policy bundle valid_until is in the past."],
        },
        recommendations=[
            {
                "symbol": "BTC",
                "action": "BUY",
                "rank": 1,
                "policy_materiality": "entry_reversal",
                "reference_price_krw": 100.0,
                "suggested_stop_price_krw": 95.0,
                "suggested_take_profit_price_krw": 110.0,
                "risk_reward_ratio": 2.0,
                "action_reason": "Policy uplift moved this candidate inside the active entry cutoff.",
            },
            {
                "symbol": "ETH",
                "action": "HOLD",
                "rank": 2,
                "policy_materiality": "near_miss",
                "final_decision": "CANCELED:MAX_CONCURRENT",
                "action_reason": "Boosted candidate remained a near miss after policy but capacity timing blocked entry.",
            },
        ],
    )

    assert "actionable BUY candidate" in payload["headline"]
    assert payload["buy_candidates"][0]["symbol"] == "BTC"
    assert payload["monitor_candidates"][0]["symbol"] == "ETH"
    assert "Policy bundle valid_until is in the past." in payload["warnings"]


def test_manual_watchlist_handles_no_actionable_candidates() -> None:
    payload = build_manual_watchlist(
        daily_summary={
            "generated_at": "2026-03-22T12:00:00Z",
            "strategy_snapshot": {"strategy_id": "mean_rev_approved"},
            "policy_snapshot": {"bundle_id": "policy_1"},
            "warnings": [],
        },
        recommendations=[
            {
                "symbol": "XRP",
                "action": "NO_BUY",
                "rank": 1,
                "policy_materiality": "none",
                "final_decision": "CANCELED:MARKET_DOWNTREND",
                "action_reason": "Market regime filter blocked new long exposure.",
            }
        ],
    )

    assert "No actionable watchlist candidates" in payload["headline"]
    assert payload["buy_candidates"] == []
    assert payload["monitor_candidates"] == []


def test_manual_watchlist_warns_when_buy_candidate_lacks_trade_levels() -> None:
    payload = build_manual_watchlist(
        daily_summary={
            "generated_at": "2026-03-22T12:00:00Z",
            "strategy_snapshot": {"strategy_id": "mean_rev_approved"},
            "policy_snapshot": {"bundle_id": "policy_1"},
            "warnings": [],
        },
        recommendations=[
            {
                "symbol": "BTC",
                "action": "BUY",
                "rank": 1,
                "policy_materiality": "none",
                "reference_price_krw": None,
                "suggested_stop_price_krw": None,
                "suggested_take_profit_price_krw": None,
                "risk_reward_ratio": None,
                "action_reason": "Scheduled by the baseline scanner.",
            }
        ],
    )

    assert any("BTC: manual BUY candidate is missing" in warning for warning in payload["warnings"])


def test_manual_watchlist_does_not_duplicate_buy_candidate_in_monitor_list() -> None:
    payload = build_manual_watchlist(
        daily_summary={
            "generated_at": "2026-03-22T12:00:00Z",
            "strategy_snapshot": {"strategy_id": "mean_rev_approved"},
            "policy_snapshot": {"bundle_id": "policy_1"},
            "warnings": [],
        },
        recommendations=[
            {
                "symbol": "BTC",
                "action": "BUY",
                "rank": 1,
                "policy_materiality": "boosted_but_not_decisive",
                "reference_price_krw": 100.0,
                "suggested_stop_price_krw": 95.0,
                "suggested_take_profit_price_krw": 110.0,
                "risk_reward_ratio": 2.0,
                "action_reason": "Scheduled normally and reinforced by a positive policy boost.",
            }
        ],
    )

    assert payload["buy_candidates"][0]["symbol"] == "BTC"
    assert payload["monitor_candidates"] == []
