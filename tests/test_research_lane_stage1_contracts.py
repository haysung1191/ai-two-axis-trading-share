from __future__ import annotations

import pytest

from research_lane_stage1.classification.classifier import classify_candidate
from research_lane_stage1.models.schema import build_component_signal_reference, build_model_definition
from research_lane_stage1.models.validation import (
    assert_account_level_model,
    reject_single_asset_candidate,
    validate_model_schema,
)


def account_model(**overrides):
    model = build_model_definition(
        model_id="KIS_COMBINED_KRW_kis_combined_short_reversal_l5_top100_axiscap0.5_reb21",
        family_id="kis_combined_short_reversal",
        family_name="KIS combined short reversal",
        account="KIS_COMBINED_KRW",
        universe={
            "universe_id": "kis_combined_all_kr_us_stock_etf",
            "asset_types": ["kr_stock", "us_stock", "kr_etf", "us_etf"],
            "include_rules": ["valid_krw_price == true"],
            "exclude_rules": ["is_suspended == true"],
            "expected_asset_count": 11996,
            "survivorship_policy": "tag_not_block",
        },
        signals={
            "selection_rule": {"type": "cross_sectional_short_reversal", "lookback_days": 5},
            "entry_rule": {"type": "rebalance_entry"},
            "exit_rule": {"type": "rebalance_exit"},
            "ranking_rule": {"type": "ascending_return"},
            "component_signal_refs": [],
        },
        portfolio={
            "sizing_rule": {"type": "equal_weight", "position_cap": 0.01},
            "rebalance_rule": {"type": "calendar", "frequency_days": 21},
            "cash_rule": {"type": "idle_cash", "unallocated_weight_goes_to_cash": True},
            "max_positions": 100,
            "axis_caps": {"axis_cap": 0.5},
        },
        costs={
            "cost_model_id": "stage1_research_costs_v1",
            "commission_bps_per_side": {"default": 20.0},
            "slippage_bps_per_side": {"default": 0.0},
            "tax_bps_sell": {"default": 0.0},
            "fx_spread_bps": {"default": 0.0},
        },
        backtest={
            "price_field": "adj_close",
            "execution_price": "next_close",
            "signal_lag_days": 1,
            "allow_fractional": True,
            "cash_return": 0,
            "base_currency": "KRW",
        },
    )
    model.update(overrides)
    return model


def metrics(*, test_cagr=0.50, test_mdd=-0.20, oos_cagr=0.20, full_trade_count=80):
    return {
        "periods": {
            "full": {
                "days": 4000,
                "cagr": 0.60,
                "mdd": min(test_mdd, -0.10),
                "sharpe": 1.5,
                "profit_factor_daily": 1.2,
                "trade_count": full_trade_count,
            },
            "test": {
                "days": 756,
                "cagr": test_cagr,
                "mdd": test_mdd,
                "sharpe": 1.1 if test_cagr > 0 else -0.5,
                "profit_factor_daily": 1.2,
            },
            "oos": {
                "days": 504,
                "cagr": oos_cagr,
                "mdd": test_mdd,
                "sharpe": 1.0 if oos_cagr > 0 else -0.4,
                "profit_factor_daily": 1.1,
            },
        }
    }


def test_valid_account_model_schema_and_invariant() -> None:
    model = account_model()

    assert validate_model_schema(model) == []
    assert_account_level_model(model)


def test_single_asset_candidate_is_reclassified_not_account_model() -> None:
    model = account_model(
        account="BITHUMB_KRW",
        universe={
            "universe_id": "btc_only",
            "asset_types": ["crypto"],
            "expected_asset_count": 1,
            "survivorship_policy": "tag_not_block",
        },
        portfolio={
            "sizing_rule": {"type": "equal_weight"},
            "rebalance_rule": {"type": "calendar", "frequency_days": 1},
            "cash_rule": {"type": "idle_cash"},
            "max_positions": 1,
        },
    )

    assert reject_single_asset_candidate(model)
    with pytest.raises(ValueError, match="not_account_level"):
        assert_account_level_model(model)

    result = classify_candidate(model, metrics(), {"blocking_flags": [], "cost_model_complete": True})
    assert result["primary_class"] == "component_signal_reference"
    assert result["conversion_queue_eligible"] is False


def test_component_signal_reference_is_never_conversion_candidate() -> None:
    signal = build_component_signal_reference(
        signal_id="btc_1d_post_spike_consolidation_breakout_v4",
        source_asset="BTC_KRW",
        account_compatibility=["BITHUMB_KRW"],
        allowed_usage=["regime_filter", "ranking_feature"],
        metrics_reference={"cagr": 0.519, "mdd": -0.118, "sharpe": 2.18},
    )

    result = classify_candidate(signal, metrics(), {"blocking_flags": [], "cost_model_complete": True})

    assert result["primary_class"] == "component_signal_reference"
    assert result["conversion_queue_eligible"] is False


def test_kis_short_reversal_top100_is_conversion_candidate() -> None:
    result = classify_candidate(
        account_model(),
        metrics(test_cagr=0.462, test_mdd=-0.311, oos_cagr=0.20, full_trade_count=90),
        {"blocking_flags": [], "warning_flags": ["survivorship_warning_current_listed_only"], "cost_model_complete": True},
    )

    assert result["primary_class"] == "conversion_candidate"
    assert result["conversion_queue_eligible"] is True
    assert "conversion_candidate" in result["secondary_tags"]


def test_kis_short_reversal_top25_is_conversion_candidate_with_high_risk_tag() -> None:
    result = classify_candidate(
        account_model(),
        metrics(test_cagr=1.07, test_mdd=-0.401, oos_cagr=0.30, full_trade_count=90),
        {"blocking_flags": [], "cost_model_complete": True},
    )

    assert result["primary_class"] == "conversion_candidate"
    assert "high_return_high_risk" in result["secondary_tags"]


def test_bithumb_negative_test_model_is_reject_or_redesign() -> None:
    model = account_model(account="BITHUMB_KRW")
    result = classify_candidate(
        model,
        metrics(test_cagr=-0.372, test_mdd=-0.612, oos_cagr=-0.25, full_trade_count=60),
        {"blocking_flags": [], "cost_model_complete": True},
    )

    assert result["primary_class"] == "reject_or_redesign"
    assert "negative_test_cagr" in result["reason_codes"]
    assert "test_collapse" in result["reason_codes"]


def test_data_quality_blocker_prevents_queue() -> None:
    result = classify_candidate(
        account_model(),
        metrics(test_cagr=1.0, test_mdd=-0.20, oos_cagr=0.50, full_trade_count=100),
        {"blocking_flags": ["fx_lookahead_detected"], "cost_model_complete": True},
    )

    assert result["primary_class"] == "data_quality_blocked"
    assert result["blocked"] is True
    assert result["conversion_queue_eligible"] is False
