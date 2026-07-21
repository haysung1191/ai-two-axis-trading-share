from __future__ import annotations

from build_stage5_materialized_from_stage2_queue import queue_record_for_candidate, stage5_pass


def test_stage5_pass_accepts_complete_positive_oos_candidate() -> None:
    metrics = {
        "periods": {
            "oos": {
                "days": 608,
                "cagr": 0.122,
                "mdd": -0.319,
                "sharpe": 0.507,
                "sortino": 0.8,
                "profit_factor_daily": 1.1,
            }
        }
    }

    passed, passed_checks, failed_checks = stage5_pass(
        metrics,
        {"robustness_queue_eligible": True, "blocking_flags": []},
        {"blocking_flags": []},
    )

    assert passed is True
    assert "oos_mdd_within_conditional_stage5_limit" in passed_checks
    assert failed_checks == []


def test_stage5_pass_rejects_oos_mdd_beyond_conditional_limit() -> None:
    metrics = {
        "periods": {
            "oos": {
                "days": 608,
                "cagr": 0.108,
                "mdd": -0.364,
                "sharpe": 0.497,
                "sortino": 0.8,
                "profit_factor_daily": 1.1,
            }
        }
    }

    passed, _, failed_checks = stage5_pass(
        metrics,
        {"robustness_queue_eligible": True, "blocking_flags": []},
        {"blocking_flags": []},
    )

    assert passed is False
    assert "oos_mdd_within_conditional_stage5_limit" in failed_checks
    assert "oos_sharpe_at_least_0_50" in failed_checks


def test_stage5_pass_rejects_classification_blocking_flags() -> None:
    metrics = {
        "periods": {
            "oos": {
                "days": 608,
                "cagr": 0.122,
                "mdd": -0.319,
                "sharpe": 0.507,
                "sortino": 0.8,
                "profit_factor_daily": 1.1,
            }
        }
    }

    passed, _, failed_checks = stage5_pass(
        metrics,
        {"robustness_queue_eligible": True, "blocking_flags": ["bad"]},
        {"blocking_flags": []},
    )

    assert passed is False
    assert "classification_no_blocking_flags" in failed_checks


def test_queue_record_for_candidate_uses_registry_variant_mapping() -> None:
    row = queue_record_for_candidate("CAND-014")

    assert row["variant_id"] == "KIS_COMBINED_KRW_b901c411a6_drawdown_state_exposure_scaler_8f1c0c9727"


def test_queue_record_for_candidate_uses_registry_metrics_ref_fallback() -> None:
    row = queue_record_for_candidate("CAND-006")

    assert row["variant_id"] == "KIS_COMBINED_KRW_cbbfff74ba_drawdown_state_exposure_scaler_8f1c0c9727"
