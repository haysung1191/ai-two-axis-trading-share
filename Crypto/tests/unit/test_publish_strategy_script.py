import json
from pathlib import Path

from scripts.publish_strategy import find_latest_approved_strategy


def test_find_latest_approved_strategy_returns_newest_file(tmp_path: Path) -> None:
    artifacts = tmp_path / "artifacts"
    run_old = artifacts / "run-old"
    run_new = artifacts / "run-new"
    run_old.mkdir(parents=True, exist_ok=True)
    run_new.mkdir(parents=True, exist_ok=True)

    old_file = run_old / "approved_strategy.json"
    new_file = run_new / "approved_strategy.json"
    old_file.write_text(json.dumps({"strategy_id": "old"}), encoding="utf-8")
    new_file.write_text(json.dumps({"strategy_id": "new"}), encoding="utf-8")

    latest = find_latest_approved_strategy(artifacts)
    assert latest == new_file

