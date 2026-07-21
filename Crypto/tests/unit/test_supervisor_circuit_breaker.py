from pathlib import Path

from app.domains.governance.artifact_store import ArtifactStore
from app.domains.governance.contracts import Spec
from app.domains.governance.run_logger import RunLogger
from app.domains.governance.workflow import GovernanceWorkflow


def test_circuit_breaker_pauses_after_three_rejects(tmp_path: Path) -> None:
    artifacts = ArtifactStore(root_dir=tmp_path / "artifacts")
    logger = RunLogger(root_dir=tmp_path / "logs")
    workflow = GovernanceWorkflow(artifact_store=artifacts, run_logger=logger)

    spec = Spec(
        run_goal="prove autonomous collaboration",
        context="mvp validation",
        requirements=["must enforce contracts"],
        metadata={"force_reject": True},
    )

    final_state = workflow.run(
        {
            "run_id": "run-cb-1",
            "spec": spec.model_dump(mode="json"),
            "design_spec": None,
            "architecture_plan": None,
            "implementation_plan": None,
            "qa_test_report": None,
            "risk_report": None,
            "backtest_report": None,
            "decision_record": None,
            "pr_package": None,
            "reject_count": 0,
            "iteration": 0,
            "max_iterations": 10,
            "status": "RUNNING",
        }
    )

    assert final_state["status"] == "PAUSED_HUMAN_APPROVAL"
    assert final_state["reject_count"] == 3
    assert final_state["decision_record"]["decision"] == "PAUSE"
