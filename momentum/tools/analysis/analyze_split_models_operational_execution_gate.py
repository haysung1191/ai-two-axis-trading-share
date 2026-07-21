from __future__ import annotations

import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


ROOT = REPO_ROOT
STATUS_SNAPSHOT_JSON = (
    ROOT / "output" / "split_models_operational_conversion_status_snapshot" / "status_snapshot_summary.json"
)
SHADOW_RUNTIME_STATUS_JSON = ROOT / "output" / "split_models_shadow" / "shadow_operator_runtime_status.json"
SHADOW_LIVE_READINESS_JSON = ROOT / "output" / "split_models_shadow" / "shadow_live_readiness.json"
OUTPUT_DIR = ROOT / "output" / "split_models_operational_execution_gate"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_markdown(summary: dict[str, object]) -> str:
    lines = [
        "# Split Models Operational Execution Gate",
        "",
        "## Branch Gate",
        "",
        f"- operational branch gate status: `{summary['operational_branch_gate_status']}`",
        f"- operational branch promotion status: `{summary['operational_branch_promotion_status']}`",
        f"- operational branch ready for live autotrade: `{summary['operational_branch_ready_for_live_autotrade']}`",
        "",
        "## Shadow Baseline Gate",
        "",
        f"- shadow baseline variant: `{summary['shadow_baseline_variant']}`",
        f"- shadow live readiness verdict: `{summary['shadow_live_readiness_verdict']}`",
        f"- shadow operator gate verdict: `{summary['shadow_operator_gate_verdict']}`",
        f"- shadow archive stability verdict: `{summary['shadow_archive_stability_verdict']}`",
        f"- shadow ready for live autotrade: `{summary['shadow_ready_for_live_autotrade']}`",
        "",
        "## Current Execution Mode",
        "",
        f"- recommended live execution mode: `{summary['recommended_live_execution_mode']}`",
        f"- execution gate verdict: `{summary['execution_gate_verdict']}`",
        "",
        "## Source Files",
        "",
        f"- operational branch source: `{summary['operational_branch_source_file']}`",
        f"- shadow runtime status source: `{summary['shadow_runtime_status_file']}`",
        f"- shadow live readiness source: `{summary['shadow_live_readiness_file']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    snapshot = _load_json(STATUS_SNAPSHOT_JSON)
    runtime_status = _load_json(SHADOW_RUNTIME_STATUS_JSON)
    live_readiness = _load_json(SHADOW_LIVE_READINESS_JSON)

    operational_branch_ready = str(snapshot["gate_status"]).upper() == "OPEN"
    shadow_ready = (
        str(live_readiness["live_readiness_verdict"]).upper() == "GO"
        and str(runtime_status["operator_gate_verdict"]).upper() == "PASS"
        and str(runtime_status["archive_stability_verdict"]).upper() == "PASS"
    )

    if operational_branch_ready:
        recommended_mode = "operational_branch"
        verdict = "the operational-conversion branch is open, so this branch may own live execution."
    elif shadow_ready:
        recommended_mode = "shadow_baseline_only"
        verdict = (
            "the operational-conversion branch stays blocked_by_drawdown, so do not route live orders to this branch. "
            "If live execution must run now, only the shadow baseline path is currently eligible."
        )
    else:
        recommended_mode = "none"
        verdict = (
            "neither the operational-conversion branch nor the shadow baseline path is eligible for live execution right now."
        )

    summary = {
        "execution_gate_version": 1,
        "operational_branch_gate_status": str(snapshot["gate_status"]),
        "operational_branch_promotion_status": str(snapshot["promotion_status"]),
        "operational_branch_ready_for_live_autotrade": operational_branch_ready,
        "shadow_baseline_variant": str(runtime_status["baseline_variant"]),
        "shadow_live_readiness_verdict": str(live_readiness["live_readiness_verdict"]),
        "shadow_operator_gate_verdict": str(runtime_status["operator_gate_verdict"]),
        "shadow_archive_stability_verdict": str(runtime_status["archive_stability_verdict"]),
        "shadow_ready_for_live_autotrade": shadow_ready,
        "recommended_live_execution_mode": recommended_mode,
        "execution_gate_verdict": verdict,
        "operational_branch_source_file": (
            "output/split_models_operational_conversion_status_snapshot/status_snapshot_summary.json"
        ),
        "shadow_runtime_status_file": "output/split_models_shadow/shadow_operator_runtime_status.json",
        "shadow_live_readiness_file": "output/split_models_shadow/shadow_live_readiness.json",
    }

    (OUTPUT_DIR / "execution_gate_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "execution_gate.md").write_text(_build_markdown(summary), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
