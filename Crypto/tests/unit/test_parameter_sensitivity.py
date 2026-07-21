import pandas as pd

from app.domains.backtesting.overfitting import OverfittingEvaluator
from app.domains.backtesting.runner import BacktestRunner


class UnstableStrategy:
    name = "unstable"
    default_params = {"amplitude": 1.0}

    def generate_signals(self, ohlcv: pd.DataFrame, params: dict[str, float] | None = None) -> pd.Series:
        amplitude = float((params or self.default_params)["amplitude"])
        close = ohlcv["close"].astype(float)
        # Very sensitive boundary around amplitude=1.0 to trigger instability.
        if amplitude >= 1.0:
            signal = (close.pct_change().fillna(0.0) > 0).astype(float)
        else:
            signal = -1.0 * (close.pct_change().fillna(0.0) > 0).astype(float)
        return signal.replace({0.0: -1.0})


def _sample_ohlcv() -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=160, freq="H")
    close = pd.Series([100 + ((i % 10) - 5) * 0.8 for i in range(160)], index=idx)
    frame = pd.DataFrame(index=idx)
    frame["close"] = close
    frame["open"] = frame["close"].shift(1).fillna(frame["close"])
    frame["high"] = frame[["open", "close"]].max(axis=1) * 1.001
    frame["low"] = frame[["open", "close"]].min(axis=1) * 0.999
    frame["volume"] = 1000.0
    return frame[["open", "high", "low", "close", "volume"]]


def test_parameter_sensitivity_rejects_unstable_strategy() -> None:
    evaluator = OverfittingEvaluator(
        runner=BacktestRunner(seed=42),
        sensitivity_limit=0.2,
    )
    drift, unstable = evaluator.parameter_sensitivity_test(UnstableStrategy(), _sample_ohlcv())

    assert drift > 0.2
    assert "amplitude" in unstable


class ZeroBoundaryStrategy:
    name = "zero-boundary"
    default_params = {"risk_off_drawdown_threshold": 0.0, "window": 10.0}

    def generate_signals(self, ohlcv: pd.DataFrame, params: dict[str, float] | None = None) -> pd.Series:
        _ = params
        close = ohlcv["close"].astype(float)
        return (close.pct_change().fillna(0.0) > 0).astype(float)


def test_parameter_sensitivity_skips_zero_boundary_parameters() -> None:
    evaluator = OverfittingEvaluator(
        runner=BacktestRunner(seed=42),
        sensitivity_limit=0.2,
    )

    drift, unstable = evaluator.parameter_sensitivity_test(ZeroBoundaryStrategy(), _sample_ohlcv())

    assert drift >= 0.0
    assert "risk_off_drawdown_threshold" not in unstable
