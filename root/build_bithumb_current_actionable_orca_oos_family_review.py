from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")
OOS_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_oos_walkforward_latest.json"
REPORT_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_orca_oos_family_review_latest.json"
REPORT_MD = ROOT / "reports/model_factory/bithumb_current_actionable_orca_oos_family_review_latest.md"

NO_ORDER_ASSERTIONS = {
    "promotion_allowed_by_this_report": False,
    "paper_enabled_by_this_report": False,
    "live_allowed_by_this_report": False,
    "broker_submit_allowed_by_this_report": False,
    "private_submit_allowed_by_this_report": False,
    "real_orders_allowed_by_this_report": False,
}


def read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default or {}


def _safe_no_order_assertions(report: dict) -> bool:
    assertions = report.get("no_order_assertions", {})
    return all(assertions.get(key) is value for key, value in NO_ORDER_ASSERTIONS.items())


def _param_key(row: dict) -> tuple:
    params = row.get("parameters", {})
    return (
        params.get("lookback_bars"),
        params.get("hold_bars"),
        params.get("volume_window"),
        params.get("volume_ratio_floor"),
        params.get("momentum_threshold"),
        params.get("stop_loss"),
        params.get("take_profit"),
    )


def build_review(oos_report: dict | None = None, generated_at: str | None = None) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    oos_report = oos_report or read_json(OOS_JSON, {})
    blockers = []
    if not _safe_no_order_assertions(oos_report):
        blockers.append("source_has_no_order_permissions")
    if oos_report.get("status") != "OOS_WALKFORWARD_PASS":
        blockers.append("oos_walkforward_not_pass")
    pass_rows = [
        row
        for row in oos_report.get("evaluations", [])
        if row.get("status") == "OOS_CANDIDATE_PASS"
        and "orca" in str(row.get("candidate_id", "")).lower()
    ]
    distinct_parameter_count = len({_param_key(row) for row in pass_rows})
    if len(pass_rows) < 2:
        blockers.append("not_enough_orca_oos_pass_children")
    if distinct_parameter_count < 2:
        blockers.append("not_enough_distinct_orca_parameters")
    ranked = sorted(
        pass_rows,
        key=lambda row: (
            float((row.get("source_conversion") or {}).get("estimated_cagr", 0.0) or 0.0),
            int((row.get("aggregate") or {}).get("pass_fold_count", 0) or 0),
            int((row.get("aggregate") or {}).get("total_trade_count", 0) or 0),
        ),
        reverse=True,
    )
    status = "ORCA_OOS_FAMILY_REVIEW_READY" if not blockers else "BLOCKED"
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "source": str(OOS_JSON),
        "oos_pass_candidate_count": len(pass_rows),
        "distinct_parameter_count": distinct_parameter_count,
        "top_candidates": ranked[:5],
        "blockers": sorted(set(blockers)),
        "review_value": {
            "reduces_single_registered_candidate_dependency": len(pass_rows) >= 2 and distinct_parameter_count >= 2,
            "supports_shadow_wait_without_forcing_signal": True,
        },
        "single_next_action": "Review ORCA OOS pass family diversity for shadow-candidate registration readiness." if not blockers else "Continue repairing ORCA OOS family diversity before shadow registration.",
        "no_order_assertions": dict(NO_ORDER_ASSERTIONS),
    }


def render_md(report: dict) -> str:
    return "\n".join(
        [
            "# Bithumb Current-Actionable ORCA OOS Family Review",
            "",
            f"- Status: `{report['status']}`",
            f"- OOS pass candidates: `{report['oos_pass_candidate_count']}`",
            f"- Distinct parameters: `{report['distinct_parameter_count']}`",
            f"- Blockers: `{', '.join(report['blockers']) if report['blockers'] else 'none'}`",
            f"- Single next action: {report['single_next_action']}",
            "",
        ]
    )


def main() -> int:
    report = build_review()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(render_md(report), encoding="utf-8")
    print(json.dumps({"status": report["status"], "oos_pass_candidate_count": report["oos_pass_candidate_count"], "distinct_parameter_count": report["distinct_parameter_count"], "latest_json": str(REPORT_JSON), "no_order_assertions": report["no_order_assertions"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
