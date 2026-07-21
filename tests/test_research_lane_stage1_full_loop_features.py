from __future__ import annotations

import pandas as pd

from research_lane_stage1.evaluation.regimes import assign_simple_regimes, compute_regime_breakdown
from research_lane_stage1.families.bithumb import (
    btc_eth_alt_rotation,
    cash_rotation,
    liquidity_rotation,
    short_reversal,
    volatility_breakout,
    xs_momentum,
)
from research_lane_stage1.families.kis import (
    axis_cap,
    combined_momentum,
    combined_short_reversal,
    dynamic_cash,
    etf_core_stock_satellite,
    risk_rotation,
)
from research_lane_stage1.persistence.legacy_import import load_legacy_stage1_records


def test_all_stage1_family_generators_emit_account_models() -> None:
    b_uni = {"symbol_count": 34, "universe_id": "bithumb_krw_liquid_min1000_vol1b"}
    k_uni = {"symbol_count": 11996, "universe_id": "kis_combined_all_kr_us_stock_etf"}
    generators = [
        xs_momentum.generate_models(b_uni),
        short_reversal.generate_models(b_uni),
        btc_eth_alt_rotation.generate_models(b_uni),
        volatility_breakout.generate_models(b_uni),
        liquidity_rotation.generate_models(b_uni),
        cash_rotation.generate_models(b_uni),
        combined_short_reversal.generate_models(k_uni),
        combined_momentum.generate_models(k_uni),
        etf_core_stock_satellite.generate_models(k_uni),
        risk_rotation.generate_models(k_uni),
        axis_cap.generate_models(k_uni),
        dynamic_cash.generate_models(k_uni),
    ]

    models = [model for batch in generators for model in batch]
    assert models
    assert all(model["candidate_type"] == "account_portfolio_model" for model in models)
    assert all(model["safety"]["live_trade_allowed"] is False for model in models)


def test_regime_breakdown_smoke() -> None:
    dates = pd.date_range("2024-01-01", periods=40, freq="D")
    price_rows = pd.DataFrame({"date": dates, "symbol": "BTC_KRW", "close": range(100, 140)})
    regimes = assign_simple_regimes(price_rows, "BITHUMB_KRW")
    daily_returns = pd.DataFrame({"date": dates, "return_net": [0.001] * 40})
    daily_equity = pd.DataFrame({"date": dates, "equity_krw": [(1.001) ** i for i in range(40)]})
    daily_turnover = pd.DataFrame({"date": dates, "one_way_turnover": [0.0] * 40})
    daily_weights = pd.DataFrame({"date": dates, "symbol": "CASH_KRW", "weight": [1.0] * 40})

    out = compute_regime_breakdown(daily_returns, daily_equity, daily_turnover, daily_weights, regimes, account="BITHUMB_KRW")

    assert out


def test_legacy_import_preserves_account_and_component_records() -> None:
    records, components = load_legacy_stage1_records({"symbol_count": 11996}, {"symbol_count": 34})

    assert records
    assert components
    assert any(row["classification"]["primary_class"] == "conversion_candidate" for row in records)
    assert components[0]["model"]["candidate_type"] == "component_signal_reference"

