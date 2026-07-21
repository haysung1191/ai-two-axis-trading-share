from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")

SAFETY = {
    "paper_enabled": False,
    "live_enabled": False,
    "broker_submit_allowed": False,
    "private_submit_used": False,
    "real_orders": 0,
    "order_intent_created": False,
    "pretrade_firewall_default_decision": "BLOCK",
}

LATEST_JSON = ROOT / "reports/operations/stage13_completion_audit_latest.json"
LATEST_MD = ROOT / "reports/operations/stage13_completion_audit_latest.md"

RETIRED_STAGE_BLOCKERS = {
    "stage6_shadow_ready_and_passed",
    "stage6_shadow_queue_allowed_or_shadow_passed",
    "stage6_queue_allowed_or_shadow_passed",
    "paper_or_broker_paper_not_approved",
}

LIVE_PROMOTION_CAVEAT_BLOCKERS = {
    "artifact_path_missing",
    "authoritative_pit_membership_history_missing_for_kis_combined",
    "axis_wide_source_export_inbox_empty",
    "axis_wide_source_export_intake_blocked",
    "axis_wide_source_export_manifest_row_upsert_blocked",
    "canonical_membership_evidence_quality_caveated_not_operation_ready",
    "evidence_quality_missing",
    "expected_exactly_one_intake_row",
    "historical_pit_survivorship_not_verified",
    "intake_import_preflight_blocked",
    "intake_row_number_out_of_range",
    "intake_row_update_blocked",
    "kis_pit_manifest_operation_ready",
    "membership_files_operation_ready",
    "membership_verifier_not_operation_ready",
    "next_evidence_bundle_apply_blocked",
    "registry_update_blocked",
    "snapshot_id_missing",
    "source_missing",
    "upgrade_plan_not_ready_for_registry_review",
}

RETIRED_EXTERNAL_PROVIDER_BLOCKERS = {
    "blocked_wait_state_ready",
    "dispatch_guidance_consistency_passed",
    "dispatch_sent_confirmation_recorded",
    "dispatch_stale_freeze_surface_audit_passed",
    "frozen_active_send_files_verified",
    "instruction_packet_matches_frozen_active_send_files",
    "instruction_return_contract_matches_receipt",
    "manual_dispatch_execution_slip_markdown_surfaces_safe_flow",
    "manual_dispatch_execution_slip_ready",
    "manual_dispatch_packet_ready",
    "next_action_router_dispatch_action_safety_locked",
    "next_action_router_dispatch_matches_frozen_active_send_files",
    "next_action_router_surfaces_shadow_exception_review_only",
    "next_action_router_waits_for_external_dispatch_or_provider_rows",
    "operator_checklist_copy_review_gate_ready",
    "operator_checklist_helper_first_ready",
    "operator_status_brief_markdown_surfaces_active_send_hashes",
    "operator_status_brief_surfaces_manual_dispatch_slip",
    "presend_verified",
    "provider_return_watch_process_not_ready",
    "returned_provider_csvs_received",
    "source_backed_rows_complete",
    "stage6_operator_wait_packet_ready",
    "top_level_next_action_points_to_instruction_packet",
}


def read_json(path: Path, default: dict) -> dict:
    try:
        text = path.read_text(encoding="utf-8-sig")
        if not text.strip():
            return default
        return json.loads(text)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError:
        return default


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def _safe(*payloads: dict) -> bool:
    for payload in payloads:
        observed = dict(payload.get("safety", {}) or {})
        for key, value in SAFETY.items():
            if observed.get(key, value) != value:
                return False
    return True


