from __future__ import annotations

from src.manual.operator_watchlist import build_operator_watchlist


def test_build_operator_watchlist_splits_baseline_and_policy_assisted() -> None:
    payload = build_operator_watchlist(
        daily_summary={
            "generated_at": "2026-03-22T16:00:00Z",
            "strategy_snapshot": {"strategy_id": "mean_rev_approved"},
            "policy_snapshot": {"bundle_id": "policy_1"},
            "warnings": [],
            "snapshot_metadata": {
                "market_filter": {"below_ema": True},
                "counterfactual_buys_without_market_filter": [
                    {"symbol": "H", "final_rank": 1, "final_ranking_score": 6.0, "policy_materiality": "none", "policy_decision": "NEUTRAL"},
                    {"symbol": "SIGN", "final_rank": 5, "final_ranking_score": 3.4, "policy_materiality": "boosted_but_not_decisive", "policy_decision": "BOOST"},
                ],
            },
        },
        recommendations=[
            {"symbol": "H", "policy_score_delta": 0.0},
            {"symbol": "SIGN", "policy_score_delta": 0.05},
        ],
    )

    assert payload["market_filter_active"] is True
    assert payload["baseline_priority"][0]["symbol"] == "H"
    assert payload["policy_assisted"][0]["symbol"] == "SIGN"
    assert payload["recheck_on_filter_release"][0]["symbol"] == "H"
    assert payload["recheck_on_filter_release"][1]["symbol"] == "SIGN"


def test_build_operator_watchlist_uses_current_recommendations_when_filter_inactive() -> None:
    payload = build_operator_watchlist(
        daily_summary={
            "generated_at": "2026-03-22T16:00:00Z",
            "strategy_snapshot": {"strategy_id": "mean_rev_approved"},
            "policy_snapshot": {"bundle_id": "policy_1"},
            "warnings": [],
            "snapshot_metadata": {
                "market_filter": {"below_ema": False},
                "counterfactual_buys_without_market_filter": [],
            },
        },
        recommendations=[
            {
                "symbol": "ADA",
                "action": "BUY",
                "final_rank": 1,
                "final_ranking_score": 5.5,
                "policy_materiality": "boosted_but_not_decisive",
                "policy_decision": "BOOST",
                "policy_score_delta": 0.05,
                "reference_price_krw": 100.0,
            },
            {
                "symbol": "ETH",
                "action": "BUY",
                "final_rank": 2,
                "final_ranking_score": 5.0,
                "policy_materiality": "none",
                "policy_decision": "NEUTRAL",
                "policy_score_delta": 0.0,
                "reference_price_krw": 200.0,
            },
        ],
    )

    assert payload["market_filter_active"] is False
    assert payload["headline"] == "Market filter is inactive; these are the strongest current operator watchlist names."
    assert payload["baseline_priority"][0]["symbol"] == "ETH"
    assert payload["policy_assisted"][0]["symbol"] == "ADA"
    assert payload["recheck_on_filter_release"][0]["symbol"] == "ADA"
