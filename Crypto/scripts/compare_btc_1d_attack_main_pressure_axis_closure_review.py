from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_attack_main_pressure_escalation_review import (
    build_report as build_escalation_review,
)


ANALYSIS_DIR = Path("analysis_results")

AXIS_FILES = {
    "challenger_reopen": "btc_1d_post_spike_challenger_main_pressure_reopen_batch_",
    "base_gap_recovery": "btc_1d_post_spike_backup_base_gap_recovery_batch_",
    "entry_timing": "btc_1d_post_spike_consolidation_breakout_main_pressure_entry_timing_batch_",
    "entry_strength": "btc_1d_post_spike_consolidation_breakout_main_pressure_entry_strength_batch_",
    "structure": "btc_1d_post_spike_consolidation_breakout_main_pressure_structure_batch_",
}


def _latest_json(prefix: str) -> Path:
    matches = sorted(ANALYSIS_DIR.glob(f"{prefix}*.json"))
    if not matches:
        raise FileNotFoundError(f"No analysis result found for prefix: {prefix}")
    return matches[-1]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _axis_summary(axis_name: str, path: Path) -> dict:
    payload = _load_json(path)
    best = dict(payload.get("best_variant", {}))
    best_label = str(best.get("variant_label", ""))
    base_gap = float(best.get("base_cagr_gap_to_main", 0.0))
    cost_gap = float(best.get("cost20_cagr_gap_to_main", 0.0))
    quality_passed = bool(best.get("quality_pressure_passed", False))
    replacement_open = bool(best.get("replacement_open_passed", False))
    anchor_retained = best_label in {"hold36_anchor", "active_anchor", "hold36"}

    closure_reason = (
        "anchor_retained_same_or_better"
        if anchor_retained
        else "best_variant_still_failed_replacement_open"
        if quality_passed and not replacement_open
        else "best_variant_failed_quality_gate"
    )

    return {
        "axis_name": axis_name,
        "source_json": str(path),
        "best_variant_label": best_label,
        "best_base_cagr_gap_to_main": base_gap,
        "best_cost20_cagr_gap_to_main": cost_gap,
        "quality_pressure_passed": quality_passed,
        "replacement_open_passed": replacement_open,
        "anchor_retained": anchor_retained,
        "axis_closed": True,
        "closure_reason": closure_reason,
    }


def build_report() -> dict:
    escalation = build_escalation_review()
    axis_summaries = []
    for axis_name, prefix in AXIS_FILES.items():
        axis_summaries.append(_axis_summary(axis_name, _latest_json(prefix)))

    remaining_base_gap = float(escalation["remaining_to_open"]["remaining_base_cagr_gap"])
    all_closed = all(bool(item["axis_closed"]) for item in axis_summaries)
    anchor_retained_axes = [item["axis_name"] for item in axis_summaries if bool(item["anchor_retained"])]
    quality_failed_axes = [
        item["axis_name"]
        for item in axis_summaries
        if not bool(item["quality_pressure_passed"])
    ]

    next_step_now = (
        "formalize_hold36_pressure_watch_ceiling"
        if all_closed and remaining_base_gap > 0.0
        else "continue_hold36_local_axis_search"
    )

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "closure_reference": {
            "attack_main": escalation["escalation_reference"]["attack_main"],
            "promoted_backup": escalation["escalation_reference"]["promoted_attack_backup"],
            "monitoring_candidate": escalation["escalation_reference"].get("monitoring_candidate"),
        },
        "open_blocker_state": {
            "primary_blocker": escalation["watch_status"]["primary_blocker"],
            "remaining_base_cagr_gap": remaining_base_gap,
            "remaining_cost20_cagr_gap": float(escalation["remaining_to_open"]["remaining_cost20_cagr_gap"]),
        },
        "axis_closure_summary": {
            "evaluated_axis_count": len(axis_summaries),
            "all_current_hold36_axes_closed": all_closed,
            "anchor_retained_axes": anchor_retained_axes,
            "quality_failed_axes": quality_failed_axes,
            "next_step_now": next_step_now,
        },
        "closed_axes": axis_summaries,
        "decision_summary": [
            f"All currently explored hold36-local axes are `{'closed' if all_closed else 'not_closed'}`.",
            f"Primary blocker remains `{escalation['watch_status']['primary_blocker']}` with remaining base gap `{remaining_base_gap:.6f}`.",
            (
                "Next step is to formalize the current hold36 pressure-watch ceiling because all explored local axes are closed."
                if next_step_now == "formalize_hold36_pressure_watch_ceiling"
                else "Next step is to continue searching additional hold36-local axes."
            ),
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    summary = report["axis_closure_summary"]
    blocker = report["open_blocker_state"]
    lines = [
        "# BTC 1d Attack Main Pressure Axis Closure Review",
        "",
        f"- Attack main: `{report['closure_reference']['attack_main']}`",
        f"- Promoted backup: `{report['closure_reference']['promoted_backup']}`",
        f"- Monitoring candidate: `{report['closure_reference']['monitoring_candidate']}`",
        f"- Primary blocker: `{blocker['primary_blocker']}`",
        f"- Remaining base CAGR gap: `{blocker['remaining_base_cagr_gap']}`",
        f"- Remaining cost20 CAGR gap: `{blocker['remaining_cost20_cagr_gap']}`",
        f"- All current hold36 axes closed: `{summary['all_current_hold36_axes_closed']}`",
        f"- Next step now: `{summary['next_step_now']}`",
        "",
        "## Closed Axes",
    ]
    for axis in report["closed_axes"]:
        lines.append(
            f"- {axis['axis_name']}: best=`{axis['best_variant_label']}` "
            f"base_gap=`{axis['best_base_cagr_gap_to_main']}` "
            f"quality=`{axis['quality_pressure_passed']}` "
            f"replacement_open=`{axis['replacement_open_passed']}` "
            f"reason=`{axis['closure_reason']}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_attack_main_pressure_axis_closure_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_attack_main_pressure_axis_closure_review_{stamp}.md"
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
