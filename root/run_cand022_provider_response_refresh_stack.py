from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")
REPORT_DIR = ROOT / "reports/live_readiness"
FORBIDDEN_SCRIPTS = ["broker-submit", "private-submit", "live-order-submit"]
SAFETY = {
    "paper_enabled": False,
    "live_enabled": False,
    "broker_submit_allowed": False,
    "private_submit_used": False,
    "real_orders": 0,
    "order_intent_created": False,
    "pretrade_firewall_default_decision": "BLOCK",
}

SAFE_REFRESH_SCRIPTS = [
    "build_kis_provider_response_validator.py",
    "build_kis_provider_response_evidence_policy.py",
    "build_kis_provider_public_source_probe_report.py",
    "build_kis_official_open_trading_api_source_probe.py",
    "build_kis_provider_response_local_source_audit.py",
    "build_kis_provider_response_gap_matrix.py",
    "build_kis_provider_response_field_closure_plan.py",
    "build_kis_provider_response_draft_workbook.py",
    "build_kis_provider_response_draft_validator.py",
    "build_kis_provider_response_copy_review_packet.py",
    "build_kis_provider_response_external_handoff_bundle.py",
    "build_kis_provider_response_handoff_integrity_verifier.py",
    "build_kis_provider_handoff_delivery_package.py",
    "build_kis_provider_handoff_delivery_verifier.py",
    "build_kis_provider_handoff_request_note.py",
    "build_kis_provider_handoff_email_draft.py",
    "build_kis_provider_returned_handoff_staging_verifier.py",
    "build_kis_provider_returned_to_handoff_copy_review.py",
    "build_kis_provider_external_request_readiness_audit.py",
    "build_kis_provider_external_dispatch_manifest.py",
    "build_kis_provider_external_return_receipt_status.py",
    "build_kis_provider_external_dispatch_send_status.py",
    "run_cand022_provider_return_watch.py",
    "build_cand022_provider_return_watch_process_status.py",
    "ensure_cand022_provider_return_watch_continuity.py",
    "build_kis_provider_external_dispatch_operator_checklist.py",
    "build_kis_provider_handoff_draft_validator.py",
    "build_kis_provider_handoff_fill_progress.py",
    "build_kis_provider_handoff_to_internal_copy_review.py",
    "build_cand022_next_action_router.py",
    "build_cand022_operator_status_brief.py",
    "build_cand022_stage6_user_action_card.py",
    "build_cand022_stage6_two_path_decision_slip.py",
    "build_kis_provider_external_presend_verifier.py",
    "build_kis_provider_external_dispatch_instruction_packet.py",
    "build_cand022_tiny_live_precondition_status.py",
    "build_cand022_operator_decision_packet.py",
    "build_cand022_shadow_only_exception_contract.py",
    "build_cand022_shadow_exception_apply_preflight.py",
    "build_cand022_pretrade_firewall_dry_run.py",
    "build_cand022_current_signal_observation.py",
    "build_cand022_kis_tradable_mapping_audit.py",
    "build_cand022_stage6_prequeue_dry_run.py",
    "build_cand022_stage6_shadow_loop_dry_run.py",
    "build_cand022_stage6_shadow_readiness_packet.py",
    "run_cand022_shadow_only_exception_apply_and_verify.py",
    "build_cand022_stage6_blocker_closure_plan.py",
    "build_cand022_stage6_goal_completion_audit.py",
    "build_cand022_tiny_live_completion_audit.py",
    "build_stage6_operating_status.py",
    "build_kis_pit_intake_import_preflight.py",
    "build_kis_pit_intake_work_order.py",
    "build_kis_pit_source_acquisition_queue.py",
    "build_kis_historical_pit_survivorship_gap_matrix.py",
    "build_kis_axis_wide_membership_handoff_package.py",
    "build_kis_axis_wide_membership_replacement_worklist.py",
    "build_kis_axis_wide_source_export_intake_contract.py",
    "build_krx_data_marketplace_access_probe.py",
    "build_kis_axis_wide_source_export_operator_packet.py",
    "apply_kis_axis_wide_source_exports_to_replacement_worklist.py",
    "build_kis_axis_wide_membership_worklist_fill_progress.py",
    "build_kis_axis_wide_historical_source_feasibility_matrix.py",
    "apply_kis_axis_wide_membership_worklist_to_shards.py",
    "build_kis_axis_wide_membership_response_validator.py",
    "apply_kis_axis_wide_membership_import.py",
    "build_kis_axis_wide_membership_coverage_progress.py",
    "build_kis_pit_next_evidence_fill_card.py",
    "update_kis_pit_intake_row.py",
    "update_kis_pit_source_artifact_registry.py",
    "apply_kis_pit_next_evidence_bundle.py",
    "build_kis_pit_source_artifact_registry_verifier.py",
    "build_kis_pit_intake_source_provenance_verifier.py",
    "apply_kis_pit_intake_canonical_import.py",
    "build_cand022_operator_status_brief.py",
    "build_cand022_stage6_user_action_card.py",
    "build_cand022_stage6_two_path_decision_slip.py",
    "build_cand022_manual_dispatch_execution_slip.py",
    "build_cand022_provider_dispatch_eml_draft.py",
    "build_cand022_dispatch_confirmation_dry_run_from_eml.py",
    "build_cand022_stage6_entry_path_audit.py",
    "build_cand022_stage6_operator_wait_packet.py",
    "build_cand022_dispatch_guidance_consistency_audit.py",
    "build_cand022_dispatch_stale_freeze_surface_audit.py",
    "build_cand022_active_thread_goal_audit.py",
    "build_cand022_blocked_wait_state.py",
    "build_stage13_completion_audit.py",
]

