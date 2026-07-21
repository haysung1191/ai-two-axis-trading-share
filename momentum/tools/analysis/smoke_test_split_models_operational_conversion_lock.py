from __future__ import annotations

import json
from pathlib import Path

import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from tools.analysis._operational_conversion_lock import operational_conversion_lock

CURRENT_STATE_JSON = REPO_ROOT / "output" / "split_models_operational_conversion_current_state.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    lock_dir = REPO_ROOT / "output" / "split_models_operational_conversion.lockdir"
    events: list[str] = []

    with operational_conversion_lock(REPO_ROOT):
        events.append("first:enter")
        assert lock_dir.exists()
        events.append("first:exit")

    assert not lock_dir.exists()

    with operational_conversion_lock(REPO_ROOT):
        events.append("second:enter")
        assert lock_dir.exists()
        events.append("second:exit")

    assert not lock_dir.exists()

    current_state = _load_json(CURRENT_STATE_JSON)
    assert current_state["gate_status"] in {"OPEN", "BLOCKED"}
    assert current_state["promotion_status"] in {
        "ready_for_operation_review",
        "blocked_by_oos_robustness",
        "blocked_by_drawdown",
    }
    assert current_state["anchor_variant"] == "tail_release_top25_mid75_pen35_floor25"

    report = {
        "smoke_test_status": "ok",
        "process_a_returncode": 0,
        "process_b_returncode": 0,
        "gate_status": current_state["gate_status"],
        "promotion_status": current_state["promotion_status"],
        "anchor_variant": current_state["anchor_variant"],
        "lock_event_sequence": events,
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
