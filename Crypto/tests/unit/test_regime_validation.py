import pandas as pd

from app.domains.backtesting.runner import BacktestRunner
from app.domains.governance.artifact_store import ArtifactStore
from app.domains.governance.contracts import RunLeaderboard, RunLeaderboardEntry, Spec
from app.domains.governance.run_logger import RunLogger
from app.domains.governance.workflow import GovernanceWorkflow
from app.domains.strategy.loader import load_strategy


def _sample_ohlcv_with_regimes() -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=240, freq="h")
    close_values: list[float] = []
    price = 100.0
    for i in range(240):
        if i < 60:  # trend
            price += 0.3
        elif i < 120:  # range
            price += 0.15 if i % 2 == 0 else -0.15
        elif i < 180:  # high volatility
            price += 1.2 if i % 2 == 0 else -1.0
        else:  # low volatility
            price += 0.03 if i % 2 == 0 else -0.02
        close_values.append(price)
    close = pd.Series(close_values, index=idx)
    frame = pd.DataFrame(index=idx)
    frame["close"] = close
    frame["open"] = frame["close"].shift(1).fillna(frame["close"])
    frame["high"] = frame[["open", "close"]].max(axis=1) * 1.001
    frame["low"] = frame[["open", "close"]].min(axis=1) * 0.999
    frame["volume"] = 1000.0
    return frame[["open", "high", "low", "close", "volume"]]


def test_backtest_runner_generates_regime_metrics() -> None:
    runner = BacktestRunner(seed=42)
    strategy = load_strategy("mean_reversion")
    frame = _sample_ohlcv_with_regimes()

    regime_metrics = runner.evaluate_regimes(strategy, frame)
    assert "sharpe_by_regime" in regime_metrics
    assert "drawdown_by_regime" in regime_metrics
    assert "sharpe_regime_std" in regime_metrics
    assert set(regime_metrics["sharpe_by_regime"].keys()) == {
        "trend",
        "range",
        "high_volatility",
        "low_volatility",
    }


def test_backtest_runner_regime_splits_use_contiguous_segments() -> None:
    runner = BacktestRunner(seed=42)
    frame = _sample_ohlcv_with_regimes()

    regime_frames = runner._split_by_regime(frame)

    for subset in regime_frames.values():
        assert len(subset) >= 30
        assert subset.index.is_monotonic_increasing
        diffs = subset.index.to_series().diff().dropna()
        assert diffs.empty or diffs.eq(pd.Timedelta(hours=1)).all()


def test_supervisor_rejects_when_regime_sharpe_variation_too_high(tmp_path) -> None:
    workflow = GovernanceWorkflow(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        run_logger=RunLogger(root_dir=tmp_path / "logs"),
        talk_delay_sec=0.0,
    )
    state = {
        "run_id": "run-regime-instability",
        "spec": Spec(
            run_goal="regime stability",
            context="unit test",
            requirements=[],
            metadata={},
        ).model_dump(mode="json"),
        "run_leaderboard": RunLeaderboard(
            run_id="run-regime-instability",
            entries=[
                RunLeaderboardEntry(
                    strategy_name="regime_unstable",
                    sharpe=1.6,
                    cagr=0.2,
                    max_drawdown=0.1,
                    win_rate=0.6,
                    trades=20,
                    qa_passed=True,
                    risk_passed=True,
                    backtest_passed=True,
                    sharpe_std=0.3,
                    sharpe_regime_std=2.2,
                    stability_score=0.9,
                    overfitting_flags=[],
                    failed_gates=[],
                )
            ],
        ).model_dump(mode="json"),
        "reject_count": 0,
        "iteration": 0,
        "max_iterations": 6,
    }

    result = workflow._supervisor_node(state)
    assert result["status"] == "REJECTED"
    assert "regime_instability" in result["decision_record"]["failed_gates"]
