import pandas as pd
import pytest

from app.domains.backtesting.runner import BacktestRunner, metrics_to_dict
from app.domains.strategy.loader import load_strategy
from app.domains.strategy.strategy_protocol import Strategy


def _sample_ohlcv() -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=120, freq="H")
    close = pd.Series([100 + (i * 0.05) + ((i % 8) - 4) * 0.2 for i in range(120)], index=idx)
    frame = pd.DataFrame(index=idx)
    frame["close"] = close
    frame["open"] = frame["close"].shift(1).fillna(frame["close"])
    frame["high"] = frame[["open", "close"]].max(axis=1) * 1.001
    frame["low"] = frame[["open", "close"]].min(axis=1) * 0.999
    frame["volume"] = 1000.0
    return frame[["open", "high", "low", "close", "volume"]]


def test_backtest_runner_is_deterministic() -> None:
    strategy = load_strategy("mean_reversion")
    runner = BacktestRunner(seed=42)
    ohlcv = _sample_ohlcv()

    first = metrics_to_dict(runner.run(strategy, ohlcv))
    second = metrics_to_dict(runner.run(strategy, ohlcv))

    assert first == second


class _AlwaysLongStrategy(Strategy):
    name = "always_long"
    default_params: dict[str, float] = {}

    def generate_signals(self, ohlcv: pd.DataFrame, params=None) -> pd.Series:
        _ = params
        return pd.Series(1.0, index=ohlcv.index)


class _AlwaysShortStrategy(Strategy):
    name = "always_short"
    default_params: dict[str, float] = {}

    def generate_signals(self, ohlcv: pd.DataFrame, params=None) -> pd.Series:
        _ = params
        return pd.Series(-1.0, index=ohlcv.index)


def test_backtest_runner_applies_execution_costs() -> None:
    strategy = _AlwaysLongStrategy()
    runner = BacktestRunner(seed=42)
    ohlcv = _sample_ohlcv()

    without_costs = runner.run(strategy, ohlcv)
    with_costs = runner.run(strategy, ohlcv, fee_bps=10.0, slippage_bps=5.0)

    assert with_costs.equity_curve_summary["end"] < without_costs.equity_curve_summary["end"]
    assert with_costs.cagr < without_costs.cagr


def test_backtest_runner_annualizes_hourly_metrics_from_index_frequency() -> None:
    strategy = _AlwaysLongStrategy()
    runner = BacktestRunner(seed=42)
    idx = pd.date_range("2024-01-01", periods=49, freq="h")
    close = pd.Series([100.0 * (1.001**i) for i in range(49)], index=idx)
    ohlcv = pd.DataFrame(index=idx)
    ohlcv["close"] = close
    ohlcv["open"] = ohlcv["close"].shift(1).fillna(ohlcv["close"])
    ohlcv["high"] = ohlcv[["open", "close"]].max(axis=1)
    ohlcv["low"] = ohlcv[["open", "close"]].min(axis=1)
    ohlcv["volume"] = 1000.0

    metrics = runner.run(strategy, ohlcv)

    period_returns = ohlcv["close"].pct_change().fillna(0.0)
    ret_mean = float(period_returns.mean())
    ret_std = float(period_returns.std(ddof=0))
    periods_per_year = 365.25 * 24.0
    expected_sharpe = (ret_mean / ret_std) * (periods_per_year ** 0.5)
    years = (len(ohlcv) - 1) / periods_per_year
    expected_cagr = float((metrics.equity_curve_summary["end"] ** (1 / years)) - 1.0)

    assert metrics.sharpe == pytest.approx(round(expected_sharpe, 8))
    assert metrics.cagr == pytest.approx(round(expected_cagr, 8))


def test_backtest_runner_handles_non_positive_final_equity_without_complex_cagr() -> None:
    strategy = _AlwaysShortStrategy()
    runner = BacktestRunner(seed=42)
    idx = pd.date_range("2024-01-01", periods=3, freq="h")
    close = pd.Series([100.0, 300.0, 300.0], index=idx)
    ohlcv = pd.DataFrame(index=idx)
    ohlcv["close"] = close
    ohlcv["open"] = ohlcv["close"].shift(1).fillna(ohlcv["close"])
    ohlcv["high"] = ohlcv[["open", "close"]].max(axis=1)
    ohlcv["low"] = ohlcv[["open", "close"]].min(axis=1)
    ohlcv["volume"] = 1000.0

    metrics = runner.run(strategy, ohlcv)

    assert metrics.equity_curve_summary["end"] < 0.0
    assert metrics.cagr == -1.0


def test_backtest_runner_emits_timestamped_equity_and_trade_ledger() -> None:
    strategy = _AlwaysLongStrategy()
    runner = BacktestRunner(seed=42)
    ohlcv = _sample_ohlcv().iloc[:8]

    metrics = runner.run(strategy, ohlcv)

    assert metrics.equity_timestamps == [ts.isoformat() for ts in ohlcv.index]
    assert len(metrics.trade_ledger) >= 1
    first_trade = metrics.trade_ledger[0]
    assert first_trade["entry_timestamp"] == ohlcv.index[1].isoformat()
    assert first_trade["direction"] == "long"
    assert "pnl" in first_trade
