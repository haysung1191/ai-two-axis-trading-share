from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import build_bithumb_current_actionable_oos_walkforward as oos_builder

ROOT = Path(__file__).resolve().parent
KST = ZoneInfo("Asia/Seoul")
OOS_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_oos_walkforward_latest.json"
REPORT_JSON = ROOT / "reports/model_factory/bithumb_current_actionable_robustness_stress_latest.json"
REPORT_MD = ROOT / "reports/model_factory/bithumb_current_actionable_robustness_stress_latest.md"

NO_ORDER_ASSERTIONS = {
    "promotion_allowed_by_this_report": False,
    "paper_enabled_by_this_report": False,
    "live_allowed_by_this_report": False,
    "broker_submit_allowed_by_this_report": False,
    "private_submit_allowed_by_this_report": False,
    "real_orders_allowed_by_this_report": False,
}

STRESS_CASES = [
    {"case_id": "base"},
    {"case_id": "higher_cost", "round_trip_cost_rate": 0.005},
    {"case_id": "stricter_momentum", "momentum_threshold_multiplier": 1.25},
    {"case_id": "looser_momentum", "momentum_threshold_multiplier": 0.85},
    {"case_id": "shorter_hold", "hold_bars_delta": -1},
    {"case_id": "longer_hold", "hold_bars_delta": 2},
    {"case_id": "tighter_stop", "stop_loss_multiplier": 0.75},
]


def read_json(path: Path, default: dict | None = None) -> dict:
    if not path.exists():
        return default or {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError:
        return default or {}


backtest = SimpleNamespace(fetch_candles=oos_builder.fetch_candles)


def apply_stress_parameters(base: dict, stress: dict) -> dict:
    updated = dict(base)
    if "hold_bars_delta" in stress:
        updated["hold_bars"] = max(1, int(updated.get("hold_bars", 1) or 1) + int(stress["hold_bars_delta"]))
    if "momentum_threshold_multiplier" in stress:
        updated["momentum_threshold"] = float(updated.get("momentum_threshold", 0.0) or 0.0) * float(stress["momentum_threshold_multiplier"])
    if "stop_loss_multiplier" in stress:
        updated["stop_loss"] = abs(float(updated.get("stop_loss", 0.12) or 0.12)) * float(stress["stop_loss_multiplier"])
    if "round_trip_cost_rate" in stress:
        updated["round_trip_cost_rate"] = float(stress["round_trip_cost_rate"])
    return updated


def _source_candidate(oos_report: dict) -> dict:
    if oos_report.get("top_oos"):
        return oos_report["top_oos"]
    candidates = [row for row in oos_report.get("evaluations", []) if row.get("status") == "OOS_CANDIDATE_PASS"]
    return sorted(
        candidates,
        key=lambda row: (
            float((row.get("source_conversion") or {}).get("estimated_cagr", 0.0) or 0.0),
            int((row.get("aggregate") or {}).get("pass_fold_count", 0) or 0),
        ),
        reverse=True,
    )[0] if candidates else {}


def _case_pass(metrics: dict) -> bool:
    return (
        metrics.get("trade_count", 0) >= 3
        and metrics.get("mdd", 0.0) >= -0.30
        and metrics.get("profit_factor", 0.0) >= 1.1
        and metrics.get("total_return", 0.0) > 0
    )


def build_report(generated_at: str | None = None) -> dict:
    generated_at = generated_at or datetime.now(tz=KST).isoformat(timespec="seconds")
    oos_report = read_json(OOS_JSON, {})
    candidate = _source_candidate(oos_report)
    cases = []
    if candidate:
        candles = backtest.fetch_candles(candidate.get("market"), candidate.get("timeframe", "1d"))
        for stress in STRESS_CASES:
            params = apply_stress_parameters(candidate.get("parameters", {}), stress)
            metrics = oos_builder._trade_metrics(candles, params) if candles else {
                "total_return": 0.0,
                "cagr": 0.0,
                "mdd": 0.0,
                "trade_count": 0,
                "profit_factor": 0.0,
                "win_rate": 0.0,
            }
            passed = _case_pass(metrics)
            cases.append({"case_id": stress["case_id"], "parameters": params, "metrics": metrics, "passed": passed})
    pass_count = sum(1 for row in cases if row["passed"])
    cost_pass_count = sum(1 for row in cases if row["passed"] and "cost" in row["case_id"])
    status = "ROBUSTNESS_STRESS_PASS" if pass_count >= 4 and cost_pass_count >= 1 else "ROBUSTNESS_STRESS_ITERATE"
    return {
        "schema_version": "1.0.0",
        "generated_at": generated_at,
        "status": status,
        "source_oos": {
            "status": oos_report.get("status"),
            "generated_at": oos_report.get("generated_at") or oos_report.get("generated_at_utc"),
            "top_candidate_id": (oos_report.get("top_oos") or {}).get("candidate_id"),
            "top_market": (oos_report.get("top_oos") or {}).get("market"),
            "top_timeframe": (oos_report.get("top_oos") or {}).get("timeframe"),
        },
        "candidate_id": candidate.get("candidate_id"),
        "parent_candidate_id": candidate.get("parent_candidate_id"),
        "market": candidate.get("market"),
        "timeframe": candidate.get("timeframe", "1d"),
        "pass_count": pass_count,
        "cost_pass_count": cost_pass_count,
        "case_count": len(STRESS_CASES),
        "cases": cases,
        "blockers": [] if status == "ROBUSTNESS_STRESS_PASS" else ["robustness_stress_pass"],
        "single_next_action": "Keep this candidate in model verification for tiny-live precondition review." if status == "ROBUSTNESS_STRESS_PASS" else "Repair robustness stress before tiny-live precondition review.",
        "no_order_assertions": dict(NO_ORDER_ASSERTIONS),
    }


def render_md(report: dict) -> str:
    return "\n".join(
        [
            "# Bithumb Current-Actionable Robustness Stress",
            "",
            f"- Status: `{report['status']}`",
            f"- Candidate: `{report.get('candidate_id', 'none')}`",
            f"- Source OOS: `{(report.get('source_oos') or {}).get('status')}` / `{(report.get('source_oos') or {}).get('generated_at')}` / top `{(report.get('source_oos') or {}).get('top_candidate_id')}` `{(report.get('source_oos') or {}).get('top_market')}`",
            f"- Pass count: `{report['pass_count']}` / `{report['case_count']}`",
            f"- Cost pass count: `{report['cost_pass_count']}`",
            f"- Single next action: {report['single_next_action']}",
            "",
        ]
    )


def write_text_atomic(path: Path, text: str) -> None:
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def write_json_atomic(path: Path, payload: dict) -> None:
    write_text_atomic(path, json.dumps(payload, indent=2))


def main() -> int:
    report = build_report()
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomic(REPORT_JSON, report)
    write_text_atomic(REPORT_MD, render_md(report))
    print(json.dumps({"status": report["status"], "candidate_id": report["candidate_id"], "pass_count": report["pass_count"], "cost_pass_count": report["cost_pass_count"], "case_count": report["case_count"], "latest_json": str(REPORT_JSON), "no_order_assertions": report["no_order_assertions"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