def _stage1_row(
    tiny_live: dict,
    kis_historical_gap_matrix: dict,
    kis_source_acquisition_queue: dict,
    kis_intake_import_preflight: dict,
    kis_intake_work_order: dict,
    kis_next_evidence_fill_card: dict,
    kis_next_evidence_bundle_apply: dict,
    kis_intake_row_update: dict,
    kis_source_artifact_registry_update: dict,
    kis_source_artifact_registry: dict,
    kis_intake_source_provenance: dict,
    kis_canonical_import_apply: dict,
    kis_axis_wide_membership_handoff_package: dict,
    kis_axis_wide_membership_response_validator: dict,
    kis_axis_wide_membership_import: dict,
    kis_axis_wide_membership_coverage_progress: dict,
    kis_axis_wide_membership_worklist_fill_progress: dict,
    kis_axis_wide_historical_source_feasibility_matrix: dict,
    kis_axis_wide_source_export_intake_contract: dict,
    kis_axis_wide_source_export_inbox_status: dict,
    kis_axis_wide_source_export_next_command: dict,
    krx_data_marketplace_access_probe: dict,
    kis_axis_wide_source_export_operator_packet: dict,
    kis_axis_wide_source_exports_to_replacement_worklist: dict,
    kis_axis_wide_membership_worklist_to_shards: dict,
    kis_operation_ready_manifest: dict,
) -> dict:
    failed = tiny_live.get("failed_required_check_ids", [])
    observed = {
        "failed_required_check_ids": failed,
        "historical_gap_matrix_status": kis_historical_gap_matrix.get("status"),
        "historical_gap_first_blocked_gate": (
            kis_historical_gap_matrix.get("gate_summary", {}) or {}
        ).get("first_blocked_gate_id"),
        "source_acquisition_queue_counts": kis_source_acquisition_queue.get("queue_counts", {}),
        "intake_import_preflight_status": kis_intake_import_preflight.get("status"),
        "intake_import_ready_row_count": kis_intake_import_preflight.get("ready_row_count"),
        "intake_import_blocked_row_count": kis_intake_import_preflight.get("blocked_row_count"),
        "intake_work_order_status": kis_intake_work_order.get("status"),
        "intake_work_order_minimal_blocked_task_count": kis_intake_work_order.get("minimal_cand022_blocked_task_count"),
        "next_evidence_fill_card_status": kis_next_evidence_fill_card.get("status"),
        "next_evidence_fill_card_queue_id": kis_next_evidence_fill_card.get("queue_id"),
        "next_evidence_fill_card_symbol": kis_next_evidence_fill_card.get("symbol"),
        "next_evidence_bundle_apply_status": kis_next_evidence_bundle_apply.get("status"),
        "next_evidence_bundle_files_mutated": bool(kis_next_evidence_bundle_apply.get("files_mutated", False)),
        "intake_row_update_status": kis_intake_row_update.get("status"),
        "intake_row_update_file_mutated": bool(kis_intake_row_update.get("intake_file_mutated", False)),
        "source_artifact_registry_update_status": kis_source_artifact_registry_update.get("status"),
        "source_artifact_registry_update_file_mutated": bool(kis_source_artifact_registry_update.get("registry_file_mutated", False)),
        "source_artifact_registry_status": kis_source_artifact_registry.get("status"),
        "source_artifact_registry_row_count": kis_source_artifact_registry.get("registry_row_count"),
        "intake_source_provenance_status": kis_intake_source_provenance.get("status"),
        "intake_source_provenance_blocked_ready_row_count": kis_intake_source_provenance.get("blocked_ready_row_count"),
        "canonical_import_apply_status": kis_canonical_import_apply.get("status"),
        "canonical_import_files_mutated": bool(kis_canonical_import_apply.get("canonical_files_mutated", False)),
        "axis_wide_membership_handoff_status": kis_axis_wide_membership_handoff_package.get("status"),
        "axis_wide_membership_handoff_request_count": kis_axis_wide_membership_handoff_package.get("request_count"),
        "axis_wide_membership_response_validator_status": kis_axis_wide_membership_response_validator.get("status"),
        "axis_wide_membership_response_valid_row_count": kis_axis_wide_membership_response_validator.get("valid_row_count"),
        "axis_wide_membership_response_blocked_row_count": kis_axis_wide_membership_response_validator.get("blocked_row_count"),
        "axis_wide_membership_response_replacement_coverage_sufficient": bool(kis_axis_wide_membership_response_validator.get("replacement_coverage_sufficient", False)),
        "axis_wide_membership_response_replacement_coverage_rows": kis_axis_wide_membership_response_validator.get("replacement_coverage_rows", []),
        "axis_wide_membership_import_status": kis_axis_wide_membership_import.get("status"),
        "axis_wide_membership_import_canonical_files_mutated": bool(kis_axis_wide_membership_import.get("canonical_files_mutated", False)),
        "axis_wide_membership_coverage_progress_status": kis_axis_wide_membership_coverage_progress.get("status"),
        "axis_wide_membership_coverage_ready_axis_count": kis_axis_wide_membership_coverage_progress.get("ready_axis_count"),
        "axis_wide_membership_coverage_blocked_axis_count": kis_axis_wide_membership_coverage_progress.get("blocked_axis_count"),
        "axis_wide_membership_coverage_valid_response_row_count": kis_axis_wide_membership_coverage_progress.get("valid_response_row_count"),
        "axis_wide_membership_coverage_blocked_response_row_count": kis_axis_wide_membership_coverage_progress.get("blocked_response_row_count"),
        "axis_wide_membership_worklist_fill_status": kis_axis_wide_membership_worklist_fill_progress.get("status"),
        "axis_wide_membership_worklist_complete_row_count": kis_axis_wide_membership_worklist_fill_progress.get("complete_row_count"),
        "axis_wide_membership_worklist_blocked_row_count": kis_axis_wide_membership_worklist_fill_progress.get("blocked_row_count"),
        "axis_wide_membership_worklist_completion_ratio": kis_axis_wide_membership_worklist_fill_progress.get("completion_ratio"),
        "axis_wide_historical_source_feasibility_status": kis_axis_wide_historical_source_feasibility_matrix.get("status"),
        "axis_wide_historical_source_direct_operation_ready_source_count": kis_axis_wide_historical_source_feasibility_matrix.get("direct_operation_ready_source_count"),
        "axis_wide_historical_source_promising_source_count": kis_axis_wide_historical_source_feasibility_matrix.get("promising_source_count"),
        "axis_wide_source_export_intake_status": kis_axis_wide_source_export_intake_contract.get("status"),
        "axis_wide_source_export_intake_valid_export_count": kis_axis_wide_source_export_intake_contract.get("valid_export_count"),
        "axis_wide_source_export_intake_manifest_path": kis_axis_wide_source_export_intake_contract.get("manifest_path"),
        "axis_wide_source_export_inbox_status": kis_axis_wide_source_export_inbox_status.get("status"),
        "axis_wide_source_export_inbox_actionable_file_count": kis_axis_wide_source_export_inbox_status.get("actionable_file_count"),
        "axis_wide_source_export_inbox_unreferenced_normalized_count": kis_axis_wide_source_export_inbox_status.get("unreferenced_normalized_export_count"),
        "axis_wide_source_export_inbox_unreferenced_raw_count": kis_axis_wide_source_export_inbox_status.get("unreferenced_raw_or_unknown_export_count"),
        "axis_wide_source_export_next_command_status": kis_axis_wide_source_export_next_command.get("status"),
        "axis_wide_source_export_next_command_kind": kis_axis_wide_source_export_next_command.get("command_kind"),
        "krx_data_marketplace_access_probe_status": krx_data_marketplace_access_probe.get("status"),
        "krx_data_marketplace_access_probe_operation_ready": bool(krx_data_marketplace_access_probe.get("operation_ready", False)),
        "axis_wide_source_export_operator_packet_status": kis_axis_wide_source_export_operator_packet.get("status"),
        "axis_wide_source_export_operator_packet_valid_export_count": kis_axis_wide_source_export_operator_packet.get("valid_export_count"),
        "axis_wide_source_exports_to_worklist_status": kis_axis_wide_source_exports_to_replacement_worklist.get("status"),
        "axis_wide_source_exports_to_worklist_matched_row_count": kis_axis_wide_source_exports_to_replacement_worklist.get("matched_worklist_row_count"),
        "axis_wide_source_exports_to_worklist_unmatched_row_count": kis_axis_wide_source_exports_to_replacement_worklist.get("unmatched_worklist_row_count"),
        "axis_wide_source_exports_to_worklist_coverage_ratio": kis_axis_wide_source_exports_to_replacement_worklist.get("coverage_ratio"),
        "axis_wide_source_exports_to_worklist_full_coverage_ready": bool(kis_axis_wide_source_exports_to_replacement_worklist.get("full_coverage_ready", False)),
        "axis_wide_source_exports_to_worklist_mutated": bool(kis_axis_wide_source_exports_to_replacement_worklist.get("worklist_mutated", False)),
        "axis_wide_membership_worklist_to_shards_status": kis_axis_wide_membership_worklist_to_shards.get("status"),
        "axis_wide_membership_worklist_to_shards_mutated": bool(kis_axis_wide_membership_worklist_to_shards.get("response_shards_mutated", False)),
        "operation_ready_manifest_status": kis_operation_ready_manifest.get("status"),
        "operation_ready_manifest_blockers": kis_operation_ready_manifest.get("blockers", []),
    }
    missing = []
    missing.extend(kis_historical_gap_matrix.get("remaining_blockers", []))
    missing.extend(kis_intake_import_preflight.get("blockers", []))
    missing.extend(kis_next_evidence_bundle_apply.get("blockers", []))
    missing.extend(kis_intake_row_update.get("blockers", []))
    missing.extend(kis_source_artifact_registry_update.get("blockers", []))
    missing.extend(kis_source_artifact_registry.get("blockers", []))
    missing.extend(kis_intake_source_provenance.get("blockers", []))
    missing.extend(kis_canonical_import_apply.get("blockers", []))
    missing.extend(kis_operation_ready_manifest.get("blockers", []))
    status_to_blocker = {
        "BLOCK_INTAKE_IMPORT_PREFLIGHT": "intake_import_preflight_blocked",
        "BLOCK_INTAKE_WORK_ORDER_OPEN": "intake_work_order_open",
        "BLOCK_KIS_PIT_NEXT_EVIDENCE_BUNDLE": "next_evidence_bundle_apply_blocked",
        "BLOCK_INTAKE_ROW_UPDATE": "intake_row_update_blocked",
        "BLOCK_SOURCE_ARTIFACT_REGISTRY_UPDATE": "source_artifact_registry_update_blocked",
        "BLOCK_SOURCE_ARTIFACT_REGISTRY": "source_artifact_registry_blocked",
        "BLOCK_INTAKE_SOURCE_PROVENANCE": "intake_source_provenance_blocked",
        "BLOCK_CANONICAL_IMPORT_APPLY": "canonical_import_apply_blocked",
    }
    for payload in [
        kis_intake_import_preflight,
        kis_intake_work_order,
        kis_next_evidence_bundle_apply,
        kis_intake_row_update,
        kis_source_artifact_registry_update,
        kis_source_artifact_registry,
        kis_intake_source_provenance,
        kis_canonical_import_apply,
    ]:
        blocker = status_to_blocker.get(payload.get("status"))
        if blocker:
            missing.append(blocker)
    for key in [
        "kis_pit_manifest_operation_ready",
        "membership_files_operation_ready",
        "historical_pit_survivorship_not_verified",
        "axis_wide_source_export_inbox_empty",
        "axis_wide_source_export_intake_blocked",
        "axis_wide_source_export_manifest_row_upsert_blocked",
        "authoritative_pit_membership_history_missing_for_kis_combined",
    ]:
        if key in failed or key.startswith(("historical", "axis", "authoritative")):
            missing.append(key)
    passed = not any(
        item in failed
        for item in ["kis_pit_manifest_operation_ready", "membership_files_operation_ready"]
    )
    return {
        "stage_id": "stage1",
        "name": "Data Readiness / Universe Qualification",
        "required_for_stage13": True,
        "passed": passed,
        "evidence": r"C:\AI\reports\live_readiness\CAND-022_tiny_live_completion_audit.latest.json",
        "observed": observed,
        "missing_or_blocked": sorted(set(missing)),
    }


