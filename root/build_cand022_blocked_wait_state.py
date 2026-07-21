from __future__ import annotations

import json
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

DEFAULT_ROUTER = ROOT / "reports/live_readiness/CAND-022_next_action_router.latest.json"
DEFAULT_AUDIT = ROOT / "reports/live_readiness/CAND-022_active_thread_goal_audit.latest.json"
DEFAULT_BRIEF = ROOT / "reports/live_readiness/CAND-022_operator_status_brief.latest.json"
DEFAULT_SEND_STATUS = ROOT / "reports/operations/kis_provider_external_dispatch_send_status_latest.json"
DEFAULT_RETURN_RECEIPT = ROOT / "reports/operations/kis_provider_external_return_receipt_status_latest.json"
DEFAULT_STAGE6_WAIT = (
    ROOT / "pipeline_orchestration/stage6_shadow_readiness/CAND-022_stage6_operator_wait_packet.latest.json"
)
LATEST_JSON = ROOT / "reports/live_readiness/CAND-022_blocked_wait_state.latest.json"
LATEST_MD = ROOT / "reports/live_readiness/CAND-022_blocked_wait_state.latest.md"


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _router_action(router: dict, action_id: str) -> dict:
    for action in router.get("action_router", []) or []:
        if action.get("action_id") == action_id:
            return dict(action)
    return {}


def _same_wait_state(router_wait: dict, brief_wait: dict) -> bool:
    return (
        router_wait.get("decision") == brief_wait.get("decision")
        and router_wait.get("can_continue_local_work")
        == brief_wait.get("can_continue_local_work")
    )


def _safe(payload: dict) -> bool:
    observed = dict(payload.get("safety", {}) or {})
    for key, value in SAFETY.items():
        if observed.get(key, value) != value:
            return False
    return True


def _is_official_kis_current_rebuild(router: dict, brief: dict, stage6_wait: dict) -> bool:
    router_wait = dict(router.get("autonomous_continuation", {}) or {})
    brief_wait = dict(brief.get("autonomous_continuation", {}) or {})
    return all(
        [
            router.get("recommended_next_action_id")
            == "rebuild_kis_current_readiness_from_official_api",
            router_wait.get("decision") == "CONTINUE_OFFICIAL_KIS_CURRENT_READINESS_REBUILD",
            router_wait.get("can_continue_local_work") is True,
            _same_wait_state(router_wait, brief_wait),
            stage6_wait.get("recommended_next_action_id")
            == "rebuild_kis_current_readiness_from_official_api",
            stage6_wait.get("stage6_reached") is True,
            stage6_wait.get("blocked_by_operator_or_provider") is False,
        ]
    )


