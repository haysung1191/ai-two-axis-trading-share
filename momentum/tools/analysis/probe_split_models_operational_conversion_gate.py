from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


CURRENT_STATE_JSON = REPO_ROOT / "output" / "split_models_operational_conversion_current_state.json"

EXIT_CODE_OPEN = 0
EXIT_CODE_BLOCKED = 2
EXIT_CODE_UNKNOWN = 3


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    current_state = _load_json(CURRENT_STATE_JSON)
    gate_status = str(current_state["gate_status"]).upper()

    report = {
        "gate_status": gate_status,
        "promotion_status": str(current_state["promotion_status"]),
        "anchor_variant": str(current_state["anchor_variant"]),
        "best_quality_variant": str(current_state["best_quality_variant"]),
        "recommended_representative_variant": str(current_state["recommended_representative_variant"]),
        "representative_challenger_search_closed": bool(current_state["representative_challenger_search_closed"]),
        "challenger_family_count": int(current_state["challenger_family_count"]),
        "representative_replacements_found": int(current_state["representative_replacements_found"]),
        "anchor_mdd_display": str(current_state["anchor_mdd_display"]),
        "baseline_mdd_display": str(current_state["baseline_mdd_display"]),
        "drawdown_gap_vs_baseline_display": str(current_state["drawdown_gap_vs_baseline_display"]),
        "representative_decision_file": str(current_state["representative_decision_file"]),
        "representative_decision_verdict": str(current_state["representative_decision_verdict"]),
        "primary_read_file": "output/split_models_operational_conversion_current_state.json",
        "exit_code_open": EXIT_CODE_OPEN,
        "exit_code_blocked": EXIT_CODE_BLOCKED,
        "exit_code_unknown": EXIT_CODE_UNKNOWN,
    }
    print(json.dumps(report, indent=2))

    if gate_status == "OPEN":
        raise SystemExit(EXIT_CODE_OPEN)
    if gate_status == "BLOCKED":
        raise SystemExit(EXIT_CODE_BLOCKED)
    raise SystemExit(EXIT_CODE_UNKNOWN)


if __name__ == "__main__":
    main()