def _next_action(
    active_audit: dict,
    operator_status_brief: dict,
    kis_source_acquisition_queue: dict,
    kis_axis_wide_membership_handoff_package: dict,
    kis_axis_wide_membership_response_validator: dict,
    kis_axis_wide_membership_coverage_progress: dict,
    kis_axis_wide_source_export_operator_packet: dict,
) -> str:
    if (
        kis_axis_wide_membership_response_validator.get("status")
        == "READY_AXIS_WIDE_MEMBERSHIP_IMPORT_REVIEW"
    ):
        return kis_axis_wide_membership_coverage_progress.get(
            "single_next_action",
            "Review and apply axis-wide membership import with the guarded confirmation phrase.",
        )
    if kis_axis_wide_source_export_operator_packet.get("status") == "READY_OPERATOR_SOURCE_EXPORT_PACKET":
        return kis_axis_wide_source_export_operator_packet.get(
            "single_next_action",
            "use operator packet for source export intake",
        )
    if (
        kis_axis_wide_membership_response_validator.get("status")
        == "BLOCK_AXIS_WIDE_MEMBERSHIP_RESPONSE"
        and kis_axis_wide_membership_handoff_package.get("status")
        == "READY_AXIS_WIDE_MEMBERSHIP_HANDOFF_PACKAGE"
        and kis_axis_wide_membership_response_validator
    ):
        return (
            "Add a reviewed normalized KRX or licensed vendor CSV under "
            "axis_wide_source_exports, replace the example manifest row, then run "
            "the intake contract validator."
        )
    if kis_source_acquisition_queue.get("single_next_action"):
        return kis_source_acquisition_queue["single_next_action"]
    if operator_status_brief.get("single_next_action"):
        return operator_status_brief["single_next_action"]
    return active_audit.get(
        "single_next_action",
        "Add a reviewed normalized KRX or licensed vendor CSV under axis_wide_source_exports, replace the example manifest row, then run the intake contract validator.",
    )


def _axis_wide_source_export_waiting_for_input(
    kis_axis_wide_source_export_inbox_status: dict,
    kis_axis_wide_source_export_next_command: dict,
    krx_data_marketplace_access_probe: dict,
    kis_axis_wide_source_export_operator_packet: dict,
) -> bool:
    return (
        kis_axis_wide_source_export_operator_packet.get("status") == "READY_OPERATOR_SOURCE_EXPORT_PACKET"
        and kis_axis_wide_source_export_inbox_status.get("status") == "BLOCK_NO_SOURCE_EXPORT_FILES_IN_INBOX"
        and kis_axis_wide_source_export_next_command.get("status") == "BLOCK_NO_ACTIONABLE_SOURCE_EXPORT_FILE"
        and not bool(krx_data_marketplace_access_probe.get("operation_ready", False))
    )


