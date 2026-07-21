import json
from pathlib import Path

from app.domains.governance.artifact_store import ArtifactStore
from app.domains.governance.contracts import RunLeaderboard, RunLeaderboardEntry, Spec
from app.domains.governance.run_logger import RunLogger
from app.domains.governance.workflow import GovernanceWorkflow
from app.domains.strategy.registry import StrategyRegistry


def _build_base_state(run_id: str) -> dict:
    return {
        "run_id": run_id,
        "spec": Spec(
            run_goal="approval check",
            context="unit test",
            requirements=[],
            metadata={
                "strategy_name": "mean_reversion",
                "strategy_id": "mean_reversion_v3",
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "position_size": 0.1,
                "expected_max_drawdown": 0.05,
            },
        ).model_dump(mode="json"),
        "run_leaderboard": RunLeaderboard(
            run_id=run_id,
            entries=[
                RunLeaderboardEntry(
                    strategy_name="mean_reversion",
                    sharpe=1.5,
                    cagr=0.2,
                    max_drawdown=0.1,
                    win_rate=0.6,
                    trades=10,
                    qa_passed=True,
                    risk_passed=True,
                    backtest_passed=True,
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


def test_approved_strategy_generated_only_on_pass(tmp_path: Path) -> None:
    artifacts = ArtifactStore(root_dir=tmp_path / "artifacts")
    registry_path = tmp_path / "strategy_registry.json"
    workflow = GovernanceWorkflow(
        artifact_store=artifacts,
        run_logger=RunLogger(root_dir=tmp_path / "logs"),
        strategy_registry=StrategyRegistry(registry_path=registry_path),
    )

    run_id_pass = "run-pass-1"
    workflow._supervisor_node(_build_base_state(run_id_pass))
    approved_path = tmp_path / "artifacts" / run_id_pass / "approved_strategy.json"
    summary_path = tmp_path / "artifacts" / run_id_pass / "decision_summary.md"
    assert approved_path.exists()
    assert summary_path.exists()
    payload = json.loads(approved_path.read_text(encoding="utf-8"))
    assert payload["top_k"] == 1
    assert payload["winners"][0]["source_run_id"] == run_id_pass
    registry_payload = json.loads(registry_path.read_text(encoding="utf-8"))
    assert registry_payload["strategies"][0]["latest_run"] == run_id_pass

    run_id_fail = "run-fail-1"
    fail_state = _build_base_state(run_id_fail)
    fail_state["run_leaderboard"]["entries"][0]["qa_passed"] = False
    fail_state["run_leaderboard"]["entries"][0]["failed_gates"] = ["qa"]
    workflow._supervisor_node(fail_state)
    fail_path = tmp_path / "artifacts" / run_id_fail / "approved_strategy.json"
    fail_summary = tmp_path / "artifacts" / run_id_fail / "decision_summary.md"
    assert not fail_path.exists()
    assert fail_summary.exists()
    registry_after_fail = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(registry_after_fail["strategies"][0]["runs"]) == 1
