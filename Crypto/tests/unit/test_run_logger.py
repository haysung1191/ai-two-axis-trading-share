import json
from pathlib import Path

from app.domains.governance.run_logger import RunLogger


def test_run_logger_writes_jsonl_entry(tmp_path: Path) -> None:
    logger = RunLogger(root_dir=tmp_path / "logs")
    run_id = "run-logger-1"
    logger.log_node(
        run_id=run_id,
        agent="QA",
        message="QA completed sandbox checks.",
        action="sandbox smoke test passed",
        input_contract="ImplementationPlan",
        output_contract="QATestReport",
        model_used="qa-model-v1",
        cache_hit=False,
        token_estimate=42,
        decision="PASS",
    )

    log_path = tmp_path / "logs" / f"{run_id}.jsonl"
    assert log_path.exists()

    entry = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert entry["agent"] == "QA"
    assert entry["message"] == "QA completed sandbox checks."
    assert entry["action"] == "sandbox smoke test passed"
    assert entry["decision"] == "PASS"
    assert entry["token_estimate"] == 42
