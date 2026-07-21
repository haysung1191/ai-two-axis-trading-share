from pathlib import Path

from app.domains.governance.artifact_store import ArtifactStore
from app.domains.governance.contracts import RunLeaderboard, RunLeaderboardEntry, Spec
from app.domains.governance.run_logger import RunLogger
from app.domains.governance.workflow import GovernanceWorkflow


def test_supervisor_selects_top_k_by_sharpe_then_drawdown(tmp_path: Path) -> None:
    state = {
        "run_id": "run-rank-1",
        "spec": Spec(
            run_goal="rank test",
            context="unit",
            requirements=[],
            metadata={"top_k": 1},
        ).model_dump(mode="json"),
        "run_leaderboard": RunLeaderboard(
            run_id="run-rank-1",
            entries=[
                RunLeaderboardEntry(
                    strategy_name="alpha",
                    sharpe=1.3,
                    cagr=0.1,
                    max_drawdown=0.2,
                    win_rate=0.5,
                    trades=20,
                    qa_passed=True,
                    risk_passed=True,
                    backtest_passed=True,
                    stability_score=0.95,
                    overfitting_flags=[],
                    failed_gates=[],
                ),
                RunLeaderboardEntry(
                    strategy_name="beta",
                    sharpe=1.3,
                    cagr=0.08,
                    max_drawdown=0.1,
                    win_rate=0.45,
                    trades=15,
                    qa_passed=True,
                    risk_passed=True,
                    backtest_passed=True,
                    stability_score=0.90,
                    overfitting_flags=[],
                    failed_gates=[],
                ),
            ],
        ).model_dump(mode="json"),
        "reject_count": 0,
        "iteration": 0,
        "max_iterations": 6,
    }

    workflow = GovernanceWorkflow(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        run_logger=RunLogger(root_dir=tmp_path / "logs"),
        talk_delay_sec=0.0,
    )
    result = workflow._supervisor_node(state)

    assert result["status"] == "APPROVED"
    assert result["approved_strategy"]["winners"][0]["strategy_id"].startswith("beta")
