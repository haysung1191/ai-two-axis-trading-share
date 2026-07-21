from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.domains.strategy.btc_derivatives_positioning_stress import (
    compute_overlay_signals,
    compute_positioning_stress_state,
)
from scripts.btc_derivatives_positioning_stress_validation import build_report
from app.domains.backtesting.runner import BacktestMetrics


def _frame(periods: int = 800) -> pd.DataFrame:
    idx = pd.date_range("2025-01-01", periods=periods, freq="h", tz="UTC")
    close = pd.Series([100.0 + (i * 0.05) for i in range(periods)], index=idx)
    frame = pd.DataFrame(index=idx)
    frame["open"] = close
    frame["high"] = close + 0.5
    frame["low"] = close - 0.5
    frame["close"] = close
    frame["volume"] = 1000.0
    frame["funding_rate"] = 0.001
    frame["open_interest"] = 10000.0 + pd.Series(range(periods), index=idx).astype(float)
    frame.iloc[-1, frame.columns.get_loc("funding_rate")] = 0.02
    frame.iloc[-1, frame.columns.get_loc("open_interest")] = frame["open_interest"].iloc[-2] * 1.5
    return frame


def test_compute_positioning_stress_state_detects_extreme_joint_state() -> None:
    frame = _frame()
    stress = compute_positioning_stress_state(frame, rolling_window=720, quantile_level=0.9)

    assert bool(stress.iloc[-1]) is True
    assert bool(stress.iloc[-2]) is False


def test_compute_overlay_signals_forces_flat_under_stress() -> None:
    frame = _frame()
    baseline, overlay, stress = compute_overlay_signals(frame, rolling_window=720, quantile_level=0.9)

    assert baseline.index.equals(overlay.index)
    assert bool(stress.iloc[-1]) is True
    assert overlay.iloc[-1] == 0.0


def test_build_report_marks_failure_when_overlay_does_not_beat_baseline() -> None:
    frame = _frame()
    idx = frame.index
    baseline_metrics = BacktestMetrics(
        trades=10,
        sharpe=1.0,
        max_drawdown=0.1,
        win_rate=0.5,
        cagr=0.1,
        equity_curve_summary={},
        equity_curve=[1.0, 1.1],
        equity_timestamps=[idx[0].isoformat(), idx[1].isoformat()],
        trade_ledger=[],
    )
    overlay_metrics = BacktestMetrics(
        trades=12,
        sharpe=0.2,
        max_drawdown=0.08,
        win_rate=0.55,
        cagr=0.05,
        equity_curve_summary={},
        equity_curve=[1.0, 1.02],
        equity_timestamps=[idx[0].isoformat(), idx[1].isoformat()],
        trade_ledger=[],
    )

    report = build_report(
        run_id="run-1",
        symbol="BTCUSDT",
        interval="1h",
        frame=frame,
        baseline_metrics=baseline_metrics,
        overlay_metrics=overlay_metrics,
        stress=pd.Series(False, index=frame.index),
    )

    assert report["decision"]["pass"] is False
    assert report["decision"]["overlay_beats_baseline"] is False
