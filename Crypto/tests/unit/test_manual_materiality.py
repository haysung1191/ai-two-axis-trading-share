from __future__ import annotations

from src.manual.materiality import build_policy_materiality_summary


def test_policy_materiality_summary_quantifies_boost_gap() -> None:
    payload = build_policy_materiality_summary(
        recommendations=[
            {
                "symbol": "SIGN",
                "policy_score_delta": 0.05,
                "score": 3.4164,
                "raw_rank": 5,
                "final_rank": 5,
                "scheduled_due_to_policy": False,
                "near_miss_after_policy": False,
                "policy_materiality": "boosted_but_not_decisive",
                "final_decision": "CANCELED:MARKET_DOWNTREND",
            },
            {
                "symbol": "ETH",
                "policy_score_delta": 0.05,
                "score": 5.55,
                "raw_rank": 2,
                "final_rank": 1,
                "scheduled_due_to_policy": True,
                "near_miss_after_policy": False,
                "policy_materiality": "entry_reversal",
                "final_decision": "SCHEDULED",
            },
        ],
        snapshot_metadata={
            "top_n": 10,
            "counterfactual_buys_without_market_filter": [
                {"symbol": "A", "final_ranking_score": 5.55},
                {"symbol": "B", "final_ranking_score": 5.0},
                {"symbol": "C", "final_ranking_score": 4.0},
                {"symbol": "D", "final_ranking_score": 3.9},
                {"symbol": "E", "final_ranking_score": 3.5},
            ],
        },
    )

    assert payload["boosted_candidate_count"] == 2
    assert payload["direct_reversal_count"] == 1
    assert payload["cutoff_rank"] == 5
    assert payload["cutoff_score"] == 3.5
    closest = payload["closest_to_reversal"][0]
    assert closest["symbol"] == "ETH"
    assert closest["required_extra_delta_for_cutoff"] == 0.0


def test_policy_materiality_excludes_market_filter_blocked_rows_from_closest_to_reversal() -> None:
    payload = build_policy_materiality_summary(
        recommendations=[
            {
                "symbol": "TRX",
                "policy_score_delta": 0.05,
                "score": 5.0,
                "raw_rank": 2,
                "final_rank": 2,
                "scheduled_due_to_policy": False,
                "near_miss_after_policy": False,
                "policy_materiality": "boosted_but_not_decisive",
                "final_decision": "CANCELED:MARKET_DOWNTREND",
            },
            {
                "symbol": "ADA",
                "policy_score_delta": 0.05,
                "score": 4.8,
                "raw_rank": 11,
                "final_rank": 11,
                "scheduled_due_to_policy": False,
                "near_miss_after_policy": True,
                "policy_materiality": "near_miss",
                "final_decision": "CANCELED:BELOW_ENTRY_CUTOFF",
            },
        ],
        snapshot_metadata={
            "top_n": 10,
            "counterfactual_buys_without_market_filter": [
                {"symbol": "X", "final_ranking_score": 5.2} for _ in range(10)
            ],
        },
    )

    assert payload["closest_to_reversal"][0]["symbol"] == "ADA"
