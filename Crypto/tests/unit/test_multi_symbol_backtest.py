from pathlib import Path

import pandas as pd

from app.domains.backtesting.runner import BacktestRunner, multi_asset_metrics_to_dict
from app.domains.governance.artifact_store import ArtifactStore
from app.domains.governance.contracts import RunLeaderboard, RunLeaderboardEntry, Spec
from app.domains.governance.run_logger import RunLogger
from app.domains.governance.workflow import GovernanceWorkflow
from app.domains.strategy.loader import load_strategy


def _sample_ohlcv(base: float, drift: float) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=120, freq="h")
    close = pd.Series([base + (i * drift) + ((i % 8) - 4) * 0.2 for i in range(120)], index=idx)
    frame = pd.DataFrame(index=idx)
    frame["close"] = close
    frame["open"] = frame["close"].shift(1).fillna(frame["close"])
    frame["high"] = frame[["open", "close"]].max(axis=1) * 1.001
    frame["low"] = frame[["open", "close"]].min(axis=1) * 0.999
    frame["volume"] = 1000.0
    return frame[["open", "high", "low", "close", "volume"]]


def test_backtest_runner_multi_symbol_aggregates_are_deterministic() -> None:
    strategy = load_strategy("mean_reversion")
    runner = BacktestRunner(seed=42)
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    ohlcv_by_symbol = {
        "BTCUSDT": _sample_ohlcv(100.0, 0.04),
        "ETHUSDT": _sample_ohlcv(80.0, 0.03),
        "SOLUSDT": _sample_ohlcv(40.0, 0.06),
    }

    first = multi_asset_metrics_to_dict(
        runner.run_multi_symbol(strategy, symbols=symbols, ohlcv_by_symbol=ohlcv_by_symbol)
    )
    second = multi_asset_metrics_to_dict(
        runner.run_multi_symbol(strategy, symbols=symbols, ohlcv_by_symbol=ohlcv_by_symbol)
    )

    assert first == second
    assert first["symbols"] == sorted(symbols)
    assert set(first["per_symbol"].keys()) == set(symbols)
    assert "sharpe_mean" in first
    assert "sharpe_std" in first
    assert "drawdown_mean" in first
    assert "drawdown_worst" in first


def test_supervisor_rejects_high_cross_asset_sharpe_std(tmp_path: Path) -> None:
    workflow = GovernanceWorkflow(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        run_logger=RunLogger(root_dir=tmp_path / "logs"),
        talk_delay_sec=0.0,
    )
    state = {
        "run_id": "run-high-sharpe-std",
        "spec": Spec(
            run_goal="multi asset stability gate",
            context="unit test",
            requirements=[],
            metadata={},
        ).model_dump(mode="json"),
        "run_leaderboard": RunLeaderboard(
            run_id="run-high-sharpe-std",
            entries=[
                RunLeaderboardEntry(
                    strategy_name="unstable_across_assets",
                    sharpe=2.0,
                    cagr=0.2,
                    max_drawdown=0.1,
                    win_rate=0.6,
                    trades=20,
                    qa_passed=True,
                    risk_passed=True,
                    backtest_passed=True,
                    sharpe_std=2.5,
                    stability_score=0.95,
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
    assert result["decision_record"]["decision"] == "FAIL"
    assert "cross_asset_instability" in result["decision_record"]["failed_gates"]
