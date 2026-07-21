from __future__ import annotations

import pandas as pd

from research_lane_stage2.classifier import classify_compressed_variant
from research_lane_stage2.eligibility import source_eligibility
from research_lane_stage2.metrics import compute_compression_metrics
from research_lane_stage2.overlay_backtest import apply_transform
from research_lane_stage2.persistence import append_robustness_queue
from research_lane_stage2.variant_schema import generate_compression_variants


def test_conversion_candidate_missing_artifact_is_ineligible(tmp_path) -> None:
    source = {"candidate_type": "account_portfolio_model", "account": "KIS_COMBINED_KRW", "primary_class": "conversion_candidate"}

    result = source_eligibility(source, {"daily_equity": tmp_path / "missing.csv"})

    assert result["eligible"] is False
    assert any(reason.startswith("missing_source_artifact") for reason in result["reason_codes"])


def test_cash_filter_reduces_exposure_and_preserves_sum() -> None:
    weights = pd.DataFrame(
        [
            {"date": "2026-01-01", "symbol": "A", "weight": 0.50},
            {"date": "2026-01-01", "symbol": "B", "weight": 0.50},
            {"date": "2026-01-01", "symbol": "CASH_KRW", "weight": 0.00},
        ]
    )
    equity = pd.Series([1.0], index=pd.to_datetime(["2026-01-01"]))

    out = apply_transform(weights, equity, {"type": "cash_filter", "exposure_scale": 0.40})

    assert out.loc[pd.Timestamp("2026-01-01"), "A"] == 0.20
    assert out.loc[pd.Timestamp("2026-01-01"), "B"] == 0.20
    assert out.loc[pd.Timestamp("2026-01-01"), "CASH_KRW"] == 0.60
    assert abs(out.sum(axis=1).iloc[0] - 1.0) < 1e-9


def test_position_cap_reduces_concentration() -> None:
    weights = pd.DataFrame(
        [
            {"date": "2026-01-01", "symbol": "A", "weight": 0.60},
            {"date": "2026-01-01", "symbol": "B", "weight": 0.40},
            {"date": "2026-01-01", "symbol": "CASH_KRW", "weight": 0.00},
        ]
    )
    equity = pd.Series([1.0], index=pd.to_datetime(["2026-01-01"]))

    out = apply_transform(weights, equity, {"type": "position_cap", "position_cap": 0.30})

    assert out.loc[pd.Timestamp("2026-01-01"), "A"] <= 0.30
    assert out.loc[pd.Timestamp("2026-01-01"), "B"] <= 0.30
    assert out.loc[pd.Timestamp("2026-01-01"), "CASH_KRW"] >= 0.40


def test_compression_metrics_and_classification_thresholds() -> None:
    source_metrics = {"periods": {"full": {"mdd": -0.40, "cagr": 1.0, "total_return": 10.0, "turnover_avg_daily": 0.10, "sortino": 1.0, "sharpe": 1.0}}}
    variant_metrics = {"periods": {"full": {"mdd": -0.30, "cagr": 0.70, "total_return": 7.0, "turnover_avg_daily": 0.05, "sortino": 1.1, "sharpe": 1.1, "average_cash_ratio": 0.30}}}
    dates = pd.date_range("2026-01-01", periods=40)
    source_artifacts = {
        "daily_returns": pd.DataFrame({"date": dates, "return_net": [-0.05] + [0.01] * 39}),
        "daily_equity": pd.DataFrame({"date": dates, "equity_krw": [1.0 + i * 0.01 for i in range(40)]}),
    }
    variant_backtest = {
        "daily_returns": pd.DataFrame({"date": dates, "return_net": [-0.03] + [0.008] * 39}),
        "daily_equity": pd.DataFrame({"date": dates, "equity_krw": [1.0 + i * 0.008 for i in range(40)]}),
    }

    metrics = compute_compression_metrics(source_metrics, source_artifacts, variant_metrics, variant_backtest)
    classification = classify_compressed_variant({"variant_id": "v1"}, variant_metrics, metrics)

    assert round(metrics["periods"]["full"]["mdd_reduction_pct"], 4) == 0.25
    assert round(metrics["periods"]["full"]["cagr_retention_pct"], 4) == 0.70
    assert classification["primary_class"] in {"robustness_candidate", "compression_research_only"}


def test_robustness_queue_rejects_component_signal(tmp_path) -> None:
    paths = {"queues": tmp_path}
    bad = {"candidate_type": "component_signal_reference", "primary_class": "robustness_candidate"}

    try:
        append_robustness_queue(bad, paths)
    except ValueError as exc:
        assert "requires_stage2_account_variant" in str(exc)
    else:
        raise AssertionError("component signal queued")


def test_variant_generation_keeps_safety_false() -> None:
    source = {"model_id": "m1", "run_id": "r1", "account": "BITHUMB_KRW", "family_id": "f1", "primary_class": "high_return_high_risk", "candidate_type": "account_portfolio_model"}

    variants = generate_compression_variants(source)

    assert variants
    assert all(v["safety"]["live_enabled"] is False for v in variants)
    assert all(v["candidate_type"] == "stage2_compressed_account_portfolio_model" for v in variants)

