from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_kis_axis_wide_source_export_intake_contract as intake_contract


KST = ZoneInfo("Asia/Seoul")
REPORT_JSON = ROOT / "reports/operations/kis_axis_wide_membership_coverage_progress_latest.json"
REPORT_MD = ROOT / "reports/operations/kis_axis_wide_membership_coverage_progress_latest.md"
MEMBERSHIP_VERIFIER_JSON = ROOT / "reports/operations/kis_pit_membership_verifier_latest.json"
HANDOFF_PACKAGE_JSON = ROOT / "reports/operations/kis_axis_wide_membership_handoff_package_latest.json"
RESPONSE_VALIDATOR_JSON = ROOT / "reports/operations/kis_axis_wide_membership_response_validator_latest.json"
IMPORT_JSON = ROOT / "reports/operations/kis_axis_wide_membership_import_latest.json"
SAFETY = intake_contract.SAFETY


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _plan_by_target(import_report: dict) -> dict[str, dict]:
    return {row.get("target_file", ""): row for row in import_report.get("append_plan", [])}


def _coverage_by_axis(response_validator: dict) -> dict[str, dict]:
    return {row.get("axis", ""): row for row in response_validator.get("replacement_coverage_rows", [])}


def build_report(
    generated_at: str | None = None,
    membership_verifier: dict | None = None,
    handoff_package: dict | None = None,
    response_validator: dict | None = None,
    import_report: dict | None = None,
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    membership_verifier = membership_verifier or _read_json(MEMBERSHIP_VERIFIER_JSON)
    handoff_package = handoff_package or _read_json(HANDOFF_PACKAGE_JSON)
    response_validator = response_validator or _read_json(RESPONSE_VALIDATOR_JSON)
    import_report = import_report or _read_json(IMPORT_JSON)
    plan_by_target = _plan_by_target(import_report)
    coverage_by_axis = _coverage_by_axis(response_validator)
    valid_response_count = len(response_validator.get("valid_rows", []))
    blocked_response_count = len(response_validator.get("blocked_rows", []))
    import_review_ready = response_validator.get("status") == "READY_AXIS_WIDE_MEMBERSHIP_IMPORT_REVIEW"
    import_dry_run_ready = str(import_report.get("status", "")).startswith("DRY_RUN_READY_FOR_AXIS_WIDE_MEMBERSHIP")
    axis_rows = []

    verifier_by_axis = {row.get("axis", ""): row for row in membership_verifier.get("axis_reports", [])}
    request_rows = handoff_package.get("request_rows", [])
    if not request_rows:
        request_rows = [
            {"axis": row.get("axis", ""), "canonical_target_file": row.get("path", "")}
            for row in membership_verifier.get("axis_reports", [])
        ]

    for request in request_rows:
        axis = request.get("axis", "")
        target = request.get("canonical_target_file", "")
        verifier_row = verifier_by_axis.get(axis, {})
        coverage = coverage_by_axis.get(axis, {})
        plan = plan_by_target.get(target, {})
        if verifier_row.get("verified"):
            status = "COMPLETE_OPERATION_READY"
            remaining_action = "None."
        elif import_review_ready and import_dry_run_ready:
            status = "IMPORT_REVIEW_READY"
            remaining_action = "Review and apply guarded import."
        else:
            status = "BLOCK_RESPONSE_REQUIRED"
            remaining_action = "Fill authoritative/licensed membership response rows for this axis."
        axis_rows.append({
            "request_id": request.get("request_id", ""),
            "axis": axis,
            "status": status,
            "canonical_target_file": target,
            "current_row_count": int(request.get("current_row_count", verifier_row.get("row_count", 0)) or 0),
            "current_caveated_row_count": int(request.get("current_caveated_row_count", verifier_row.get("caveated_row_count", 0)) or 0),
            "current_operation_ready_row_count": int(request.get("current_operation_ready_row_count", verifier_row.get("operation_ready_quality_row_count", 0)) or 0),
            "required_replacement_row_count": int(coverage.get("required_replacement_row_count", request.get("current_caveated_row_count", 0)) or 0),
            "valid_replacement_row_count": int(coverage.get("valid_replacement_row_count", 0) or 0),
            "remaining_replacement_row_count": int(coverage.get("remaining_replacement_row_count", request.get("current_caveated_row_count", 0)) or 0),
            "replacement_coverage_sufficient": bool(coverage.get("replacement_coverage_sufficient", False)),
            "import_plan_row_count": int(plan.get("row_count", 0) or 0),
            "remaining_required_action": remaining_action,
        })

    ready_axis_count = sum(1 for row in axis_rows if row["status"] == "COMPLETE_OPERATION_READY")
    blocked_axis_count = sum(1 for row in axis_rows if row["status"] == "BLOCK_RESPONSE_REQUIRED")
    import_review_ready_axis_count = sum(1 for row in axis_rows if row["status"] == "IMPORT_REVIEW_READY")
    blockers = []
    if blocked_axis_count:
        blockers.append("blocked_axes_present")
    if not valid_response_count:
        blockers.append("no_valid_axis_wide_response_rows")
    if ready_axis_count < 4:
        blockers.append("not_all_axes_operation_ready")
    status = "PARTIAL_AXIS_WIDE_MEMBERSHIP_PROGRESS" if import_review_ready_axis_count else "BLOCK_AXIS_WIDE_MEMBERSHIP_COVERAGE_PROGRESS"
    single_next_action = response_validator.get("next_safe_action") or "Fill authoritative/licensed membership response rows for blocked axes."
    if import_review_ready_axis_count:
        single_next_action = "Review and apply axis-wide membership import with the guarded confirmation phrase."

    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "universe_id": "KIS_COMBINED_KRW",
        "status": status,
        "ready_axis_count": ready_axis_count,
        "blocked_axis_count": blocked_axis_count,
        "import_review_ready_axis_count": import_review_ready_axis_count,
        "valid_response_row_count": valid_response_count,
        "blocked_response_row_count": blocked_response_count,
        "axis_rows": axis_rows,
        "blockers": sorted(set(blockers)),
        "single_next_action": single_next_action,
        "non_goals": [
            "does_not_import_rows",
            "does_not_enable_paper_live_broker_submit_or_order_intent",
        ],
        "safety": SAFETY,
    }


def render_md(report: dict) -> str:
    lines = [
        "# KIS Axis-Wide Membership Coverage Progress",
        "",
        "| Axis | Status | Remaining |",
        "|---|---:|---:|",
    ]
    for row in report.get("axis_rows", []):
        lines.append(f"| {row['axis']} | {row['status']} | {row['remaining_replacement_row_count']} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "ready_axis_count": report["ready_axis_count"],
        "blocked_axis_count": report["blocked_axis_count"],
        "valid_response_row_count": report["valid_response_row_count"],
        "latest_json": str(REPORT_JSON),
        "safety": report["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
