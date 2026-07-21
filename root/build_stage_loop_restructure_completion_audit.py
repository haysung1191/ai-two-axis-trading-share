from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(r"C:\AI")
REPORTS = ROOT / "reports" / "operations"
REPORT_JSON = REPORTS / "stage_loop_restructure_completion_audit_latest.json"
REPORT_MD = REPORTS / "stage_loop_restructure_completion_audit_latest.md"

SAFETY = {
    "paper_enabled": False,
    "live_enabled": False,
    "broker_submit_allowed": False,
    "private_submit_used": False,
    "real_orders": 0,
    "order_intent_created": False,
    "pretrade_firewall_default_decision": "BLOCK",
}


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default


def load_supervisor_module():
    path = ROOT / "run_full_pipeline_safe_supervisor.py"
    spec = importlib.util.spec_from_file_location("run_full_pipeline_safe_supervisor_for_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def safety_matches(payload: dict[str, Any]) -> bool:
    observed = payload.get("safety", {}) or {}
    return all(observed.get(key, expected) == expected for key, expected in SAFETY.items())


def build_report(generated_at: str | None = None) -> dict[str, Any]:
    generated_at = generated_at or datetime.now().isoformat(timespec="seconds")
    supervisor = load_supervisor_module()
    stage13 = read_json(REPORTS / "stage13_completion_audit_latest.json", {})
    stage_status = read_json(REPORTS / "full_pipeline_stage_status_latest.json", {})
    direct_next = read_json(REPORTS / "pipeline_direct_next_command_latest.json", {})
    direct_blocker = read_json(REPORTS / "pipeline_direct_blocker_packet_latest.json", {})

    loop_specs = supervisor.loop_specs()
    required_scripts = [spec.script for spec in loop_specs if spec.required]
    optional_scripts = [spec.script for spec in loop_specs if not spec.required]
    stage_by_id = {row.get("id"): row for row in stage_status.get("stages", [])}
    stage13_rows = {row.get("stage_id"): row for row in stage13.get("prompt_to_artifact_checklist", [])}

    checks = [
        {
            "requirement_id": "shadow_paper_removed_from_required_stage_progress",
            "passed": "stage6" not in stage13.get("failed_required_stage_ids", [])
            and "stage7" not in stage13.get("failed_required_stage_ids", [])
            and stage13_rows.get("retired_shadow_paper_state", {}).get("passed") is True,
            "evidence": str(REPORTS / "stage13_completion_audit_latest.json"),
        },
        {
            "requirement_id": "supervisor_required_loops_exclude_shadow_and_paper",
            "passed": "run_stage6_shadow_loop.py" not in required_scripts
            and "run_stage7_local_sim_from_shadow.py" not in required_scripts
            and "run_stage6_shadow_loop.py" in optional_scripts
            and "run_stage7_local_sim_from_shadow.py" in optional_scripts,
            "evidence": str(ROOT / "run_full_pipeline_safe_supervisor.py"),
            "observed": {"required_scripts": required_scripts, "optional_scripts": optional_scripts},
        },
        {
            "requirement_id": "stage_status_marks_shadow_and_paper_optional",
            "passed": stage_by_id.get(6, {}).get("autonomous_action") == "OPTIONAL_DIAGNOSTIC_ONLY_NOT_REQUIRED"
            and stage_by_id.get(7, {}).get("autonomous_action") == "OPTIONAL_DIAGNOSTIC_ONLY_NOT_REQUIRED",
            "evidence": str(REPORTS / "full_pipeline_stage_status_latest.json"),
        },
        {
            "requirement_id": "required_next_gate_is_stage9_live_approval_wait",
            "passed": stage13.get("current_target_stage_id") == 9
            and direct_next.get("status") == "WAITING_FOR_EXACT_LIVE_APPROVAL_OR_NO_SUBMIT_POLICY"
            and "LIVE APPROVE" in str(direct_next.get("next_command", "")),
            "evidence": str(REPORTS / "pipeline_direct_next_command_latest.json"),
        },
        {
            "requirement_id": "direct_blocker_is_stage9_not_shadow_or_kis_export",
            "passed": [
                row.get("axis") for row in direct_blocker.get("direct_blockers", [])
            ]
            == ["PIPELINE_STAGE9"],
            "evidence": str(REPORTS / "pipeline_direct_blocker_packet_latest.json"),
        },
        {
            "requirement_id": "report_only_run_preserved_safety",
            "passed": all(
                safety_matches(payload)
                for payload in [stage13, stage_status, direct_next, direct_blocker]
            ),
            "evidence": "stage13, stage_status, direct_next, direct_blocker safety fields",
        },
        {
            "requirement_id": "canonical_stage_source_exists",
            "passed": Path(stage13.get("canonical_stage_source", "")).exists()
            and Path(stage13.get("stage_policy_implementation", "")).exists(),
            "evidence": stage13.get("canonical_stage_source"),
            "observed": {
                "canonical_stage_source": stage13.get("canonical_stage_source"),
                "stage_policy_implementation": stage13.get("stage_policy_implementation"),
            },
        },
    ]
    missing = [row["requirement_id"] for row in checks if not row["passed"]]
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "objective_restatement": "Remove shadow and paper from required stage/loop progress, and verify the safe report-only loop reaches Stage 9 live approval wait without enabling paper, live, broker submit, or order intent creation.",
        "completion_decision": "COMPLETE" if not missing else "NOT_COMPLETE",
        "prompt_to_artifact_checklist": checks,
        "missing_or_weak_requirements": missing,
        "safety": SAFETY,
    }


def render_md(report: dict[str, Any]) -> str:
    lines = [
        "# Stage/Loop Restructure Completion Audit",
        "",
        f"- Completion: `{report['completion_decision']}`",
        f"- Objective: {report['objective_restatement']}",
        "",
    ]
    for row in report["prompt_to_artifact_checklist"]:
        mark = "PASS" if row["passed"] else "FAIL"
        lines.append(f"- {mark}: `{row['requirement_id']}`")
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"completion_decision": report["completion_decision"], "missing_or_weak_requirements": report["missing_or_weak_requirements"], "latest_json": str(REPORT_JSON)}, ensure_ascii=False, indent=2))
    return 0 if report["completion_decision"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
