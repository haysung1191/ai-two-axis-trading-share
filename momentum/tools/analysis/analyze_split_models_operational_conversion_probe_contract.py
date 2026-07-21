from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
CURRENT_STATE_JSON = ROOT / "output" / "split_models_operational_conversion_current_state.json"
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_probe_contract"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Probe Contract",
        "",
        "## Probe Scope",
        "",
        f"- machine entrypoint: `{summary['probe_command']}`",
        f"- expected gate status today: `{summary['gate_status']}`",
        f"- expected blocked exit code: `{summary['exit_code_blocked']}`",
        "",
        "## Required Payload Fields",
        "",
    ]
    for field in summary["required_fields"]:
        lines.append(f"- `{field}`")
    lines.extend(
        [
            "",
            "## Representative Semantics",
            "",
            f"- recommended representative: `{summary['recommended_representative_variant']}`",
            f"- best quality overlay: `{summary['best_quality_variant']}`",
            f"- representative challenger search closed: `{summary['representative_challenger_search_closed']}`",
            f"- representative decision file: `{summary['representative_decision_file']}`",
            f"- representative decision verdict: `{summary['representative_decision_verdict']}`",
            "",
            "## Contract Rule",
            "",
            f"- verdict: `{summary['verdict']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    current_state = _load_json(CURRENT_STATE_JSON)
    required_fields = [
        "gate_status",
        "promotion_status",
        "anchor_variant",
        "best_quality_variant",
        "recommended_representative_variant",
        "representative_challenger_search_closed",
        "challenger_family_count",
        "representative_replacements_found",
        "anchor_mdd_display",
        "baseline_mdd_display",
        "drawdown_gap_vs_baseline_display",
        "representative_decision_file",
        "representative_decision_verdict",
        "primary_read_file",
        "exit_code_open",
        "exit_code_blocked",
        "exit_code_unknown",
    ]

    summary = {
        "probe_contract_version": 1,
        "probe_command": "python tools/analysis/probe_split_models_operational_conversion_gate.py",
        "gate_status": str(current_state["gate_status"]),
        "promotion_status": str(current_state["promotion_status"]),
        "recommended_representative_variant": str(current_state["recommended_representative_variant"]),
        "best_quality_variant": str(current_state["best_quality_variant"]),
        "representative_challenger_search_closed": bool(current_state["representative_challenger_search_closed"]),
        "challenger_family_count": int(current_state["challenger_family_count"]),
        "representative_replacements_found": int(current_state["representative_replacements_found"]),
        "representative_decision_file": str(current_state["representative_decision_file"]),
        "representative_decision_verdict": str(current_state["representative_decision_verdict"]),
        "required_fields": required_fields,
        "exit_code_open": 0,
        "exit_code_blocked": 2,
        "exit_code_unknown": 3,
        "verdict": (
            "downstream consumers may treat probe as the canonical machine-facing summary for gate status and "
            "representative decision. If any required field disappears or changes semantics, update the probe "
            "contract and the smoke/check paths together."
        ),
    }

    (OUTPUT_DIR / "probe_contract_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "probe_contract.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
