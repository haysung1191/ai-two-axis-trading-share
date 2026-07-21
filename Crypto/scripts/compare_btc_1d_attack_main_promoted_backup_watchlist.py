from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_attack_main_promoted_backup_review import (
    build_report as build_main_vs_backup_review,
)
from scripts.compare_btc_1d_post_spike_reopen_seed_pressure_reconciliation import (
    build_report as build_reopen_seed_pressure_reconciliation,
)


ANALYSIS_DIR = Path("analysis_results")


def _status_band(base_gap: float, cost20_gap: float, has_pressure: bool, replace_now: bool) -> str:
    if replace_now:
        return "replacement_open"
    if has_pressure and base_gap <= 0.10 and cost20_gap <= 0.08:
        return "pressure_watch"
    if has_pressure:
        return "quality_watch"
    return "baseline_hold"


def build_report() -> dict:
    review = build_main_vs_backup_review()
    reconciliation = build_reopen_seed_pressure_reconciliation()
    metrics = review["main_vs_promoted_backup_metrics"]
    verdict = review["promotion_pressure_verdict"]
    gate = review["promotion_pressure_gate"]

    base_gap = float(metrics["base_cagr_gap_to_main"])
    cost20_gap = float(metrics["cost20_cagr_gap_to_main"])
    remaining_base_gap_to_open = max(0.0, base_gap - float(gate["allowed_max_base_cagr_gap"]))
    remaining_cost20_gap_to_open = max(0.0, cost20_gap - float(gate["allowed_max_cost20_cagr_gap"]))
    status = _status_band(
        base_gap=base_gap,
        cost20_gap=cost20_gap,
        has_pressure=bool(verdict["promoted_backup_has_main_pressure"]),
        replace_now=bool(verdict["replace_attack_main_now"]),
    )
    lane_status = str(reconciliation["verdict"]["lane_status"])
    effective_has_pressure = bool(verdict["promoted_backup_has_main_pressure"])
    effective_next_step = str(verdict["next_step_now"])
    if lane_status == "revalidation_hold":
        status = "revalidation_hold"
        effective_has_pressure = False
        effective_next_step = str(reconciliation["verdict"]["next_step_now"])

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "watch_reference": dict(review["active_stack_reference"]),
        "pressure_watch_snapshot": {
            "status_band": status,
            "replace_attack_main_now": bool(verdict["replace_attack_main_now"]),
            "promoted_backup_has_main_pressure": effective_has_pressure,
            "next_step_now": effective_next_step,
            "remaining_base_cagr_gap_to_open": remaining_base_gap_to_open,
            "remaining_cost20_cagr_gap_to_open": remaining_cost20_gap_to_open,
            "lane_reconciliation_status": lane_status,
            "lane_framing_conflict": bool(reconciliation["lane_alignment"]["framing_conflict"]),
        },
        "watch_metrics": {
            "base_cagr_gap_to_main": base_gap,
            "cost20_cagr_gap_to_main": cost20_gap,
            "sharpe_edge_vs_main": float(metrics["sharpe_edge_vs_main"]),
            "mdd_improvement_vs_main": float(metrics["mdd_improvement_vs_main"]),
            "drift_improvement_vs_main": float(metrics["drift_improvement_vs_main"]),
        },
        "watch_thresholds": {
            "pressure_watch_max_base_gap": 0.10,
            "pressure_watch_max_cost20_gap": 0.08,
            "replacement_open_base_gap": float(gate["allowed_max_base_cagr_gap"]),
            "replacement_open_cost20_gap": float(gate["allowed_max_cost20_cagr_gap"]),
        },
        "lane_reconciliation": {
            "lane_status": lane_status,
            "reason": str(reconciliation["verdict"]["reason"]),
        },
        "decision_summary": [
            (
                "Promoted backup is in `revalidation_hold`: the reopen seed passed its seed-cycle lane, but failed the stricter main-pressure quality gate, so live pressure watch should pause."
                if status == "revalidation_hold"
                else
                "Promoted backup is in `pressure_watch`: quality edge is strong enough to monitor as a live main-pressure candidate, but return gap is still above replacement-open."
                if status == "pressure_watch"
                else "Promoted backup is in `replacement_open`: main replacement review can open immediately."
                if status == "replacement_open"
                else "Promoted backup is in `quality_watch`: quality edge exists, but return gap is still too wide for direct pressure."
                if status == "quality_watch"
                else "Promoted backup remains in `baseline_hold`: continue holding stack without pressure escalation."
            ),
            f"Remaining gap to open main replacement is base CAGR `{remaining_base_gap_to_open:.6f}` and cost20 CAGR `{remaining_cost20_gap_to_open:.6f}`.",
            f"Keep next action as `{effective_next_step}`.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    snapshot = report["pressure_watch_snapshot"]
    metrics = report["watch_metrics"]
    thresholds = report["watch_thresholds"]
    lines = [
        "# BTC 1d Attack Main Promoted Backup Watchlist",
        "",
        f"- Attack main: `{report['watch_reference']['attack_main']}`",
        f"- Promoted backup: `{report['watch_reference']['promoted_attack_backup']}`",
        f"- Status band: `{snapshot['status_band']}`",
        f"- Replace attack main now: `{snapshot['replace_attack_main_now']}`",
        f"- Promoted backup has main pressure: `{snapshot['promoted_backup_has_main_pressure']}`",
        f"- Next step now: `{snapshot['next_step_now']}`",
        "",
        "## Metrics",
        f"- Base CAGR gap to main: `{metrics['base_cagr_gap_to_main']}`",
        f"- Cost20 CAGR gap to main: `{metrics['cost20_cagr_gap_to_main']}`",
        f"- Sharpe edge vs main: `{metrics['sharpe_edge_vs_main']}`",
        f"- MDD improvement vs main: `{metrics['mdd_improvement_vs_main']}`",
        f"- Drift improvement vs main: `{metrics['drift_improvement_vs_main']}`",
        f"- Remaining base CAGR gap to open: `{snapshot['remaining_base_cagr_gap_to_open']}`",
        f"- Remaining cost20 CAGR gap to open: `{snapshot['remaining_cost20_cagr_gap_to_open']}`",
        "",
        "## Thresholds",
        f"- pressure_watch_max_base_gap: `{thresholds['pressure_watch_max_base_gap']}`",
        f"- pressure_watch_max_cost20_gap: `{thresholds['pressure_watch_max_cost20_gap']}`",
        f"- replacement_open_base_gap: `{thresholds['replacement_open_base_gap']}`",
        f"- replacement_open_cost20_gap: `{thresholds['replacement_open_cost20_gap']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_attack_main_promoted_backup_watchlist_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_attack_main_promoted_backup_watchlist_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "report": report,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
