from __future__ import annotations

import pandas as pd

from research_lane_stage3.run_stage3 import decision, max_drawdown, period_metrics


def test_max_drawdown_from_equity_curve() -> None:
    equity = pd.Series([1.0, 1.2, 0.9, 1.3])

    assert round(max_drawdown(equity), 4) == -0.25


def test_period_metrics_positive_curve() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=5),
            "return_net": [0.0, 0.01, 0.01, 0.01, 0.01],
            "cash_weight": [0.0, 0.1, 0.1, 0.1, 0.1],
            "equity_krw": [1.0, 1.01, 1.02, 1.03, 1.04],
        }
    )

    metrics = period_metrics(frame)

    assert metrics["days"] == 5
    assert metrics["cagr"] > 0
    assert metrics["mdd"] == 0.0
    assert metrics["avg_cash_weight"] > 0


def test_decision_blocks_bad_late_window() -> None:
    metrics = {
        "full": {"cagr": 0.3, "mdd": -0.2, "sharpe": 1.0},
        "late": {"cagr": -0.1, "mdd": -0.2, "sharpe": -0.2},
    }
    source = {"periods": {"full": {"cagr": 0.5, "mdd": -0.3}}}

    status, reasons = decision(metrics, source)

    assert status == "stage3_needs_repair_or_more_evidence"
    assert "late_window_cagr_not_positive" in reasons