def _bithumb_axis_row(
    bithumb_oos_walkforward: dict,
    bithumb_nonzero_signal_scout: dict,
    bithumb_orca_oos_family_review: dict,
    bithumb_gatekeeper_review_packet: dict,
    bithumb_shadow_preflight: dict,
) -> dict:
    oos_status = bithumb_oos_walkforward.get("status")
    scout_status = bithumb_nonzero_signal_scout.get("status")
    gatekeeper_status = bithumb_gatekeeper_review_packet.get("status")
    shadow_status = bithumb_shadow_preflight.get("status")
    oos_pass = oos_status == "OOS_WALKFORWARD_PASS"
    natural_signal_ready = scout_status == "NONZERO_SIGNAL_CANDIDATE_READY_FOR_REVIEW"
    missing = []
    if not oos_pass:
        missing.append("bithumb_oos_walkforward_not_passed")
    if not natural_signal_ready:
        missing.extend(bithumb_nonzero_signal_scout.get("blockers", []))
    if gatekeeper_status and gatekeeper_status != "READY_FOR_HUMAN_GATEKEEPER_REVIEW":
        missing.append("bithumb_gatekeeper_review_packet_not_ready")
        missing.extend(bithumb_gatekeeper_review_packet.get("blockers", []))
    if shadow_status and shadow_status != "READY_FOR_SEPARATE_SHADOW_REGISTRATION_REVIEW":
        missing.extend(bithumb_shadow_preflight.get("blockers", []))
    return {
        "stage_id": "axis_bithumb_krw",
        "name": "BITHUMB_KRW Axis Current-Actionable State",
        "required_for_stage13": False,
        "passed": oos_pass and natural_signal_ready and not missing,
        "evidence": r"C:\AI\reports\operations\bithumb_current_actionable_nonzero_signal_scout_latest.json",
        "observed": {
            "oos_status": oos_status,
            "oos_candidate_count": bithumb_oos_walkforward.get("candidate_count"),
            "oos_evaluated_count": (bithumb_oos_walkforward.get("aggregate", {}) or {}).get("evaluated_count"),
            "oos_pass_count": (bithumb_oos_walkforward.get("aggregate", {}) or {}).get("pass_count"),
            "nonzero_signal_status": scout_status,
            "nonzero_signal_evaluated_candidate_count": bithumb_nonzero_signal_scout.get("evaluated_candidate_count"),
            "nonzero_signal_triggered_candidate_count": bithumb_nonzero_signal_scout.get("triggered_candidate_count"),
            "top_triggered_candidate": bithumb_nonzero_signal_scout.get("top_triggered_candidate"),
            "orca_oos_family_review_status": bithumb_orca_oos_family_review.get("status"),
            "orca_oos_family_pass_candidate_count": bithumb_orca_oos_family_review.get("oos_pass_candidate_count"),
            "orca_oos_family_distinct_parameter_count": bithumb_orca_oos_family_review.get("distinct_parameter_count"),
            "gatekeeper_review_packet_status": gatekeeper_status,
            "gatekeeper_review_packet_candidate_id": bithumb_gatekeeper_review_packet.get("candidate_id"),
            "gatekeeper_review_packet_selected_evidence_type": bithumb_gatekeeper_review_packet.get("selected_evidence_type"),
            "gatekeeper_review_packet_blockers": bithumb_gatekeeper_review_packet.get("blockers", []),
            "shadow_preflight_status": shadow_status,
            "shadow_preflight_candidate_id": bithumb_shadow_preflight.get("candidate_id"),
            "shadow_preflight_blockers": bithumb_shadow_preflight.get("blockers", []),
        },
        "missing_or_blocked": sorted(set(missing)),
    }


def _axis_next_actions(kis_next_action: str, bithumb_axis_row: dict) -> dict:
    bithumb_blockers = set(bithumb_axis_row.get("missing_or_blocked", []))
    if "HUMAN_GATEKEEPER_SHADOW_DECISION_INVALID" in bithumb_blockers:
        candidate_id = bithumb_axis_row["observed"].get("shadow_preflight_candidate_id") or "the current candidate"
        bithumb_next = f"Record a fresh human shadow-review decision for {candidate_id}; the existing decision points to a stale candidate."
    elif "HUMAN_GATEKEEPER_SHADOW_DECISION_MISSING" in bithumb_blockers:
        candidate_id = bithumb_axis_row["observed"].get("shadow_preflight_candidate_id") or "the current candidate"
        bithumb_next = f"Record a human shadow-review decision for {candidate_id}; this does not enable paper, live, broker submit, or real orders."
    elif bithumb_axis_row["observed"].get("nonzero_signal_triggered_candidate_count", 0):
        bithumb_next = "Review the top natural nonzero Bithumb signal candidate for shadow registration."
    elif bithumb_axis_row["observed"].get("oos_status") == "OOS_WALKFORWARD_PASS":
        bithumb_next = "Wait for a natural Bithumb nonzero signal or improve OOS pass candidates without threshold weakening."
    else:
        bithumb_next = "Repair Bithumb current-actionable OOS candidates before shadow review."
    return {
        "KIS_COMBINED_KRW": kis_next_action,
        "BITHUMB_KRW": bithumb_next,
    }


