from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT_JSON = ROOT / "reports/model_factory/gatekeeper_pending_decision_board_latest.json"
REPORT_MD = ROOT / "reports/model_factory/gatekeeper_pending_decision_board_latest.md"

PAPER_SMOKE_JSON = ROOT / "reports/model_factory/paper_smoke_gatekeeper_review_packet_latest.json"
BITHUMB_TEMPLATE_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_decision_template_latest.json"
BITHUMB_DRAFT_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_human_decision_draft_latest.json"
BITHUMB_REGISTRATION_ACTION_PACKET_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_registration_action_packet_latest.json"
BITHUMB_REGISTRATION_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_shadow_registration_latest.json"
RISK_GUARD_JSON = ROOT / "ops/reports/realtime_risk_guard_latest.json"

BOARD_PERMISSIONS = {
    "shadow_registration_allowed_by_this_board": False,
    "paper_enabled_by_this_board": False,
    "live_allowed_by_this_board": False,
    "broker_submit_allowed_by_this_board": False,
    "private_submit_allowed_by_this_board": False,
    "real_orders_allowed_by_this_board": False,
}

SAFETY = {
    "does_register_shadow_candidate": False,
    "does_start_shadow_loop": False,
    "does_enable_paper": False,
    "does_enable_live": False,
    "broker_submit_allowed": False,
    "private_submit_allowed": False,
    "real_orders_allowed": False,
}


def read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default or {}


def _risk_guard_hard_safety_ok(risk_guard: dict) -> bool:
    if risk_guard.get("status") == "PASS":
        return True
    hard_names = {"live_disabled", "private_submit_unused", "real_orders_zero", "broker_submit_scope"}
    checks = risk_guard.get("checks", []) or []
    if not checks:
        return False
    return all(row.get("status") == "PASS" for row in checks if row.get("name") in hard_names)


def _paper_smoke_item(packet: dict) -> dict | None:
    if not packet:
        return None
    status = packet.get("status", "READY_FOR_GATEKEEPER_REVIEW")
    ready = bool(packet.get("review_ready", status == "READY_FOR_GATEKEEPER_REVIEW"))
    return {
        "decision_id": "paper_smoke_review",
        "decision_type": "gatekeeper_paper_smoke_review",
        "candidate_id": "small_account_growth_paper",
        "lane": "portfolio",
        "status": status,
        "ready_for_human_review": ready,
        "recommended_decision": "REVIEW_PAPER_SMOKE_ONLY",
        "exact_phrase_to_record": "REVIEW_PAPER_SMOKE_ONLY",
        "alternate_allowed_phrases": [],
        "review_only_effect": "Records evidence review only. It does not approve promotion, shadow registration, paper/live, broker submit, private submit, or real orders.",
        "evidence_summary": packet.get("evidence_summary", {}),
        "blockers": packet.get("blockers", []),
        "source_path": str(PAPER_SMOKE_JSON),
    }


def _bithumb_shadow_item(template: dict, draft: dict | None = None) -> dict | None:
    if not template:
        return None
    draft = draft or {}
    human_decision = template.get("human_decision", {}) or {}
    normalized = human_decision.get("normalized", {}) or {}
    return {
        "decision_id": "bithumb_current_actionable_shadow_review",
        "decision_type": "shadow_registration_review",
        "candidate_id": template.get("candidate_id"),
        "lane": "bithumb_1d",
        "status": template.get("status"),
        "ready_for_human_review": True,
        "closed": False,
        "recommended_decision": "DEFER_OR_APPROVE_SHADOW_REVIEW_ONLY",
        "exact_phrase_to_record": "APPROVE_SHADOW_REVIEW_ONLY",
        "alternate_allowed_phrases": ["REJECT", "DEFER"],
        "review_only_effect": "Records human approval for shadow-review consideration only. It does not register a shadow candidate, start a loop, enable paper/live, or allow orders.",
        "human_decision_path": human_decision.get("path"),
        "human_decision_present": bool(human_decision.get("present")),
        "human_decision_valid": bool(human_decision.get("valid")),
        "recorded_candidate_id": normalized.get("candidate_id"),
        "decision_candidate_match": (
            normalized.get("candidate_id") == template.get("candidate_id")
            if human_decision.get("present")
            else None
        ),
        "human_decision_draft_status": draft.get("status"),
        "human_decision_draft_candidate_id": draft.get("candidate_id"),
        "human_decision_draft_path": draft.get("draft_path"),
        "evidence_summary": template.get("evidence_summary", {}),
        "blockers": template.get("blockers", []),
        "source_path": str(BITHUMB_TEMPLATE_JSON),
    }


def _generic_item(source: dict, decision_id: str, decision_type: str, lane: str, phrase: str) -> dict | None:
    if not source:
        return None
    candidate_id = source.get("candidate_id") or source.get("best_candidate_id") or source.get("top_candidate_id")
    return {
        "decision_id": decision_id,
        "decision_type": decision_type,
        "candidate_id": candidate_id,
        "lane": lane,
        "status": source.get("status", "READY_FOR_HUMAN_GATEKEEPER_REVIEW"),
        "ready_for_human_review": not bool(source.get("blockers")),
        "recommended_decision": phrase,
        "exact_phrase_to_record": phrase,
        "alternate_allowed_phrases": [],
        "review_only_effect": "Records evidence review only. It does not approve promotion, shadow registration, paper/live, broker submit, private submit, or real orders.",
        "evidence_summary": source.get("evidence_summary", source),
        "blockers": source.get("blockers", []),
    }


