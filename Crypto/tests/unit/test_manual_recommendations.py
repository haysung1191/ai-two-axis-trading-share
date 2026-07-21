from __future__ import annotations

from src.manual.recommendations import build_manual_trade_recommendation


def test_manual_recommendation_marks_policy_reversal_as_buy() -> None:
    recommendation = build_manual_trade_recommendation(
        symbol="BTC",
        blocked_reason=None,
        trace_ctx={
            "normalized_feature_snapshot": {"close": 100.0},
            "suggested_stop_dist": 5.0,
            "suggested_tp_dist": 10.0,
            "suggested_time_exit_ts_ms": 1_710_000_000_000,
            "policy_result": {"policy_decision": "BOOST", "policy_score_delta_capped": 0.05},
            "scheduled_due_to_policy": True,
            "near_miss_after_policy": False,
        },
    )

    assert recommendation["action"] == "BUY"
    assert recommendation["policy_materiality"] == "entry_reversal"
    assert recommendation["reference_price_krw"] == 100.0
    assert recommendation["suggested_stop_price_krw"] == 95.0
    assert recommendation["suggested_take_profit_price_krw"] == 110.0
    assert recommendation["risk_reward_ratio"] == 2.0


def test_manual_recommendation_marks_near_miss_as_hold() -> None:
    recommendation = build_manual_trade_recommendation(
        symbol="ETH",
        blocked_reason="MAX_CONCURRENT",
        trace_ctx={
            "normalized_feature_snapshot": {"close": 200.0},
            "suggested_stop_dist": 8.0,
            "suggested_tp_dist": 16.0,
            "policy_result": {"policy_decision": "BOOST", "policy_score_delta_capped": 0.05},
            "scheduled_due_to_policy": False,
            "near_miss_after_policy": True,
        },
    )

    assert recommendation["action"] == "HOLD"
    assert recommendation["policy_materiality"] == "near_miss"
    assert "near miss" in recommendation["action_reason"].lower()


def test_manual_recommendation_marks_market_downtrend_as_no_buy() -> None:
    recommendation = build_manual_trade_recommendation(
        symbol="XRP",
        blocked_reason="MARKET_DOWNTREND",
        trace_ctx={
            "normalized_feature_snapshot": {"close": 50.0},
            "suggested_stop_dist": 2.0,
            "suggested_tp_dist": 4.0,
            "policy_result": {"policy_decision": "NEUTRAL", "policy_score_delta_capped": 0.0},
        },
    )

    assert recommendation["action"] == "NO_BUY"
    assert recommendation["policy_materiality"] == "none"
    assert "market regime filter" in recommendation["action_reason"].lower()


def test_manual_recommendation_marks_below_cutoff_near_miss_as_hold() -> None:
    recommendation = build_manual_trade_recommendation(
        symbol="SOL",
        blocked_reason="BELOW_ENTRY_CUTOFF",
        trace_ctx={
            "normalized_feature_snapshot": {"close": 300.0},
            "suggested_stop_dist": 10.0,
            "suggested_tp_dist": 20.0,
            "policy_result": {"policy_decision": "BOOST", "policy_score_delta_capped": 0.05},
            "scheduled_due_to_policy": False,
            "near_miss_after_policy": True,
        },
    )

    assert recommendation["action"] == "HOLD"
    assert recommendation["policy_materiality"] == "near_miss"
    assert "below the active entry cutoff" in recommendation["action_reason"].lower()


def test_manual_recommendation_marks_boosted_below_cutoff_as_hold() -> None:
    recommendation = build_manual_trade_recommendation(
        symbol="ADA",
        blocked_reason="BELOW_ENTRY_CUTOFF",
        trace_ctx={
            "normalized_feature_snapshot": {"close": 300.0},
            "suggested_stop_dist": 10.0,
            "suggested_tp_dist": 20.0,
            "policy_result": {"policy_decision": "BOOST", "policy_score_delta_capped": 0.05},
            "scheduled_due_to_policy": False,
            "near_miss_after_policy": False,
        },
    )

    assert recommendation["action"] == "HOLD"
    assert recommendation["policy_materiality"] == "boosted_but_not_decisive"


def test_manual_recommendation_marks_advisory_soft_reject_as_no_buy() -> None:
    recommendation = build_manual_trade_recommendation(
        symbol="XRP",
        blocked_reason=None,
        trace_ctx={
            "normalized_feature_snapshot": {"close": 50.0},
            "suggested_stop_dist": 2.0,
            "suggested_tp_dist": 4.0,
            "policy_result": {"policy_decision": "SOFT_REJECT", "policy_score_delta_capped": 0.0},
        },
    )

    assert recommendation["action"] == "NO_BUY"
    assert recommendation["policy_materiality"] == "policy_reject"