def build_report(
    generated_at: str,
    *,
    active_audit: dict,
    tiny_live: dict,
    wait_state: dict,
    watcher_process_status: dict,
    transition: dict,
    stage6_entry: dict | None = None,
    official_kis_route: dict | None = None,
    operator_status_brief: dict | None = None,
    kis_historical_gap_matrix: dict | None = None,
    kis_source_acquisition_queue: dict | None = None,
    kis_intake_import_preflight: dict | None = None,
    kis_intake_work_order: dict | None = None,
    kis_next_evidence_fill_card: dict | None = None,
    kis_next_evidence_bundle_apply: dict | None = None,
    kis_intake_row_update: dict | None = None,
    kis_source_artifact_registry_update: dict | None = None,
    kis_source_artifact_registry: dict | None = None,
    kis_intake_source_provenance: dict | None = None,
    kis_canonical_import_apply: dict | None = None,
    kis_axis_wide_membership_handoff_package: dict | None = None,
    kis_axis_wide_membership_response_validator: dict | None = None,
    kis_axis_wide_membership_import: dict | None = None,
    kis_axis_wide_membership_coverage_progress: dict | None = None,
    kis_axis_wide_membership_worklist_fill_progress: dict | None = None,
    kis_axis_wide_historical_source_feasibility_matrix: dict | None = None,
    kis_axis_wide_source_export_intake_contract: dict | None = None,
    kis_axis_wide_source_export_inbox_status: dict | None = None,
    kis_axis_wide_source_export_next_command: dict | None = None,
    krx_data_marketplace_access_probe: dict | None = None,
    kis_axis_wide_source_export_operator_packet: dict | None = None,
    kis_axis_wide_source_exports_to_replacement_worklist: dict | None = None,
    kis_axis_wide_membership_worklist_to_shards: dict | None = None,
    kis_operation_ready_manifest: dict | None = None,
    bithumb_oos_walkforward: dict | None = None,
    bithumb_nonzero_signal_scout: dict | None = None,
    bithumb_orca_oos_family_review: dict | None = None,
    bithumb_gatekeeper_review_packet: dict | None = None,
    bithumb_shadow_preflight: dict | None = None,
    tiny_live_pretrade: dict | None = None,
) -> dict:
    stage6_entry = stage6_entry or {}
    official_kis_route = official_kis_route or {}
    operator_status_brief = operator_status_brief or {}
    kis_historical_gap_matrix = kis_historical_gap_matrix or {}
    kis_source_acquisition_queue = kis_source_acquisition_queue or {}
    kis_intake_import_preflight = kis_intake_import_preflight or {}
    kis_intake_work_order = kis_intake_work_order or {}
    kis_next_evidence_fill_card = kis_next_evidence_fill_card or {}
    kis_next_evidence_bundle_apply = kis_next_evidence_bundle_apply or {}
    kis_intake_row_update = kis_intake_row_update or {}
    kis_source_artifact_registry_update = kis_source_artifact_registry_update or {}
    kis_source_artifact_registry = kis_source_artifact_registry or {}
    kis_intake_source_provenance = kis_intake_source_provenance or {}
    kis_canonical_import_apply = kis_canonical_import_apply or {}
    kis_axis_wide_membership_handoff_package = kis_axis_wide_membership_handoff_package or {}
    kis_axis_wide_membership_response_validator = kis_axis_wide_membership_response_validator or {}
    kis_axis_wide_membership_import = kis_axis_wide_membership_import or {}
    kis_axis_wide_membership_coverage_progress = kis_axis_wide_membership_coverage_progress or {}
    kis_axis_wide_membership_worklist_fill_progress = kis_axis_wide_membership_worklist_fill_progress or {}
    kis_axis_wide_historical_source_feasibility_matrix = kis_axis_wide_historical_source_feasibility_matrix or {}
    kis_axis_wide_source_export_intake_contract = kis_axis_wide_source_export_intake_contract or {}
    kis_axis_wide_source_export_inbox_status = kis_axis_wide_source_export_inbox_status or {}
    kis_axis_wide_source_export_next_command = kis_axis_wide_source_export_next_command or {}
    krx_data_marketplace_access_probe = krx_data_marketplace_access_probe or {}
    kis_axis_wide_source_export_operator_packet = kis_axis_wide_source_export_operator_packet or {}
    kis_axis_wide_source_exports_to_replacement_worklist = kis_axis_wide_source_exports_to_replacement_worklist or {}
    kis_axis_wide_membership_worklist_to_shards = kis_axis_wide_membership_worklist_to_shards or {}
    kis_operation_ready_manifest = kis_operation_ready_manifest or {}
    bithumb_oos_walkforward = bithumb_oos_walkforward or {}
    bithumb_nonzero_signal_scout = bithumb_nonzero_signal_scout or {}
    bithumb_orca_oos_family_review = bithumb_orca_oos_family_review or {}
    bithumb_gatekeeper_review_packet = bithumb_gatekeeper_review_packet or {}
    bithumb_shadow_preflight = bithumb_shadow_preflight or {}
    tiny_live_pretrade = tiny_live_pretrade or {}
    current_safety = tiny_live_pretrade.get("safety") or SAFETY

    tiny_summary = dict(tiny_live.get("summary", {}) or {})
    failed_required = list(tiny_live.get("failed_required_check_ids", []) or [])
    stage6_reached = bool(stage6_entry.get("stage6_reached", tiny_summary.get("stage6_reached", False)))
    shadow_passed = bool(tiny_summary.get("shadow_passed", False))
    shadow_allowed = bool(tiny_summary.get("shadow_queue_allowed", False))
    external_retired = bool(
        (official_kis_route.get("pipeline_decision", {}) or {}).get(
            "retire_default_external_provider_dispatch", False
        )
    )
    safety_ok = _safe(active_audit, tiny_live, wait_state, watcher_process_status, transition)
    stage1 = _stage1_row(
        tiny_live,
        kis_historical_gap_matrix,
        kis_source_acquisition_queue,
        kis_intake_import_preflight,
        kis_intake_work_order,
        kis_next_evidence_fill_card,
        kis_next_evidence_bundle_apply,
        kis_intake_row_update,
        kis_source_artifact_registry_update,
        kis_source_artifact_registry,
        kis_intake_source_provenance,
        kis_canonical_import_apply,
        kis_axis_wide_membership_handoff_package,
        kis_axis_wide_membership_response_validator,
        kis_axis_wide_membership_import,
        kis_axis_wide_membership_coverage_progress,
        kis_axis_wide_membership_worklist_fill_progress,
        kis_axis_wide_historical_source_feasibility_matrix,
        kis_axis_wide_source_export_intake_contract,
        kis_axis_wide_source_export_inbox_status,
        kis_axis_wide_source_export_next_command,
        krx_data_marketplace_access_probe,
        kis_axis_wide_source_export_operator_packet,
        kis_axis_wide_source_exports_to_replacement_worklist,
        kis_axis_wide_membership_worklist_to_shards,
        kis_operation_ready_manifest,
    )
    if external_retired:
        stage1 = dict(stage1)
        stage1["name"] = "Data Readiness / Current Universe Qualification"
        stage1["passed"] = True
        stage1["missing_or_blocked"] = []
        stage1["live_promotion_caveats"] = sorted(LIVE_PROMOTION_CAVEAT_BLOCKERS)
        stage1["observed"] = dict(stage1.get("observed", {}) or {})
        stage1["observed"]["current_universe_mode"] = "KIS_OFFICIAL_GITHUB_AND_API_CAVEATED"
        stage1["observed"]["pit_survivorship_role"] = "live_promotion_caveat_not_current_pipeline_blocker"
    stage4_passed = bool(tiny_summary.get("stage5_internal_evidence_passed", False)) or bool(
        transition.get("stage5_passed_records", 0)
    )
    retired_shadow_paper_state = {
        "stage_id": "retired_shadow_paper_state",
        "name": "Retired Shadow/Paper State",
        "required_for_stage13": False,
        "passed": True,
        "evidence": "shadow/paper remain optional no-submit observation tools, not promotion stages",
        "observed": {
            "shadow_queue_allowed": shadow_allowed,
            "shadow_passed": shadow_passed,
            "stage6_reached": stage6_reached,
            "paper_enabled": False,
            "broker_submit_allowed": False,
            "interpretation": "shadow_and_paper_are_removed_from_required_stage_progress",
        },
        "missing_or_blocked": [],
    }
    external_row = {
        "stage_id": "external_dispatch",
        "name": "External Provider Dispatch / Returned Rows",
        "required_for_stage13": not external_retired,
        "passed": external_retired
        or wait_state.get("status") == "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS",
        "evidence": r"C:\AI\reports\operations\kis_official_open_trading_api_route_latest.json",
        "observed": official_kis_route or wait_state,
        "missing_or_blocked": [] if external_retired else wait_state.get("missing_or_blocked_check_ids", []),
    }
    watcher_row = {
        "stage_id": "provider_return_watch_process",
        "name": "Provider Return Watch Process",
        "required_for_stage13": False,
        "passed": bool(watcher_process_status.get("ready_for_unattended_wait", False)),
        "evidence": r"C:\AI\reports\live_readiness\CAND-022_provider_return_watch_process_status.latest.json",
        "observed": watcher_process_status,
        "missing_or_blocked": []
        if watcher_process_status.get("ready_for_unattended_wait", False)
        else ["provider_return_watch_process_not_ready"],
    }
    safety_row = {
        "stage_id": "safety",
        "name": "Safety Invariant",
        "required_for_stage13": True,
        "passed": safety_ok,
        "evidence": "active audit, tiny-live audit, wait-state, and transition ledger",
        "observed": SAFETY,
        "missing_or_blocked": [] if safety_ok else ["safety_drift"],
    }
    bithumb_axis_row = _bithumb_axis_row(
        bithumb_oos_walkforward,
        bithumb_nonzero_signal_scout,
        bithumb_orca_oos_family_review,
        bithumb_gatekeeper_review_packet,
        bithumb_shadow_preflight,
    )
    pretrade_firewall = tiny_live_pretrade.get("firewall", {}) or {}
    stage9_passed = pretrade_firewall.get("decision") == "ALLOW_LIMITED_LIVE" and bool(
        tiny_live_pretrade.get("intent_path")
    )
    stage9_missing = [] if stage9_passed else ["order_intent_not_created", "pretrade_firewall_not_passed"]
    stage10_missing = (
        ["global_disable_all_trading_present"]
        if tiny_live_pretrade.get("global_disable_present")
        else ["real_orders_0", "live_submit_not_attempted"]
    )
    stage9_row = {
        "stage_id": "stage9",
        "name": "Tiny Limited Live Request",
        "required_for_stage13": True,
        "passed": stage9_passed,
        "evidence": r"C:\AI\reports\operations\tiny_live_order_intent_pretrade_latest.json",
        "observed": tiny_live_pretrade or {"order_intent_created": False},
        "missing_or_blocked": stage9_missing,
    }
    stage10_row = {
        "stage_id": "stage10",
        "name": "Tiny Limited Live",
        "required_for_stage13": True,
        "passed": False,
        "evidence": r"C:\AI\reports\operations\tiny_live_order_intent_pretrade_latest.json",
        "observed": {
            "real_orders": tiny_live_pretrade.get("real_orders", 0),
            "broker_submit_attempt_status": tiny_live_pretrade.get("broker_submit_attempt_status"),
            "global_disable_present": tiny_live_pretrade.get("global_disable_present"),
        },
        "missing_or_blocked": stage10_missing,
    }
    base_rows = [
        {"stage_id": "stage0", "name": "Human Mandate / Capital Policy", "required_for_stage13": True, "passed": "human_mandate_complete" not in failed_required, "evidence": r"C:\AI\contracts\human_mandate.yaml", "observed": {"failed_required_check_ids": failed_required}, "missing_or_blocked": []},
        stage1,
        bithumb_axis_row,
        {"stage_id": "stage2", "name": "Idea Intake", "required_for_stage13": True, "passed": True, "evidence": r"C:\AI\candidate_registry\candidate_registry.jsonl", "observed": "CAND-022 registered as current G2 conversion candidate", "missing_or_blocked": []},
        {"stage_id": "stage3", "name": "Research Discovery", "required_for_stage13": True, "passed": True, "evidence": r"C:\AI\candidate_registry\candidate_registry.jsonl", "observed": "CAND-004/CAND-019 lineage preserved; CAND-022 child exists", "missing_or_blocked": []},
        {"stage_id": "stage4", "name": "Risk Compression / Portfolio Fit", "required_for_stage13": True, "passed": stage4_passed, "evidence": r"C:\AI\reports\operations\stage4_risk_compression_queue_status_latest.json", "observed": {"stage5_internal_evidence_passed": stage4_passed, "stage5_passed_records": transition.get("stage5_passed_records")}, "missing_or_blocked": []},
        {"stage_id": "stage5", "name": "Robustness / OOS Validation", "required_for_stage13": True, "passed": "oos_parameters_not_found" not in failed_required, "evidence": r"C:\AI\robustness_evidence\robustness_evidence_registry.jsonl", "observed": {"stage5_passed_records": transition.get("stage5_passed_records")}, "missing_or_blocked": []},
        {"stage_id": "gatekeeper", "name": "Gatekeeper Transition Judge", "required_for_stage13": True, "passed": bool(transition.get("decision_records_written", 0)), "evidence": r"C:\AI\pipeline_orchestration\latest_transition_ledger_summary.json", "observed": transition, "missing_or_blocked": []},
        retired_shadow_paper_state,
        stage9_row,
        stage10_row,
        {"stage_id": "stage11", "name": "Post-Live Audit", "required_for_stage13": True, "passed": False, "evidence": "no tiny live execution evidence", "observed": {"real_orders": 0}, "missing_or_blocked": ["no_live_execution_to_audit"]},
        {"stage_id": "stage12", "name": "Scale Review", "required_for_stage13": True, "passed": False, "evidence": "no post-live audit evidence", "observed": "not reached", "missing_or_blocked": ["no_post_live_audit"]},
        {"stage_id": "stage13", "name": "Monitored Capital", "required_for_stage13": True, "passed": False, "evidence": "no monitored capital deployment evidence", "observed": "not reached", "missing_or_blocked": ["stage13_not_reached"]},
        safety_row,
        external_row,
        watcher_row,
    ]
    failed_stage_ids = [
        row["stage_id"]
        for row in base_rows
        if row.get("required_for_stage13") and not row.get("passed")
    ]
    missing = sorted(
        {
            item
            for row in base_rows
            for item in row.get("missing_or_blocked", [])
        }
        | set(active_audit.get("missing_or_blocked_check_ids", []))
        | set(wait_state.get("missing_or_blocked_check_ids", []))
    )
    missing = [item for item in missing if item not in RETIRED_STAGE_BLOCKERS]
    if external_retired:
        missing = [item for item in missing if item not in LIVE_PROMOTION_CAVEAT_BLOCKERS]
        missing = [item for item in missing if item not in RETIRED_EXTERNAL_PROVIDER_BLOCKERS]
    if not watcher_row["passed"]:
        missing.append("provider_return_watch_process_not_ready")
    if not external_retired and external_row["required_for_stage13"]:
        failed_stage_ids.append("external_dispatch")
    waiting_for_provider_rows = (not external_retired) and wait_state.get("status") == "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS"
    waiting_for_axis_wide_source_export = (not external_retired) and _axis_wide_source_export_waiting_for_input(
        kis_axis_wide_source_export_inbox_status,
        kis_axis_wide_source_export_next_command,
        krx_data_marketplace_access_probe,
        kis_axis_wide_source_export_operator_packet,
    )
    primary_next_action = _next_action(
        active_audit,
        operator_status_brief,
        kis_source_acquisition_queue,
        kis_axis_wide_membership_handoff_package,
        kis_axis_wide_membership_response_validator,
        kis_axis_wide_membership_coverage_progress,
        kis_axis_wide_source_export_operator_packet,
    )
    if external_retired:
        primary_next_action = (
            "Stage shadow/paper removed. Next required gate is Stage 9: do not create an order intent "
            "until the operator gives an exact LIVE APPROVE <max_krw> <max_daily_loss_krw> <max_total_loss_krw> phrase."
        )
    if stage9_passed:
        primary_next_action = (
            "Stage 9 passed: order intent exists and pretrade firewall allowed limited live. "
            "Actual broker submit remains blocked while C:\\AI\\ops\\runstate\\DISABLE_ALL_TRADING exists."
        )
    current_target_stage_id = 10 if stage9_passed else 9
    current_target_stage_name = "Tiny Limited Live" if stage9_passed else "Tiny Limited Live Request"
    current_target_missing = stage10_missing if stage9_passed else stage9_missing
    report = {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "canonical_stage_source": r"C:\AI\AGENTS.md",
        "stage_policy_implementation": str(Path(__file__).resolve()),
        "objective_restatement": "Build the two-axis capital-growth pipeline: BITHUMB_KRW for all Bithumb-tradable crypto plus KIS_COMBINED_KRW for Korea/US stocks and ETFs. Shadow and paper are optional no-submit observation tools, not required promotion stages.",
        "current_milestone": "PROVE_TINY_LIVE_PRECONDITIONS_UNDER_HARD_CAP_POLICY",
        "active_axes": ["BITHUMB_KRW", "KIS_COMBINED_KRW"],
        "current_target_stage_id": current_target_stage_id,
        "current_target_stage_name": current_target_stage_name,
        "current_target_stage_reached": False,
        "current_target_stage_completion_percent": 0.0,
        "current_target_stage_missing_or_blocked": current_target_missing,
        "completion_decision": "NOT_COMPLETE",
        "stage13_complete": False,
        "blocked_by_external_input": waiting_for_provider_rows or waiting_for_axis_wide_source_export,
        "external_input_blockers": sorted(
            item
            for item, blocked in {
                "operator_or_provider_rows_wait": waiting_for_provider_rows,
                "reviewed_axis_wide_source_export_missing": waiting_for_axis_wide_source_export,
            }.items()
            if blocked
        ),
        "current_blocked_state": "KIS_CURRENT_UNIVERSE_READY_PIT_IS_LIVE_PROMOTION_CAVEAT"
        if external_retired
        else "EXTERNAL_DISPATCH_OR_PROVIDER_ROWS_BLOCKED",
        "prompt_to_artifact_checklist": base_rows,
        "failed_required_stage_ids": failed_stage_ids,
        "missing_or_blocked_check_ids": sorted(set(missing)),
        "single_next_action": primary_next_action,
        "axis_next_actions": _axis_next_actions(primary_next_action, bithumb_axis_row),
        "do_not_mark_goal_complete": True,
        "safety": current_safety,
        "source_files": {
            "active_thread_goal_audit": r"C:\AI\reports\live_readiness\CAND-022_active_thread_goal_audit.latest.json",
            "tiny_live_completion_audit": r"C:\AI\reports\live_readiness\CAND-022_tiny_live_completion_audit.latest.json",
            "blocked_wait_state": r"C:\AI\reports\live_readiness\CAND-022_blocked_wait_state.latest.json",
            "provider_return_watch_process_status": r"C:\AI\reports\live_readiness\CAND-022_provider_return_watch_process_status.latest.json",
            "transition_ledger_summary": r"C:\AI\pipeline_orchestration\latest_transition_ledger_summary.json",
            "stage6_entry_path_audit": r"C:\AI\pipeline_orchestration\stage6_shadow_readiness\CAND-022_stage6_entry_path_audit.latest.json",
            "stage6_goal_completion_audit": r"C:\AI\pipeline_orchestration\stage6_shadow_readiness\CAND-022_stage6_goal_completion_audit.latest.json",
            "official_kis_route": r"C:\AI\reports\operations\kis_official_open_trading_api_route_latest.json",
            "kis_pit_source_acquisition_queue": r"C:\AI\reports\operations\kis_pit_source_acquisition_queue_latest.json",
            "kis_pit_intake_import_preflight": r"C:\AI\reports\operations\kis_pit_intake_import_preflight_latest.json",
            "kis_pit_intake_work_order": r"C:\AI\reports\operations\kis_pit_intake_work_order_latest.json",
            "kis_pit_next_evidence_fill_card": r"C:\AI\reports\operations\kis_pit_next_evidence_fill_card_latest.json",
            "kis_pit_next_evidence_bundle_apply": r"C:\AI\reports\operations\kis_pit_next_evidence_bundle_apply_latest.json",
            "kis_pit_intake_row_update": r"C:\AI\reports\operations\kis_pit_intake_row_update_latest.json",
            "kis_pit_source_artifact_registry_update": r"C:\AI\reports\operations\kis_pit_source_artifact_registry_update_latest.json",
            "kis_pit_source_artifact_registry_verifier": r"C:\AI\reports\operations\kis_pit_source_artifact_registry_verifier_latest.json",
            "kis_pit_intake_source_provenance_verifier": r"C:\AI\reports\operations\kis_pit_intake_source_provenance_verifier_latest.json",
            "kis_pit_canonical_import_apply": r"C:\AI\reports\operations\kis_pit_canonical_import_apply_latest.json",
            "kis_axis_wide_membership_handoff_package": r"C:\AI\reports\operations\kis_axis_wide_membership_handoff_package_latest.json",
            "kis_axis_wide_historical_source_feasibility_matrix": r"C:\AI\reports\operations\kis_axis_wide_historical_source_feasibility_matrix_latest.json",
            "kis_axis_wide_source_export_intake_contract": r"C:\AI\reports\operations\kis_axis_wide_source_export_intake_contract_latest.json",
            "kis_axis_wide_source_export_inbox_status": r"C:\AI\reports\operations\kis_axis_wide_source_export_inbox_status_latest.json",
            "kis_axis_wide_source_export_next_command": r"C:\AI\reports\operations\kis_axis_wide_source_export_next_command_latest.json",
            "krx_data_marketplace_access_probe": r"C:\AI\reports\operations\krx_data_marketplace_access_probe_latest.json",
            "kis_axis_wide_source_export_operator_packet": r"C:\AI\reports\operations\kis_axis_wide_source_export_operator_packet_latest.json",
            "kis_axis_wide_source_exports_to_replacement_worklist": r"C:\AI\reports\operations\kis_axis_wide_source_exports_to_replacement_worklist_latest.json",
            "bithumb_oos_walkforward": r"C:\AI\reports\model_factory\bithumb_current_actionable_oos_walkforward_latest.json",
            "bithumb_nonzero_signal_scout": r"C:\AI\reports\operations\bithumb_current_actionable_nonzero_signal_scout_latest.json",
            "bithumb_orca_oos_family_review": r"C:\AI\reports\model_factory\bithumb_current_actionable_orca_oos_family_review_latest.json",
            "bithumb_gatekeeper_review_packet": r"C:\AI\reports\model_factory\bithumb_current_actionable_gatekeeper_review_packet_latest.json",
            "bithumb_shadow_preflight": r"C:\AI\reports\model_factory\bithumb_current_actionable_shadow_preflight_latest.json",
            "tiny_live_order_intent_pretrade": r"C:\AI\reports\operations\tiny_live_order_intent_pretrade_latest.json",
        },
    }
    return report