def build_board(
    paper_smoke_gatekeeper_review: dict | None = None,
    bithumb_current_actionable_shadow_decision_template: dict | None = None,
    btc_eth_intraday_shadow_decision_template: dict | None = None,
    stock_conversion_gatekeeper_review_packet: dict | None = None,
    risk_guard: dict | None = None,
    bithumb_current_actionable_shadow_registration_action_packet: dict | None = None,
    bithumb_current_actionable_shadow_registration: dict | None = None,
    **kwargs: dict,
) -> dict:
    risk_guard = risk_guard or {"status": "WARN", "checks": []}
    items: list[dict] = []
    for item in [
        _paper_smoke_item(paper_smoke_gatekeeper_review or {}),
        _bithumb_shadow_item(
            bithumb_current_actionable_shadow_decision_template or {},
            kwargs.get("bithumb_actionable_human_decision_draft")
            or kwargs.get("bithumb_current_actionable_shadow_human_decision_draft"),
        ),
    ]:
        if item:
            items.append(item)
    if btc_eth_intraday_shadow_decision_template:
        item = _bithumb_shadow_item(btc_eth_intraday_shadow_decision_template, kwargs.get("btc_eth_intraday_human_decision_draft"))
        if item:
            item["decision_id"] = "btc_eth_intraday_shadow_review"
            item["lane"] = "btc_eth_1h4h"
            items.append(item)
    if stock_conversion_gatekeeper_review_packet:
        items.append(
            _generic_item(
                stock_conversion_gatekeeper_review_packet,
                "stock_conversion_review",
                "conversion_evidence_review",
                "kis_stock_etf",
                "REVIEW_CONVERSION_EVIDENCE_ONLY",
            )
        )
    for key, value in kwargs.items():
        if key.endswith("_human_decision_draft") or not isinstance(value, dict) or not value:
            continue
        decision_id = key.removesuffix("_packet").removesuffix("_review")
        phrase = "REVIEW_" + decision_id.upper() + "_ONLY"
        items.append(_generic_item(value, decision_id, decision_id, value.get("lane", "bithumb_1d"), phrase))
    if bithumb_current_actionable_shadow_registration_action_packet:
        item = _generic_item(
            bithumb_current_actionable_shadow_registration_action_packet,
            "bithumb_current_actionable_shadow_registration_action",
            "shadow_registration_action_review",
            "bithumb_1d",
            "REVIEW_ACTION_PACKET_ONLY",
        )
        if bithumb_current_actionable_shadow_registration and bithumb_current_actionable_shadow_registration.get("status") == "REGISTERED":
            item["status"] = "SHADOW_REVIEW_REGISTERED"
            item["closed"] = True
            item["ready_for_human_review"] = False
            item["blockers"] = []
        items.append(item)
    items = [item for item in items if item]
    risk_ok = _risk_guard_hard_safety_ok(risk_guard)
    if not risk_ok:
        for item in items:
            if item.get("ready_for_human_review"):
                item.setdefault("blockers", []).append("RISK_GUARD_NOT_PASS")
                item["ready_for_human_review"] = False
    ready = [item for item in items if item.get("ready_for_human_review")]
    blocked = [item for item in items if not item.get("ready_for_human_review")]
    priority_ids = [
        "bithumb_current_actionable_shadow_review",
        "bithumb_current_actionable_shadow_registration_action",
        "paper_smoke_review",
    ]
    next_decision = None
    for decision_id in priority_ids:
        next_decision = next((item for item in ready if item.get("decision_id") == decision_id), None)
        if next_decision:
            break
    if next_decision is None:
        next_decision = ready[0] if ready else None
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "report": "gatekeeper_pending_decision_board",
        "scope": "decision_support_only_no_registration_no_order_paths",
        "status": "READY_FOR_GATEKEEPER_REVIEW" if ready and risk_ok else "BLOCKED",
        "decision_count": len(items),
        "ready_decision_count": len(ready),
        "blocked_decision_count": len(blocked),
        "risk_guard_status": risk_guard.get("status"),
        "risk_guard_hard_safety_ok": risk_ok,
        "items": items,
        "next_decision": next_decision,
        "board_permissions": dict(BOARD_PERMISSIONS),
        "safety": dict(SAFETY),
    }


def render_md(board: dict) -> str:
    next_decision = board.get("next_decision") or {}
    return "\n".join(
        [
            "# Gatekeeper Pending Decision Board",
            "",
            f"- Status: `{board['status']}`",
            f"- Ready decisions: `{board['ready_decision_count']}`",
            f"- Blocked decisions: `{board['blocked_decision_count']}`",
            f"- Next decision: `{next_decision.get('decision_id', 'none')}`",
            "",
        ]
    )


def main() -> int:
    board = build_board(
        read_json(PAPER_SMOKE_JSON, {}),
        read_json(BITHUMB_TEMPLATE_JSON, {}),
        {},
        {},
        read_json(RISK_GUARD_JSON, {"status": "WARN"}),
        read_json(BITHUMB_REGISTRATION_ACTION_PACKET_JSON, {}),
        read_json(BITHUMB_REGISTRATION_JSON, {}),
        bithumb_actionable_human_decision_draft=read_json(BITHUMB_DRAFT_JSON, {}),
    )
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(board, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(board), encoding="utf-8")
    print(json.dumps({"status": board["status"], "ready_decision_count": board["ready_decision_count"], "blocked_decision_count": board["blocked_decision_count"], "latest_json": str(REPORT_JSON)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