SCRIPT_EXTRA_ARGS = {
    "run_cand022_provider_return_watch.py": ["--cycles", "1", "--sleep-seconds", "0", "--no-refresh"],
    "ensure_cand022_provider_return_watch_continuity.py": ["--start-if-needed"],
    "run_cand022_shadow_only_exception_apply_and_verify.py": [
        "--operator-instruction",
        "APPLY CAND-022 SHADOW_ONLY_EXCEPTION NO_SUBMIT REVIEW_ONLY",
    ],
}

RETIRED_EXTERNAL_DISPATCH_SCRIPTS = [
    "build_cand022_manual_dispatch_execution_slip.py",
    "build_cand022_provider_dispatch_eml_draft.py",
    "build_cand022_dispatch_confirmation_dry_run_from_eml.py",
    "build_cand022_dispatch_guidance_consistency_audit.py",
    "build_cand022_dispatch_stale_freeze_surface_audit.py",
    "build_cand022_blocked_wait_state.py",
]
DUPLICATE_SCRIPTS = [
    "build_cand022_operator_status_brief.py",
    "build_cand022_stage6_two_path_decision_slip.py",
    "build_cand022_stage6_user_action_card.py",
]


def output_paths(run_id: str, dry_run: bool) -> dict[str, Path]:
    stem = "CAND-022_provider_response_refresh_stack"
    if dry_run:
        return {
            "json": REPORT_DIR / f"{stem}.dry_run_latest.json",
            "md": REPORT_DIR / f"{stem}.dry_run_latest.md",
        }
    return {
        "json": REPORT_DIR / f"{stem}.latest.json",
        "md": REPORT_DIR / f"{stem}.latest.md",
    }


def official_route_retired_external_dispatch() -> bool:
    path = ROOT / "reports/operations/kis_official_open_trading_api_route_latest.json"
    if not path.exists():
        return False
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return bool(report.get("pipeline_decision", {}).get("retire_default_external_provider_dispatch"))


def _scripts_for_current_route() -> tuple[list[str], list[str], bool]:
    retired = official_route_retired_external_dispatch()
    scripts = list(SAFE_REFRESH_SCRIPTS)
    skipped: list[str] = []
    if retired:
        skipped = [script for script in RETIRED_EXTERNAL_DISPATCH_SCRIPTS if script in scripts]
        scripts = [script for script in scripts if script not in set(skipped)]
        insert_after = scripts.index("build_kis_official_open_trading_api_source_probe.py") + 1
        scripts.insert(insert_after, "build_kis_pit_membership_verifier.py")
    return scripts, skipped, retired


def build_report(generated_at: str | None = None, dry_run: bool = True, timeout_seconds: int = 120) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    scripts, skipped_scripts, retired = _scripts_for_current_route()
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": "DRY_RUN_READY" if dry_run else "READY_SAFE_REFRESH_STACK",
        "dry_run": dry_run,
        "timeout_seconds": timeout_seconds,
        "official_kis_route_retired_external_dispatch": retired,
        "scripts": scripts,
        "skipped_scripts": skipped_scripts,
        "script_step_count": len(scripts),
        "unique_script_count": len(set(scripts)),
        "duplicate_scripts": DUPLICATE_SCRIPTS,
        "failed_scripts": [],
        "interpretation": "Duplicate script steps are intentional because operator surfaces are refreshed before and after dependency updates.",
        "non_goals": [
            "does_not_enable_paper_live_broker_submit_or_order_intent",
            "does_not_send_external_dispatch",
            "does_not_submit_orders",
        ],
        "safety": SAFETY,
    }


def render_md(report: dict) -> str:
    lines = [
        "# CAND-022 Provider Response Refresh Stack",
        "",
        f"- Status: `{report['status']}`",
        f"- Dry run: `{report['dry_run']}`",
        f"- Script steps: `{report['script_step_count']}`",
        f"- Skipped scripts: `{len(report['skipped_scripts'])}`",
        f"- Official KIS route retired external dispatch: `{report['official_kis_route_retired_external_dispatch']}`",
    ]
    return "\n".join(lines) + "\n"


def write_report(report: dict, dry_run: bool) -> dict[str, Path]:
    run_id = datetime.now(tz=KST).strftime("%Y%m%d_%H%M%S")
    paths = output_paths(run_id, dry_run=dry_run)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths["json"].write_text(json.dumps(report, indent=2), encoding="utf-8")
    paths["md"].write_text(render_md(report), encoding="utf-8")
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=120)
    args = parser.parse_args()
    report = build_report(dry_run=args.dry_run, timeout_seconds=args.timeout_seconds)
    paths = write_report(report, dry_run=args.dry_run)
    print(json.dumps({
        "status": report["status"],
        "dry_run": report["dry_run"],
        "script_step_count": report["script_step_count"],
        "latest_json": str(paths["json"]),
        "safety": report["safety"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