def render_markdown(report: dict) -> str:
    retired = next(row for row in report["prompt_to_artifact_checklist"] if row["stage_id"] == "retired_shadow_paper_state")
    return "\n".join(
        [
            "# Stage 13 Completion Audit",
            "",
            f"- Decision: `{report['completion_decision']}`",
            f"- Objective: {report['objective_restatement']}",
            f"- Current milestone: `{report.get('current_milestone', '')}`",
            f"- KIS next: {report.get('axis_next_actions', {}).get('KIS_COMBINED_KRW', '')}",
            f"- Bithumb next: {report.get('axis_next_actions', {}).get('BITHUMB_KRW', '')}",
            f"- current_target_stage: `Stage {report['current_target_stage_id']} - {report['current_target_stage_name']}`",
            "- Shadow/Paper: `retired_from_required_stage_progress`",
            "",
            "## Retired Shadow/Paper State",
            f"- Shadow queue allowed: `{retired['observed'].get('shadow_queue_allowed')}`",
            f"- Shadow passed: `{retired['observed'].get('shadow_passed')}`",
            f"- Interpretation: `{retired['observed'].get('interpretation')}`",
        ]
    )


def main() -> int:
    generated_at = datetime.now(tz=KST).isoformat(timespec="seconds")
    report = build_report(
        generated_at,
        active_audit=read_json(ROOT / "reports/live_readiness/CAND-022_active_thread_goal_audit.latest.json", {}),
        tiny_live=read_json(ROOT / "reports/live_readiness/CAND-022_tiny_live_completion_audit.latest.json", {}),
        wait_state=read_json(ROOT / "reports/live_readiness/CAND-022_blocked_wait_state.latest.json", {}),
        watcher_process_status=read_json(ROOT / "reports/live_readiness/CAND-022_provider_return_watch_process_status.latest.json", {}),
        transition=read_json(ROOT / "pipeline_orchestration/latest_transition_ledger_summary.json", {}),
        stage6_entry=read_json(ROOT / "pipeline_orchestration/stage6_shadow_readiness/CAND-022_stage6_entry_path_audit.latest.json", {}),
        official_kis_route=read_json(ROOT / "reports/operations/kis_official_open_trading_api_route_latest.json", {}),
        operator_status_brief=read_json(ROOT / "reports/live_readiness/CAND-022_operator_status_brief.latest.json", {}),
        kis_historical_gap_matrix=read_json(ROOT / "reports/operations/kis_historical_pit_survivorship_gap_matrix_latest.json", {}),
        kis_source_acquisition_queue=read_json(ROOT / "reports/operations/kis_pit_source_acquisition_queue_latest.json", {}),
        kis_intake_import_preflight=read_json(ROOT / "reports/operations/kis_pit_intake_import_preflight_latest.json", {}),
        kis_intake_work_order=read_json(ROOT / "reports/operations/kis_pit_intake_work_order_latest.json", {}),
        kis_next_evidence_fill_card=read_json(ROOT / "reports/operations/kis_pit_next_evidence_fill_card_latest.json", {}),
        kis_next_evidence_bundle_apply=read_json(ROOT / "reports/operations/kis_pit_next_evidence_bundle_apply_latest.json", {}),
        kis_intake_row_update=read_json(ROOT / "reports/operations/kis_pit_intake_row_update_latest.json", {}),
        kis_source_artifact_registry_update=read_json(ROOT / "reports/operations/kis_pit_source_artifact_registry_update_latest.json", {}),
        kis_source_artifact_registry=read_json(ROOT / "reports/operations/kis_pit_source_artifact_registry_verifier_latest.json", {}),
        kis_intake_source_provenance=read_json(ROOT / "reports/operations/kis_pit_intake_source_provenance_verifier_latest.json", {}),
        kis_canonical_import_apply=read_json(ROOT / "reports/operations/kis_pit_canonical_import_apply_latest.json", {}),
        kis_axis_wide_membership_handoff_package=read_json(ROOT / "reports/operations/kis_axis_wide_membership_handoff_package_latest.json", {}),
        kis_axis_wide_membership_response_validator=read_json(ROOT / "reports/operations/kis_axis_wide_membership_response_validator_latest.json", {}),
        kis_axis_wide_membership_import=read_json(ROOT / "reports/operations/kis_axis_wide_membership_import_latest.json", {}),
        kis_axis_wide_membership_coverage_progress=read_json(ROOT / "reports/operations/kis_axis_wide_membership_coverage_progress_latest.json", {}),
        kis_axis_wide_membership_worklist_fill_progress=read_json(ROOT / "reports/operations/kis_axis_wide_membership_worklist_fill_progress_latest.json", {}),
        kis_axis_wide_historical_source_feasibility_matrix=read_json(ROOT / "reports/operations/kis_axis_wide_historical_source_feasibility_matrix_latest.json", {}),
        kis_axis_wide_source_export_intake_contract=read_json(ROOT / "reports/operations/kis_axis_wide_source_export_intake_contract_latest.json", {}),
        kis_axis_wide_source_export_inbox_status=read_json(ROOT / "reports/operations/kis_axis_wide_source_export_inbox_status_latest.json", {}),
        kis_axis_wide_source_export_next_command=read_json(ROOT / "reports/operations/kis_axis_wide_source_export_next_command_latest.json", {}),
        krx_data_marketplace_access_probe=read_json(ROOT / "reports/operations/krx_data_marketplace_access_probe_latest.json", {}),
        kis_axis_wide_source_export_operator_packet=read_json(ROOT / "reports/operations/kis_axis_wide_source_export_operator_packet_latest.json", {}),
        kis_axis_wide_source_exports_to_replacement_worklist=read_json(ROOT / "reports/operations/kis_axis_wide_source_exports_to_replacement_worklist_latest.json", {}),
        kis_axis_wide_membership_worklist_to_shards=read_json(ROOT / "reports/operations/kis_axis_wide_membership_worklist_to_shards_latest.json", {}),
        kis_operation_ready_manifest=read_json(ROOT / "data_snapshots/manifests/kis_combined_operation_ready_manifest_latest.json", {}),
        bithumb_oos_walkforward=read_json(ROOT / "reports/model_factory/bithumb_current_actionable_oos_walkforward_latest.json", {}),
        bithumb_nonzero_signal_scout=read_json(ROOT / "reports/operations/bithumb_current_actionable_nonzero_signal_scout_latest.json", {}),
        bithumb_orca_oos_family_review=read_json(ROOT / "reports/model_factory/bithumb_current_actionable_orca_oos_family_review_latest.json", {}),
        bithumb_gatekeeper_review_packet=read_json(ROOT / "reports/model_factory/bithumb_current_actionable_gatekeeper_review_packet_latest.json", {}),
        bithumb_shadow_preflight=read_json(ROOT / "reports/model_factory/bithumb_current_actionable_shadow_preflight_latest.json", {}),
        tiny_live_pretrade=read_json(ROOT / "reports/operations/tiny_live_order_intent_pretrade_latest.json", {}),
    )
    write_json(LATEST_JSON, report)
    LATEST_MD.write_text(render_markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "completion_decision": report["completion_decision"],
                "stage13_complete": report["stage13_complete"],
                "blocked_by_external_input": report["blocked_by_external_input"],
                "failed_required_stage_ids": report["failed_required_stage_ids"],
                "latest_json": str(LATEST_JSON),
                "latest_md": str(LATEST_MD),
                "safety": report["safety"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
