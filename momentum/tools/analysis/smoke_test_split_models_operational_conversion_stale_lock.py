from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import time


REPO_ROOT = Path(__file__).resolve().parents[2]
LOCK_DIR = REPO_ROOT / "output" / "split_models_operational_conversion.lockdir"
OWNER_JSON = LOCK_DIR / "owner.json"
SYNC_SCRIPT = REPO_ROOT / "tools" / "analysis" / "sync_split_models_operational_conversion_state.py"
CURRENT_STATE_JSON = REPO_ROOT / "output" / "split_models_operational_conversion_current_state.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    OWNER_JSON.write_text(json.dumps({"pid": 999999, "created_at": 0.0}), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SYNC_SCRIPT)],
        cwd=str(REPO_ROOT),
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        raise SystemExit(result.returncode)

    current_state = _load_json(CURRENT_STATE_JSON)
    assert current_state["gate_status"] in {"OPEN", "BLOCKED"}
    assert current_state["promotion_status"] in {
        "ready_for_operation_review",
        "blocked_by_oos_robustness",
        "blocked_by_drawdown",
    }

    lock_dir_exists_after_sync = LOCK_DIR.exists()
    if lock_dir_exists_after_sync:
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline and LOCK_DIR.exists():
            time.sleep(0.1)
        lock_dir_exists_after_sync = LOCK_DIR.exists()

    report = {
        "smoke_test_status": "ok",
        "sync_stdout": result.stdout.strip(),
        "gate_status": current_state["gate_status"],
        "promotion_status": current_state["promotion_status"],
        "lock_dir_exists_after_sync": lock_dir_exists_after_sync,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