def build_report(
    generated_at: str,
    *,
    router_path: Path = DEFAULT_ROUTER,
    active_audit_path: Path = DEFAULT_AUDIT,
    operator_brief_path: Path = DEFAULT_BRIEF,
    send_status_path: Path = DEFAULT_SEND_STATUS,
    return_receipt_path: Path = DEFAULT_RETURN_RECEIPT,
    stage6_wait_packet_path: Path = DEFAULT_STAGE6_WAIT,
) -> dict:
    router = _load(router_path)
    audit = _load(active_audit_path)
    brief = _load(operator_brief_path)
    send_status = _load(send_status_path)
    return_receipt = _load(return_receipt_path)
    stage6_wait = _load(stage6_wait_packet_path)

    router_wait = dict(router.get("autonomous_continuation", {}) or {})
    brief_wait = dict(brief.get("autonomous_continuation", {}) or {})
    dispatch_action = _router_action(router, "send_external_provider_dispatch_packet")
    checks = {
        "router_waits_for_external_input": router_wait.get("decision")
        == "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS",
        "operator_brief_matches_wait_state": _same_wait_state(router_wait, brief_wait),
        "active_audit_not_complete": audit.get("completion_decision", audit.get("status"))
        not in {"COMPLETE", "COMPLETED"},
        "external_blockers_open": bool(
            set(audit.get("missing_or_blocked_check_ids", []))
            & {
                "dispatch_sent_confirmation_recorded",
                "returned_provider_csvs_received",
                "source_backed_rows_complete",
                "tiny_live_preconditions_complete",
            }
        ),
        "dispatch_not_confirmed": not bool(send_status.get("send_confirmation_valid", False)),
        "returned_provider_csvs_missing": bool(return_receipt.get("missing_files", []))
        or return_receipt.get("status") == "WAITING_FOR_RETURNED_PROVIDER_CSVS",
        "stage6_wait_packet_matches_wait_state": bool(
            stage6_wait.get("blocked_by_operator_or_provider", False)
        )
        or (
            stage6_wait.get("stage6_reached") is True
            and stage6_wait.get("blocked_by_operator_or_provider") is True
            and stage6_wait.get("prompt_to_artifact_completion_audit", {}).get("complete")
            is True
            and router_wait.get("decision")
            == "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS"
        ),
        "stage6_wait_packet_has_safe_watch_commands": "run_cand022_provider_return_watch.py"
        in str(stage6_wait.get("dispatch_wait", {}).get("safe_watch_command_after_dispatch", ""))
        and "--no-refresh"
        in str(stage6_wait.get("dispatch_wait", {}).get("safe_watch_command_report_only", "")),
        "stage6_wait_packet_has_returned_copy_review": bool(
            stage6_wait.get("dispatch_wait", {})
            .get("after_return_copy_review", {})
            .get("required_before_refresh", False)
        ),
        "router_dispatch_action_safety_locked": dispatch_action.get("action_safety")
        == SAFETY,
        "stage6_copy_review_before_refresh_enforced": bool(
            stage6_wait.get("dispatch_wait", {}).get(
                "copy_review_before_refresh_enforced",
                stage6_wait.get("dispatch_wait", {})
                .get("after_return_copy_review", {})
                .get("required_before_refresh", False),
            )
        ),
        "safety_preserved": all(
            _safe(payload)
            for payload in [router, audit, brief, send_status, return_receipt, stage6_wait]
        ),
    }

    if _is_official_kis_current_rebuild(router, brief, stage6_wait):
        status = "CONTINUE_OFFICIAL_KIS_CURRENT_READINESS_REBUILD"
        can_continue = True
        blockers: list[str] = []
        recommended = (
            "Run read-only KIS current-readiness refreshes and keep historical "
            "PIT/survivorship as the live blocker."
        )
    else:
        required = [
            "router_waits_for_external_input",
            "operator_brief_matches_wait_state",
            "active_audit_not_complete",
            "external_blockers_open",
            "dispatch_not_confirmed",
            "returned_provider_csvs_missing",
            "stage6_wait_packet_matches_wait_state",
            "stage6_wait_packet_has_safe_watch_commands",
            "stage6_wait_packet_has_returned_copy_review",
            "router_dispatch_action_safety_locked",
            "stage6_copy_review_before_refresh_enforced",
            "safety_preserved",
        ]
        blockers = [key for key in required if not checks[key]]
        status = (
            "WAIT_FOR_OPERATOR_EXTERNAL_DISPATCH_OR_PROVIDER_ROWS"
            if not blockers
            else "BLOCKED_WAIT_STATE_INCONSISTENT"
        )
        can_continue = False if not blockers else None
        recommended = (
            "Use C:\\AI\\reports\\live_readiness\\CAND-022_manual_dispatch_execution_slip.latest.md, "
            "send only the frozen files, then record actual dispatch with python "
            ".\\write_cand022_dispatch_sent_confirmation.py --sent-at \"<timezone-aware sent time>\" "
            "--sent-by \"<operator_or_account>\" --recipient-or-channel \"<provider_or_channel>\" "
            "--i-confirm-actual-send."
        )

    dispatch_wait = dict(stage6_wait.get("dispatch_wait", {}) or {})
    report = {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "candidate_id": "CAND-022",
        "status": status,
        "can_continue_local_work": can_continue,
        "recommended_operator_action": recommended,
        "allowed_local_actions": router_wait.get("allowed_local_actions", []),
        "blocked_local_actions": router_wait.get("blocked_local_actions", []),
        "checks": checks,
        "blockers": blockers,
        "missing_or_blocked_check_ids": audit.get("missing_or_blocked_check_ids", []),
        "dispatch_send_status": {
            "status": send_status.get("status"),
            "send_confirmation_valid": send_status.get("send_confirmation_valid", False),
            "send_confirmation_blockers": send_status.get(
                "send_confirmation_blockers", []
            ),
        },
        "return_receipt": {
            "status": return_receipt.get("status"),
            "missing_files": return_receipt.get("missing_files", []),
        },
        "stage6_wait_packet": {
            "status": stage6_wait.get("status"),
            "stage6_reached": stage6_wait.get("stage6_reached", False),
            "blocked_by_operator_or_provider": stage6_wait.get(
                "blocked_by_operator_or_provider", False
            ),
            "safe_watch_command_after_dispatch": dispatch_wait.get(
                "safe_watch_command_after_dispatch", ""
            ),
            "safe_watch_command_report_only": dispatch_wait.get(
                "safe_watch_command_report_only", ""
            ),
            "after_return_copy_review": dispatch_wait.get(
                "after_return_copy_review", {}
            ),
            "after_return_command": dispatch_wait.get("after_return_command", ""),
            "completion_audit_complete": stage6_wait.get(
                "prompt_to_artifact_completion_audit", {}
            ).get("complete", False),
            "missing": stage6_wait.get("prompt_to_artifact_completion_audit", {}).get(
                "missing", []
            ),
        },
        "router_dispatch_action": {
            "status": dispatch_action.get("status"),
            "action_safety": dispatch_action.get("action_safety"),
            "after_return_copy_review_required_before_refresh": dispatch_action.get(
                "after_return_copy_review_required_before_refresh"
            ),
            "after_return_copy_review_artifact": dispatch_action.get(
                "after_return_copy_review_artifact"
            ),
            "after_return_refresh_allowed_only_if_copy_review_status": dispatch_action.get(
                "after_return_refresh_allowed_only_if_copy_review_status"
            ),
            "after_return_refresh_forbidden_if_copy_review_status": dispatch_action.get(
                "after_return_refresh_forbidden_if_copy_review_status"
            ),
            "after_return_copy_review_then_refresh_contract": dispatch_action.get(
                "after_return_copy_review_then_refresh_contract"
            ),
        },
        "non_goals": [
            "does_not_send_email",
            "does_not_create_dispatch_confirmation",
            "does_not_fill_source_rows",
            "does_not_enable_paper_live_broker_submit_or_order_intent",
            "does_not_mark_goal_complete",
        ],
        "safety": SAFETY,
        "source_files": {
            "next_action_router": str(router_path),
            "active_thread_goal_audit": str(active_audit_path),
            "operator_status_brief": str(operator_brief_path),
            "dispatch_send_status": str(send_status_path),
            "return_receipt": str(return_receipt_path),
            "stage6_wait_packet": str(stage6_wait_packet_path),
        },
    }
    return report


def render_md(report: dict) -> str:
    return "\n".join(
        [
            "# CAND-022 Blocked Wait State",
            "",
            f"- Status: `{report['status']}`",
            f"- Can continue local work: `{str(report['can_continue_local_work']).lower()}`",
            f"- Recommended operator action: {report['recommended_operator_action']}",
            f"- Blockers: `{len(report['blockers'])}`",
            "",
            "## Blocked Local Actions",
            *[f"- `{item}`" for item in report.get("blocked_local_actions", [])],
            "",
            "## Allowed Local Actions",
            *[f"- `{item}`" for item in report.get("allowed_local_actions", [])],
            "",
        ]
    )


def main() -> int:
    generated_at = datetime.now(tz=KST).isoformat(timespec="seconds")
    report = build_report(generated_at)
    LATEST_JSON.parent.mkdir(parents=True, exist_ok=True)
    LATEST_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    LATEST_MD.write_text(render_md(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["status"],
                "latest_json": str(LATEST_JSON),
                "latest_md": str(LATEST_MD),
                "blockers": report["blockers"],
                "safety": report["safety"],
            },
            indent=2,
        )
    )
    return 0 if report["status"] != "BLOCKED_WAIT_STATE_INCONSISTENT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
