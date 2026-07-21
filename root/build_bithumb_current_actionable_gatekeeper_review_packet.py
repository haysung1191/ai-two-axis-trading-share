from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")
RISK_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_risk_conversion_latest.json"
SWEEP_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_parameter_sweep_latest.json"
OOS_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_oos_walkforward_latest.json"
ROBUSTNESS_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_robustness_stress_latest.json"
BACKTEST_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_backtest_screen_latest.json"
FROZEN_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_frozen_candidate_latest.json"
ACTION_PACKET_JSON = ROOT / "reports/model_factory/model_factory_gatekeeper_action_packet_latest.json"
RISK_GUARD_JSON = ROOT / "ops/reports/realtime_risk_guard_latest.json"
REPORT_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_gatekeeper_review_packet_latest.json"
REPORT_MD = ROOT / "reports/model_factory/bithumb_current_actionable_gatekeeper_review_packet_latest.md"

SAFE_REPORT_ASSERTIONS = {
    "promotion_allowed_by_this_report": False,
    "paper_enabled_by_this_report": False,
    "live_allowed_by_this_report": False,
    "broker_submit_allowed_by_this_report": False,
    "private_submit_allowed_by_this_report": False,
    "real_orders_allowed_by_this_report": False,
}
NO_ORDER_ASSERTIONS = {
    "promotion_allowed_by_this_packet": False,
    "shadow_enabled_by_this_packet": False,
    "paper_enabled_by_this_packet": False,
    "live_allowed_by_this_packet": False,
    "broker_submit_allowed_by_this_packet": False,
    "private_submit_allowed_by_this_packet": False,
    "real_orders_allowed_by_this_packet": False,
}


def read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default or {}


def _safe_report(report: dict) -> bool:
    assertions = report.get("no_order_assertions", {})
    return all(assertions.get(key) is value for key, value in SAFE_REPORT_ASSERTIONS.items())


def _risk_guard_hard_safety_pass(risk_guard: dict) -> bool:
    if risk_guard.get("status") == "PASS":
        return True
    checks = risk_guard.get("checks", [])
    hard_names = {"live_disabled", "private_submit_unused", "real_orders_zero", "broker_submit_scope"}
    if checks:
        return all(row.get("status") == "PASS" for row in checks if row.get("name") in hard_names)
    return False


def _best_oos_candidate(oos: dict, robustness: dict) -> dict:
    target = robustness.get("candidate_id")
    for row in oos.get("evaluations", []):
        if row.get("candidate_id") == target:
            return row
    rows = [row for row in oos.get("evaluations", []) if row.get("status") == "OOS_CANDIDATE_PASS"]
    return rows[0] if rows else {}


def build_packet(
    risk_conversion: dict,
    parameter_sweep: dict,
    oos: dict,
    robustness: dict,
    backtest: dict,
    frozen: dict,
    action_packet: dict,
    risk_guard: dict,
    generated_at: str | None = None,
) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    blockers = []
    selected_evidence_type = "risk_conversion"
    selected = risk_conversion.get("top_conversion", {})
    if parameter_sweep.get("top_sweep"):
        selected_evidence_type = "parameter_sweep"
        selected = parameter_sweep["top_sweep"]
    oos_candidate = _best_oos_candidate(oos, robustness)
    if oos_candidate:
        selected_evidence_type = "oos_walkforward"
        selected = oos_candidate
    if not _safe_report(risk_conversion):
        blockers.append("risk_no_order_safe")
    for source, name in [(parameter_sweep, "parameter_sweep_no_order_safe"), (oos, "oos_no_order_safe"), (robustness, "robustness_no_order_safe"), (backtest, "backtest_no_order_safe"), (frozen, "frozen_no_order_safe")]:
        if source and not _safe_report(source):
            blockers.append(name)
    if oos.get("status") != "OOS_WALKFORWARD_PASS":
        blockers.append("oos_walkforward_pass")
    if robustness.get("status") != "ROBUSTNESS_STRESS_PASS":
        blockers.append("robustness_stress_pass")
    if not _risk_guard_hard_safety_pass(risk_guard):
        blockers.append("risk_guard_hard_safety_pass")
    if selected_evidence_type == "parameter_sweep" and oos.get("status") != "OOS_WALKFORWARD_PASS":
        blockers.append("oos_walkforward_pass")
    candidate_id = selected.get("candidate_id") or robustness.get("candidate_id") or risk_conversion.get("top_conversion", {}).get("candidate_id")
    evidence_summary = {
        "market": selected.get("market") or robustness.get("market"),
        "timeframe": selected.get("timeframe") or robustness.get("timeframe", "1d"),
        "recommended_exposure_cap": (selected.get("source_conversion") or selected.get("conversion") or {}).get("recommended_exposure_cap"),
        "estimated_cagr": (selected.get("source_conversion") or selected.get("conversion") or {}).get("estimated_cagr"),
        "estimated_mdd": (selected.get("source_conversion") or selected.get("conversion") or {}).get("estimated_mdd"),
        "oos_status": oos.get("status"),
        "oos_pass_fold_count": (selected.get("aggregate", {}) or {}).get("pass_fold_count"),
        "oos_positive_fold_count": (selected.get("aggregate", {}) or {}).get("positive_fold_count"),
        "oos_total_trade_count": (selected.get("aggregate", {}) or {}).get("total_trade_count"),
        "robustness_status": robustness.get("status"),
        "robustness_pass_count": robustness.get("pass_count"),
        "robustness_cost_pass_count": robustness.get("cost_pass_count"),
        "robustness_case_count": robustness.get("case_count"),
    }
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": "READY_FOR_HUMAN_GATEKEEPER_REVIEW" if not blockers else "BLOCKED",
        "candidate_id": candidate_id,
        "parent_candidate_id": selected.get("parent_candidate_id"),
        "selected_evidence_type": selected_evidence_type,
        "blockers": sorted(set(blockers)),
        "evidence_summary": evidence_summary,
        "readiness_checks": {"risk_guard_hard_safety_pass": _risk_guard_hard_safety_pass(risk_guard)},
        "single_next_action": "Human gatekeeper review for Bithumb shadow-review-only preflight." if not blockers else "Close Bithumb gatekeeper blockers before shadow preflight.",
        "no_order_assertions": dict(NO_ORDER_ASSERTIONS),
    }


def build_report() -> dict:
    return build_packet(
        read_json(RISK_JSON, {}),
        read_json(SWEEP_JSON, {}),
        read_json(OOS_JSON, {}),
        read_json(ROBUSTNESS_JSON, {}),
        read_json(BACKTEST_JSON, {}),
        read_json(FROZEN_JSON, {}),
        read_json(ACTION_PACKET_JSON, {}),
        read_json(RISK_GUARD_JSON, {"status": "PASS"}),
    )


def render_md(report: dict) -> str:
    return "\n".join(
        [
            "# Bithumb Current-Actionable Gatekeeper Review Packet",
            "",
            f"- Status: `{report['status']}`",
            f"- Candidate: `{report.get('candidate_id', 'none')}`",
            f"- Evidence type: `{report['selected_evidence_type']}`",
            f"- Blockers: `{', '.join(report['blockers']) if report['blockers'] else 'none'}`",
            f"- Single next action: {report['single_next_action']}",
            "",
        ]
    )


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "candidate_id": report["candidate_id"], "blockers": report["blockers"], "latest_json": str(REPORT_JSON), "no_order_assertions": report["no_order_assertions"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
