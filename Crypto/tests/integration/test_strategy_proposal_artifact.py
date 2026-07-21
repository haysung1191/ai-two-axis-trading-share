from pathlib import Path

from fastapi.testclient import TestClient

from app.core.dependencies import get_governance_run_service_dependency
from app.domains.governance.artifact_store import ArtifactStore
from app.domains.governance.run_logger import RunLogger
from app.domains.governance.service import GovernanceRunService
from app.main import create_app


def test_runs_start_produces_strategy_proposal_artifact(tmp_path: Path) -> None:
    artifact_store = ArtifactStore(root_dir=tmp_path / "artifacts")
    run_logger = RunLogger(root_dir=tmp_path / "logs")
    service = GovernanceRunService(artifact_store=artifact_store, run_logger=run_logger, talk_delay_sec=0.0)

    app = create_app()
    app.dependency_overrides[get_governance_run_service_dependency] = lambda: service

    client = TestClient(app)
    response = client.post(
        "/api/v1/runs/start",
        json={
            "title": "Research-first run",
            "description": "Ensure strategy proposal artifact exists",
            "priority": "medium",
        },
    )

    assert response.status_code == 200
    run_id = response.json()["run_id"]
    proposal_path = tmp_path / "artifacts" / run_id / "strategy_proposal.json"
    assert proposal_path.exists()

