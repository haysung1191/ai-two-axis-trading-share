from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_attack_main_pressure_axis_closure_review import (
    build_report as build_axis_closure_review,
)
from scripts.compare_btc_1d_attack_main_promoted_backup_watchlist import (
    build_report as build_promoted_backup_watchlist,
)


ANALYSIS_DIR = Path("analysis_results")


def build_report() -> dict:
    watchlist = build_promoted_backup_watchlist()
    closure = build_axis_closure_review()

    snapshot = watchlist["pressure_watch_snapshot"]
    metrics = watchlist["watch_metrics"]
    blocker = closure["open_blocker_state"]
    summary = closure["axis_closure_summary"]

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "ceiling_reference": {
            "attack_main": watchlist["watch_reference"]["attack_main"],
            "active_backup": watchlist["watch_reference"]["promoted_attack_backup"],
            "monitoring_candidate": watchlist["watch_reference"]["monitoring_candidate"],
        },
        "pressure_watch_ceiling": {
            "status_band": snapshot["status_band"],
            "ceiling_confirmed": bool(summary["all_current_hold36_axes_closed"]) and str(snapshot["status_band"]) == "pressure_watch",
            "primary_blocker": blocker["primary_blocker"],
            "remaining_base_cagr_gap_to_open": float(blocker["remaining_base_cagr_gap"]),
            "remaining_cost20_cagr_gap_to_open": float(blocker["remaining_cost20_cagr_gap"]),
            "local_axis_count_closed": int(summary["evaluated_axis_count"]),
            "next_step_now": str(summary["next_step_now"]),
        },
        "ceiling_metrics": {
            "base_cagr_gap_to_main": float(metrics["base_cagr_gap_to_main"]),
            "cost20_cagr_gap_to_main": float(metrics["cost20_cagr_gap_to_main"]),
            "sharpe_edge_vs_main": float(metrics["sharpe_edge_vs_main"]),
            "mdd_improvement_vs_main": float(metrics["mdd_improvement_vs_main"]),
            "drift_improvement_vs_main": float(metrics["drift_improvement_vs_main"]),
        },
        "closed_axes": list(closure["closed_axes"]),
        "decision_summary": [
            f"`{watchlist['watch_reference']['promoted_attack_backup']}` remains the confirmed `pressure_watch` ceiling inside the current local search range.",
            f"All explored local axes are closed and the only blocker left is `{blocker['primary_blocker']}` with remaining base gap `{blocker['remaining_base_cagr_gap']:.6f}`.",
            "Do not continue the same local-axis search loop from this point; treat the current hold36 candidate as the local ceiling until a genuinely new family or wider search frame opens.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    ceiling = report["pressure_watch_ceiling"]
    metrics = report["ceiling_metrics"]
    lines = [
        "# BTC 1d Hold36 Pressure Watch Ceiling",
        "",
        f"- Attack main: `{report['ceiling_reference']['attack_main']}`",
        f"- Active backup: `{report['ceiling_reference']['active_backup']}`",
        f"- Monitoring candidate: `{report['ceiling_reference']['monitoring_candidate']}`",
        f"- Status band: `{ceiling['status_band']}`",
        f"- Ceiling confirmed: `{ceiling['ceiling_confirmed']}`",
        f"- Primary blocker: `{ceiling['primary_blocker']}`",
        f"- Remaining base CAGR gap: `{ceiling['remaining_base_cagr_gap_to_open']}`",
        f"- Remaining cost20 CAGR gap: `{ceiling['remaining_cost20_cagr_gap_to_open']}`",
        f"- Local axes closed: `{ceiling['local_axis_count_closed']}`",
        f"- Next step now: `{ceiling['next_step_now']}`",
        "",
        "## Metrics",
        f"- Base CAGR gap to main: `{metrics['base_cagr_gap_to_main']}`",
        f"- Cost20 CAGR gap to main: `{metrics['cost20_cagr_gap_to_main']}`",
        f"- Sharpe edge vs main: `{metrics['sharpe_edge_vs_main']}`",
        f"- MDD improvement vs main: `{metrics['mdd_improvement_vs_main']}`",
        f"- Drift improvement vs main: `{metrics['drift_improvement_vs_main']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_hold36_pressure_watch_ceiling_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_hold36_pressure_watch_ceiling_{stamp}.md"
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
