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
from scripts.compare_btc_1d_hold36_pressure_watch_ceiling import (
    build_report as build_hold36_pressure_watch_ceiling,
)


ANALYSIS_DIR = Path("analysis_results")


def build_report() -> dict:
    ceiling = build_hold36_pressure_watch_ceiling()
    closure = build_axis_closure_review()

    reference = ceiling["ceiling_reference"]
    pressure = ceiling["pressure_watch_ceiling"]
    metrics = ceiling["ceiling_metrics"]
    closed_axes = [axis["axis_name"] for axis in closure["closed_axes"]]

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "handoff_reference": {
            "attack_main": reference["attack_main"],
            "active_backup": reference["active_backup"],
            "monitoring_candidate": reference["monitoring_candidate"],
        },
        "local_ceiling_status": {
            "status_band": pressure["status_band"],
            "ceiling_confirmed": pressure["ceiling_confirmed"],
            "primary_blocker": pressure["primary_blocker"],
            "remaining_base_cagr_gap_to_open": pressure["remaining_base_cagr_gap_to_open"],
            "remaining_cost20_cagr_gap_to_open": pressure["remaining_cost20_cagr_gap_to_open"],
            "closed_local_axes": closed_axes,
            "do_not_repeat_local_loop": True,
            "next_step_now": "open_only_new_family_or_wider_frame_search",
        },
        "handoff_metrics": {
            "base_cagr_gap_to_main": metrics["base_cagr_gap_to_main"],
            "cost20_cagr_gap_to_main": metrics["cost20_cagr_gap_to_main"],
            "sharpe_edge_vs_main": metrics["sharpe_edge_vs_main"],
            "mdd_improvement_vs_main": metrics["mdd_improvement_vs_main"],
            "drift_improvement_vs_main": metrics["drift_improvement_vs_main"],
        },
        "handoff_rules": {
            "continue_allowed_only_if": [
                "a genuinely new family opens",
                "a materially wider search frame opens",
                "a non-local structural hypothesis appears",
            ],
            "do_not_restart": [
                "challenger_reopen",
                "base_gap_recovery",
                "entry_timing",
                "entry_strength",
                "structure",
            ],
            "reason": (
                "The current hold36 backup is the confirmed local pressure-watch ceiling, so repeating the same local-axis "
                "loop is no longer a productive use of search budget."
            ),
        },
        "decision_summary": [
            f"`{reference['active_backup']}` is the confirmed local pressure-watch ceiling under the current search frame.",
            f"The only remaining blocker is `{pressure['primary_blocker']}` with remaining base gap `{pressure['remaining_base_cagr_gap_to_open']:.6f}`.",
            "Do not reopen the same local-axis loop from this point; only continue if a new family, wider frame, or non-local structural hypothesis is introduced.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    status = report["local_ceiling_status"]
    metrics = report["handoff_metrics"]
    rules = report["handoff_rules"]
    lines = [
        "# BTC 1d Hold36 Local Ceiling Handoff",
        "",
        f"- Attack main: `{report['handoff_reference']['attack_main']}`",
        f"- Active backup: `{report['handoff_reference']['active_backup']}`",
        f"- Status band: `{status['status_band']}`",
        f"- Ceiling confirmed: `{status['ceiling_confirmed']}`",
        f"- Primary blocker: `{status['primary_blocker']}`",
        f"- Remaining base CAGR gap: `{status['remaining_base_cagr_gap_to_open']}`",
        f"- Remaining cost20 CAGR gap: `{status['remaining_cost20_cagr_gap_to_open']}`",
        f"- Do not repeat local loop: `{status['do_not_repeat_local_loop']}`",
        f"- Next step now: `{status['next_step_now']}`",
        "",
        "## Metrics",
        f"- Base CAGR gap to main: `{metrics['base_cagr_gap_to_main']}`",
        f"- Cost20 CAGR gap to main: `{metrics['cost20_cagr_gap_to_main']}`",
        f"- Sharpe edge vs main: `{metrics['sharpe_edge_vs_main']}`",
        f"- MDD improvement vs main: `{metrics['mdd_improvement_vs_main']}`",
        f"- Drift improvement vs main: `{metrics['drift_improvement_vs_main']}`",
        "",
        "## Do Not Restart",
    ]
    for item in rules["do_not_restart"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Continue Allowed Only If"])
    for item in rules["continue_allowed_only_if"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_hold36_local_ceiling_handoff_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_hold36_local_ceiling_handoff_{stamp}.md"
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
