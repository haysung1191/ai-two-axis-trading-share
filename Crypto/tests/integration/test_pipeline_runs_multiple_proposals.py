import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.dependencies import get_governance_run_service_dependency
from app.domains.governance.artifact_store import ArtifactStore
from app.domains.governance.run_logger import RunLogger
from app.domains.governance.service import GovernanceRunService
from app.main import create_app


def test_pipeline_runs_multiple_proposals(tmp_path: Path) -> None:
    artifact_store = ArtifactStore(root_dir=tmp_path / "artifacts")
    run_logger = RunLogger(root_dir=tmp_path / "logs")
    service = GovernanceRunService(artifact_store=artifact_store, run_logger=run_logger, talk_delay_sec=0.0)

    app = create_app()
    app.dependency_overrides[get_governance_run_service_dependency] = lambda: service
    client = TestClient(app)

    response = client.post(
        "/api/v1/runs/start",
        json={
            "title": "LLM research pipeline",
            "description": "Run all proposals end-to-end",
            "priority": "high",
        },
    )
    assert response.status_code == 200

    run_id = response.json()["run_id"]
    run_dir = tmp_path / "artifacts" / run_id
    proposal_path = run_dir / "strategy_proposal.json"
    backtests_path = run_dir / "backtest_reports.json"

    assert proposal_path.exists()
    assert backtests_path.exists()

    proposals = json.loads(proposal_path.read_text(encoding="utf-8"))["proposals"]
    reports = json.loads(backtests_path.read_text(encoding="utf-8"))

    assert len(proposals) == 10
    assert len(reports) == 10
