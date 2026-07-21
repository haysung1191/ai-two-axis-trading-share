from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_operational_conversion_promotion_gate"
VERDICT_JSON = (
    ROOT / "output" / "split_models_operational_conversion_verdict" / "operational_conversion_verdict_summary.json"
)
OOS_REGISTRATION_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_oos_registration"
    / "oos_registration_summary.json"
)
OOS_ROBUSTNESS_GATE_JSON = (
    ROOT
    / "output"
    / "split_models_operational_conversion_oos_robustness_gate"
    / "oos_robustness_gate_summary.json"
)


def _pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Conversion Promotion Gate",
        "",
        "## Status",
        "",
        f"- gate status: `{summary['gate_status']}`",
        f"- anchor variant: `{summary['anchor_variant']}`",
        f"- blocking metric: `{summary['blocking_metric']}`",
        f"- current value: `{summary['current_value_display']}`",
        f"- reopen threshold: `{summary['reopen_threshold_display']}`",
        "",
        "## Preconditions",
        "",
    ]
    for item in summary["must_satisfy"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Notes",
            "",
            f"- best quality overlay while blocked: `{summary['best_quality_variant']}`",
            f"- known drag regime: `{summary['drawdown_window_peak']} -> {summary['drawdown_window_trough']}`",
            f"- main symbol drags: `{summary['top_symbol_drags']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    verdict = _load_json(VERDICT_JSON)
    oos_registration = _load_json(OOS_REGISTRATION_JSON)
    oos_robustness_gate = _load_json(OOS_ROBUSTNESS_GATE_JSON) if OOS_ROBUSTNESS_GATE_JSON.exists() else {}
    threshold = float(verdict["anchor_mdd"])
    baseline_mdd = float(verdict["baseline_mdd"])
    oos_registered = oos_registration.get("status") == "REGISTERED_FOR_OOS_ROBUSTNESS"
    oos_ready = oos_robustness_gate.get("promotion_decision") == "READY_FOR_OPERATION_REVIEW"
    summary = {
        "gate_status": "OPEN" if oos_ready else "BLOCKED",
        "anchor_variant": str(verdict["anchor_variant"]),
        "blocking_metric": "none" if oos_ready else "oos_robustness_validation" if oos_registered else "max_drawdown",
        "current_value": float(oos_registration["metrics"]["mdd"]) if oos_ready else float(verdict["anchor_mdd"]),
        "current_value_display": _pct(float(oos_registration["metrics"]["mdd"]))
        if oos_ready
        else _pct(float(verdict["anchor_mdd"])),
        "reopen_threshold": baseline_mdd if oos_ready else threshold,
        "reopen_threshold_display": "passed" if oos_ready else f">{_pct(threshold)}",
        "baseline_reference_display": _pct(baseline_mdd),
        "drawdown_gap_vs_baseline_display": _pct(float(verdict["drawdown_gap_vs_baseline"])),
        "must_satisfy": [
            *(
                []
                if oos_ready
                else list(oos_registration["required_next_gates"])
                if oos_registered
                else [
                    f"improve MDD above {_pct(threshold)}",
                    "keep negative walk-forward windows at 0",
                    "preserve the current branch as the best nearby anchor or replace it with a better one",
                ]
            ),
        ],
        "oos_registered_candidate_id": str(oos_registration.get("candidate_id") or ""),
        "oos_registered_variant": str(oos_registration.get("variant") or ""),
        "oos_registration_status": str(oos_registration.get("status") or ""),
        "oos_robustness_gate_decision": str(oos_robustness_gate.get("gate_decision") or ""),
        "oos_promotion_decision": str(oos_robustness_gate.get("promotion_decision") or ""),
        "best_quality_variant": str(verdict["best_quality_variant"]),
        "drawdown_window_peak": str(verdict["drawdown_window_peak"]),
        "drawdown_window_trough": str(verdict["drawdown_window_trough"]),
        "top_symbol_drags": str(verdict["top_symbol_drags"]),
        "verdict_source": "operational_conversion_verdict_summary.json",
    }

    (OUTPUT_DIR / "promotion_gate_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "promotion_gate.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
