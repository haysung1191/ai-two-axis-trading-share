from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.main import create_app


def test_btc_paper_validation_latest_endpoint_reads_latest_run(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "artifacts" / "btc-paper-run"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "btc_paper_validation.json").write_text(
        json.dumps(
            {
                "run_id": "btc-paper-run",
                "generated_at": "2026-04-11T07:00:00+00:00",
                "config": {"symbol": "BTCUSDT", "interval": "4h"},
                "source_analysis": {"final_decision": "carry_forward"},
                "comparison": {"directionally_aligned": True},
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "decision_record.json").write_text(
        json.dumps({"run_id": "btc-paper-run", "decision": "PASS", "summary": "ok"}),
        encoding="utf-8",
    )
    (run_dir / "run_leaderboard.json").write_text(
        json.dumps({"run_id": "btc-paper-run", "entries": [{"strategy_name": "btc"}]}),
        encoding="utf-8",
    )

    client = TestClient(create_app())
    response = client.get("/api/v1/experiments/btc-paper/latest")

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == "btc-paper-run"
    assert payload["config"]["symbol"] == "BTCUSDT"
    assert payload["comparison"]["directionally_aligned"] is True
