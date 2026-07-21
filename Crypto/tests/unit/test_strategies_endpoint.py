import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


def test_strategies_endpoint_lists_python_strategies() -> None:
    client = TestClient(create_app())
    response = client.get("/api/v1/strategies")
    assert response.status_code == 200
    payload = response.json()
    assert "strategies" in payload
    assert "mean_reversion" in payload["strategies"]


def test_strategy_registry_endpoint_returns_registry_payload(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "strategy_registry.json").write_text(
        json.dumps(
            {
                "strategies": [
                    {
                        "strategy_id": "mean_reversion_approved",
                        "first_seen_run": "run-1",
                        "latest_run": "run-1",
                        "best_sharpe": 1.2,
                        "best_cagr": 0.1,
                        "best_drawdown": 0.2,
                        "runs": [],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    client = TestClient(create_app())
    response = client.get("/api/v1/strategies/registry")
    assert response.status_code == 200
    payload = response.json()
    assert payload["strategies"][0]["strategy_id"] == "mean_reversion_approved"
