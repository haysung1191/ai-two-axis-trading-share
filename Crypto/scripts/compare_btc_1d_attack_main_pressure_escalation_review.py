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
from scripts.compare_btc_1d_attack_main_promoted_backup_watchlist import (
    build_report as build_pressure_watchlist,
)


ANALYSIS_DIR = Path("analysis_results")


def build_report() -> dict:
    review = build_main_vs_backup_review()
    watchlist = build_pressure_watchlist()

    metrics = review["main_vs_promoted_backup_metrics"]
    gate = review["promotion_pressure_gate"]
    watch = watchlist["pressure_watch_snapshot"]

    checks = {
        "quality_edge_sharpe_ready": float(metrics["sharpe_edge_vs_main"]) >= float(gate["required_min_sharpe_edge"]),
        "quality_edge_mdd_ready": float(metrics["mdd_improvement_vs_main"]) >= float(gate["required_min_mdd_improvement"]),
        "quality_edge_drift_ready": float(metrics["drift_improvement_vs_main"]) >= float(gate["required_min_drift_improvement"]),
        "base_cagr_gap_ready": float(metrics["base_cagr_gap_to_main"]) <= float(gate["allowed_max_base_cagr_gap"]),
        "cost20_cagr_gap_ready": float(metrics["cost20_cagr_gap_to_main"]) <= float(gate["allowed_max_cost20_cagr_gap"]),
        "lane_reconciliation_ready": str(watch["status_band"]) != "revalidation_hold",
    }

    bottlenecks: list[str] = []
    if not checks["lane_reconciliation_ready"]:
        bottlenecks.append("lane_reconciliation")
    if not checks["base_cagr_gap_ready"]:
        bottlenecks.append("base_cagr_gap")
    if not checks["cost20_cagr_gap_ready"]:
        bottlenecks.append("cost20_cagr_gap")
    if not checks["quality_edge_sharpe_ready"]:
        bottlenecks.append("sharpe_edge")
    if not checks["quality_edge_mdd_ready"]:
        bottlenecks.append("mdd_improvement")
    if not checks["quality_edge_drift_ready"]:
        bottlenecks.append("drift_improvement")

    escalation_ready = all(checks.values())
    primary_blocker = bottlenecks[0] if bottlenecks else "none"

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "escalation_reference": dict(review["active_stack_reference"]),
        "watch_status": {
            "status_band": watch["status_band"],
            "next_step_now": (
                "open_attack_main_replacement_review"
                if escalation_ready
                else "continue_revalidation_hold"
                if str(watch["status_band"]) == "revalidation_hold"
                else "continue_pressure_watch"
            ),
            "escalation_ready": escalation_ready,
            "primary_blocker": primary_blocker,
            "open_bottlenecks": bottlenecks,
        },
        "escalation_checks": checks,
        "remaining_to_open": {
            "remaining_base_cagr_gap": float(watch["remaining_base_cagr_gap_to_open"]),
            "remaining_cost20_cagr_gap": float(watch["remaining_cost20_cagr_gap_to_open"]),
        },
        "decision_summary": [
            (
                "Attack main replacement escalation can open now because all quality and return gates are satisfied."
                if escalation_ready
                else f"Attack main replacement escalation stays closed because the primary blocker is `{primary_blocker}`."
            ),
            f"Open bottlenecks: `{bottlenecks or ['none']}`.",
            f"Remaining return gap to open is base `{watch['remaining_base_cagr_gap_to_open']:.6f}` and cost20 `{watch['remaining_cost20_cagr_gap_to_open']:.6f}`.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    status = report["watch_status"]
    checks = report["escalation_checks"]
    remaining = report["remaining_to_open"]
    lines = [
        "# BTC 1d Attack Main Pressure Escalation Review",
        "",
        f"- Attack main: `{report['escalation_reference']['attack_main']}`",
        f"- Promoted backup: `{report['escalation_reference']['promoted_attack_backup']}`",
        f"- Status band: `{status['status_band']}`",
        f"- Escalation ready: `{status['escalation_ready']}`",
        f"- Primary blocker: `{status['primary_blocker']}`",
        f"- Next step now: `{status['next_step_now']}`",
        "",
        "## Checks",
        *(f"- {key}: `{value}`" for key, value in checks.items()),
        "",
        "## Remaining To Open",
        f"- remaining_base_cagr_gap: `{remaining['remaining_base_cagr_gap']}`",
        f"- remaining_cost20_cagr_gap: `{remaining['remaining_cost20_cagr_gap']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_attack_main_pressure_escalation_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_attack_main_pressure_escalation_review_{stamp}.md"
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
