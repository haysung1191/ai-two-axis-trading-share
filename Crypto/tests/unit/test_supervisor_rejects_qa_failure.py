from pathlib import Path

from app.domains.governance.artifact_store import ArtifactStore
from app.domains.governance.contracts import RunLeaderboard, RunLeaderboardEntry, Spec
from app.domains.governance.run_logger import RunLogger
from app.domains.governance.workflow import GovernanceWorkflow


def test_supervisor_rejects_when_qa_failed(tmp_path: Path) -> None:
    workflow = GovernanceWorkflow(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        run_logger=RunLogger(root_dir=tmp_path / "logs"),
    )

    state = {
        "run_id": "run-sup-qa-fail",
        "spec": Spec(
            run_goal="qa reject check",
            context="unit test",
            requirements=[],
            metadata={"strategy_name": "mean_reversion"},
        ).model_dump(mode="json"),
        "run_leaderboard": RunLeaderboard(
            run_id="run-sup-qa-fail",
            entries=[
                RunLeaderboardEntry(
                    strategy_name="mean_reversion",
                    sharpe=2.0,
                    cagr=0.2,
                    max_drawdown=0.05,
                    win_rate=0.7,
                    trades=12,
                    qa_passed=False,
                    risk_passed=True,
                    backtest_passed=True,
                    stability_score=0.9,
                    overfitting_flags=[],
                    failed_gates=["qa"],
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
    assert "qa" in result["decision_record"]["failed_gates"]
