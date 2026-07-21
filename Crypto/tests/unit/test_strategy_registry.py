import json
from pathlib import Path

from app.domains.strategy.registry import StrategyRegistry


def test_strategy_registry_tracks_best_metrics_and_runs(tmp_path: Path) -> None:
    registry = StrategyRegistry(registry_path=tmp_path / "strategy_registry.json")

    first = registry.update_strategy(
        strategy_id="mean_reversion_approved",
        run_id="run-1",
        sharpe=1.2,
        cagr=0.10,
        drawdown=0.20,
    )
    assert first["first_seen_run"] == "run-1"
    assert first["latest_run"] == "run-1"
    assert first["best_sharpe"] == 1.2
    assert first["best_drawdown"] == 0.2

    second = registry.update_strategy(
        strategy_id="mean_reversion_approved",
        run_id="run-2",
        sharpe=1.1,
        cagr=0.15,
        drawdown=0.10,
    )
    assert second["first_seen_run"] == "run-1"
    assert second["latest_run"] == "run-2"
    assert second["best_sharpe"] == 1.2
    assert second["best_cagr"] == 0.15
    assert second["best_drawdown"] == 0.1
    assert len(second["runs"]) == 2

    payload = json.loads((tmp_path / "strategy_registry.json").read_text(encoding="utf-8"))
    assert payload["strategies"][0]["strategy_id"] == "mean_reversion_approved"
