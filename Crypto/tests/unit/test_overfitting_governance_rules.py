from pathlib import Path

from app.domains.governance.artifact_store import ArtifactStore
from app.domains.governance.contracts import RunLeaderboard, RunLeaderboardEntry, Spec
from app.domains.governance.risk_policy import RiskPolicy
from app.domains.governance.run_logger import RunLogger
from app.domains.governance.workflow import GovernanceWorkflow


def test_risk_policy_enforces_is_oos_walk_forward_and_fee_slippage_rules() -> None:
    policy = RiskPolicy(rules_path=Path("app/domains/governance/rules/risk_rules.yml"))
    metadata = {
        "strategy_name": "mean_reversion",
        "position_size": 0.1,
        "expected_max_drawdown": 0.05,
        "min_sharpe": 1.0,
        "max_drawdown": 0.2,
        "min_win_rate": 0.5,
        "min_cagr": 0.05,
        # fee_bps/slippage_bps intentionally omitted
    }
    backtest = {
        "trades": 20,
        "sharpe": 1.5,
        "max_drawdown": 0.1,
        "win_rate": 0.6,
        "cagr": 0.1,
    }
    overfitting = {
        "passed": True,
        "sensitivity_max_drift": 0.1,
        "is_metrics": {"sharpe": 1.6},
        "oos_metrics": {},
        "walk_forward": [],
    }

    _, violations, failed_gates = policy.evaluate(metadata, backtest, overfitting)

    assert "overfitting_is_oos_split" in failed_gates
    assert "overfitting_walk_forward" in failed_gates
    assert "execution_model" in failed_gates
    assert any("fee/slippage model required" in v for v in violations)


def test_supervisor_rejects_on_overfitting_flags_or_low_stability(tmp_path: Path) -> None:
    workflow = GovernanceWorkflow(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        run_logger=RunLogger(root_dir=tmp_path / "logs"),
        talk_delay_sec=0.0,
    )
    state = {
        "run_id": "run-overfit-reject",
        "spec": Spec(
            run_goal="overfitting guard",
            context="unit test",
            requirements=[],
            metadata={"top_k": 1},
        ).model_dump(mode="json"),
        "run_leaderboard": RunLeaderboard(
            run_id="run-overfit-reject",
            entries=[
                RunLeaderboardEntry(
                    strategy_name="flagged",
                    sharpe=2.0,
                    cagr=0.2,
                    max_drawdown=0.05,
                    win_rate=0.7,
                    trades=20,
                    qa_passed=True,
                    risk_passed=True,
                    backtest_passed=True,
                    stability_score=0.95,
                    overfitting_flags=["unstable_parameters"],
                    failed_gates=[],
                ),
                RunLeaderboardEntry(
                    strategy_name="low_stability",
                    sharpe=1.8,
                    cagr=0.15,
                    max_drawdown=0.08,
                    win_rate=0.65,
                    trades=20,
                    qa_passed=True,
                    risk_passed=True,
                    backtest_passed=True,
                    stability_score=0.2,
                    overfitting_flags=[],
                    failed_gates=[],
                ),
            ],
        ).model_dump(mode="json"),
        "reject_count": 0,
        "iteration": 0,
        "max_iterations": 6,
    }

    result = workflow._supervisor_node(state)

    assert result["status"] == "REJECTED"
    assert result["decision_record"]["decision"] == "FAIL"
    assert "overfitting_flags" in result["decision_record"]["failed_gates"]
    assert "stability_score" in result["decision_record"]["failed_gates"]
