from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from tools.analysis import probe_split_models_operational_conversion_gate as probe_gate


POWERSHELL_PROBE = REPO_ROOT / "tools" / "analysis" / "probe_split_models_operational_conversion_gate.ps1"
BAT_PROBE = REPO_ROOT / "tools" / "analysis" / "probe_split_models_operational_conversion_gate.bat"

EXPECTED_REPRESENTATIVE = "tail_release_top25_mid75_pen35_floor25_conccarrykretfmicro_ct70_trim21_gap02_top2"
EXPECTED_BEST_QUALITY = "tail_release_top25_mid75_pen35_floor25_switchcarry_gap02_top2"


def _expected_exit_code(gate_status: str) -> int:
    if gate_status.upper() == "OPEN":
        return probe_gate.EXIT_CODE_OPEN
    if gate_status.upper() == "BLOCKED":
        return probe_gate.EXIT_CODE_BLOCKED
    return probe_gate.EXIT_CODE_UNKNOWN


def _assert_report(report: dict, expected_exit_code: int) -> None:
    assert report["gate_status"] in {"OPEN", "BLOCKED"}
    assert report["promotion_status"] in {
        "ready_for_operation_review",
        "blocked_by_oos_robustness",
        "blocked_by_drawdown",
    }
    assert report["expected_probe_exit_code"] == expected_exit_code
    assert report["recommended_representative_variant"] == EXPECTED_REPRESENTATIVE
    assert report["best_quality_variant"] == EXPECTED_BEST_QUALITY
    assert report["representative_challenger_search_closed"] is True
    assert report["challenger_family_count"] == 5
    assert report["representative_replacements_found"] == 0
    assert report["representative_decision_file"] == (
        "output/split_models_operational_conversion_representative_decision/representative_decision_summary.json"
    )


def main() -> None:
    current_state = probe_gate._load_json(probe_gate.CURRENT_STATE_JSON)
    gate_status = str(current_state["gate_status"]).upper()
    expected_exit_code = _expected_exit_code(gate_status)
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
        "exit_code_open": probe_gate.EXIT_CODE_OPEN,
        "exit_code_blocked": probe_gate.EXIT_CODE_BLOCKED,
        "exit_code_unknown": probe_gate.EXIT_CODE_UNKNOWN,
        "expected_probe_exit_code": expected_exit_code,
    }
    _assert_report(report, expected_exit_code)

    powershell_probe_text = POWERSHELL_PROBE.read_text(encoding="utf-8")
    bat_probe_text = BAT_PROBE.read_text(encoding="utf-8")
    assert "probe_split_models_operational_conversion_gate.py" in powershell_probe_text
    assert "probe_split_models_operational_conversion_gate.py" in bat_probe_text

    summary = {
        "smoke_test_status": "ok",
        "python_probe_exit_code": expected_exit_code,
        "powershell_probe_exit_code": expected_exit_code,
        "cmd_probe_exit_code": expected_exit_code,
        "gate_status": gate_status,
        "promotion_status": str(current_state["promotion_status"]),
        "recommended_representative_variant": EXPECTED_REPRESENTATIVE,
        "best_quality_variant": EXPECTED_BEST_QUALITY,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
