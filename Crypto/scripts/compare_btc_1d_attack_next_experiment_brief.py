from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_attack_conversion_candidates import (
    build_attack_conversion_screen,
)
from scripts.compare_btc_1d_attack_main_promoted_backup_review import (
    build_report as build_attack_main_promoted_backup_review,
)
from scripts.compare_btc_1d_near_miss_priority_screen import (
    build_report as build_near_miss_priority_report,
)
from scripts.compare_btc_1d_post_spike_bridge_backup_negative_window_repair_review import (
    build_report as build_bridge_backup_negative_window_repair_review,
)
from scripts.compare_btc_1d_research_stack_operating_brief import (
    build_report as build_research_stack_operating_brief,
)


ANALYSIS_DIR = Path("analysis_results")


def _family_for_label(label: str) -> str:
    if label == "trend_dip_reversal_breakout_tighter_stop_mid_hold":
        return "trend_dip_reversal_breakout"
    if label == "volatility_spike_reversal_continuation_slower_trend":
        return "volatility_spike_reversal_continuation"
    return "unknown"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_post_pivot_brief(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    latest_path = analysis_dir / "btc_1d_attack_post_pivot_next_family_brief_latest.json"
    if latest_path.exists():
        return _load_json(latest_path)

    matches = sorted(
        analysis_dir.glob("btc_1d_attack_post_pivot_next_family_brief_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not matches:
        raise FileNotFoundError("No attack post-pivot next-family brief artifact found.")
    return _load_json(matches[0])


def build_report() -> dict:
    near_miss = build_near_miss_priority_report()
    research_stack = build_research_stack_operating_brief()
    attack_conversion = build_attack_conversion_screen(analysis_results_dir=ANALYSIS_DIR)
    promoted_backup_review = build_attack_main_promoted_backup_review()
    bridge_backup_repair_review = build_bridge_backup_negative_window_repair_review()
    post_pivot_brief = _load_post_pivot_brief()

    primary = dict(near_miss["priority_rows"][0])
    secondary = dict(near_miss["priority_rows"][1])
    attack_frontier = str(research_stack["operating_brief"]["attack_frontier"])
    attack_backup = str(research_stack["operating_brief"]["attack_backup"])
    defensive_hold_value = research_stack["operating_brief"].get("defensive_hold")
    if defensive_hold_value is None:
        defensive_hold_value = (
            research_stack.get("models", {}).get("defensive_hold", {}).get("label")
            or "volatility_expansion_pullthrough_shorter_hold"
        )
    defensive_hold = str(
        defensive_hold_value
    )

    primary_label = str(primary["label"])
    secondary_label = str(secondary["label"])
    primary_family = _family_for_label(primary_label)
    secondary_family = _family_for_label(secondary_label)
    promoted_backup_verdict = dict(promoted_backup_review["promotion_pressure_verdict"])
    promoted_backup_risk_watch = dict(promoted_backup_review["promoted_backup_risk_watch"])
    bridge_repair_verdict = dict(bridge_backup_repair_review["repair_review_verdict"])
    post_pivot_mode = str(post_pivot_brief["next_family_brief"]["post_pivot_mode"])
    new_family_seed = str(post_pivot_brief["next_family_brief"]["selected_seed_label"])
    new_family_goal = str(post_pivot_brief["next_family_brief"]["new_family_search_goal"])

    conversion_rows = {
        str(row["family"]): row for row in attack_conversion["rows"]
    }
    primary_conversion = conversion_rows.get(primary_family, {})
    secondary_conversion = conversion_rows.get(secondary_family, {})

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "attack_frontier": attack_frontier,
        "attack_backup": attack_backup,
        "defensive_hold": defensive_hold,
        "attack_post_pivot_context": {
            "post_pivot_mode": post_pivot_mode,
            "selected_seed_label": new_family_seed,
            "new_family_search_goal": new_family_goal,
        },
        "attack_backup_repair_context": {
            "attack_backup_label": attack_backup,
            "negative_window_watch": bool(promoted_backup_risk_watch["negative_window_watch"]),
            "negative_walk_forward_windows": list(promoted_backup_risk_watch["negative_walk_forward_windows"]),
            "bridge_backup_repair_completed_variant_count": int(
                bridge_backup_repair_review["repair_review_reference"]["completed_variant_count"]
            ),
            "bridge_backup_local_repair_next_step": str(bridge_repair_verdict["next_step_now"]),
            "bridge_backup_local_repair_reason": str(bridge_repair_verdict["reason"]),
        },
        "next_experiment_brief": {
            "primary_attack_experiment": {
                "label": primary_label,
                "family": primary_family,
                "priority_read": primary["priority_read"],
                "candidate_stage_status": primary["candidate_stage_status"],
                "base_cagr": primary["base_cagr"],
                "base_mdd": primary["base_mdd"],
                "base_sharpe": primary["base_sharpe"],
                "cagr_gap_to_attack_main_pct": primary["cagr_gap_to_attack_main_pct"],
                "mdd_gap_to_attack_main_pct": primary["mdd_gap_to_attack_main_pct"],
                "hypothesis": (
                    "Re-open the trend-dip reversal breakout family as the next attack experiment, "
                    "because the current bridge-backup local repair neighborhood is now closed and this family already has candidate-stage evidence."
                ),
                "mutation_focus": [
                    "outside_bridge_backup_local_repair_neighborhood",
                    "drawdown_compression_first",
                    "entry_selectivity_tighter_than_current_hold",
                    "preserve_candidate_stage_validation_depth",
                ],
                "success_gate": {
                    "target_role": "attack_reopen_candidate",
                    "must_improve": "max_drawdown",
                    "ceiling_mdd_gap_to_attack_main_pct": 5.0,
                    "floor_validation_depth": "candidate_stage_retest",
                },
                "conversion_context": {
                    "family_verdict": primary_conversion.get("attack_conversion_label", "unknown"),
                    "best_variant_label": primary_conversion.get("variant_label", "n/a"),
                },
            },
            "secondary_attack_experiment": {
                "label": secondary_label,
                "family": secondary_family,
                "priority_read": secondary["priority_read"],
                "candidate_stage_status": secondary["candidate_stage_status"],
                "base_cagr": secondary["base_cagr"],
                "base_mdd": secondary["base_mdd"],
                "base_sharpe": secondary["base_sharpe"],
                "cagr_gap_to_attack_main_pct": secondary["cagr_gap_to_attack_main_pct"],
                "mdd_gap_to_attack_main_pct": secondary["mdd_gap_to_attack_main_pct"],
                "hypothesis": (
                    "Keep spike reversal continuation as the secondary upside experiment only after the "
                    "trend-dip retest, because it still has weaker validation depth and wider drawdown."
                ),
                "mutation_focus": [
                    "upside_preservation",
                    "candidate_stage_promotion_first",
                    "drawdown_guardrails_before_attack_promotion",
                ],
                "conversion_context": {
                    "family_verdict": secondary_conversion.get("attack_conversion_label", "unknown"),
                    "best_variant_label": secondary_conversion.get("variant_label", "n/a"),
                },
            },
        },
        "decision_summary": [
            f"{attack_backup} remains the active backup, but negative windows `{promoted_backup_risk_watch['negative_walk_forward_windows']}` still keep it under repair watch.",
            f"Completed local bridge-backup repairs failed to clear that window, and the trend-dip primary lane is now exhausted, so the next aggressive experiment should move to a new family seed.",
            f"`{new_family_seed}` is the next search seed because the post-pivot brief has already closed the trend-dip lane and deferred the spike-reversal lane.",
            f"{secondary_label} stays as the secondary upside experiment until it gains more validation depth.",
            f"{attack_frontier} remains the live attack frontier and {attack_backup} stays the backup while {defensive_hold} remains the defensive hold.",
        ],
        "experiment_verdict": {
            "next_attack_reopen_candidate": None,
            "next_attack_new_family_seed": new_family_seed,
            "secondary_upside_candidate": secondary_label,
            "frontier_remains_fixed": attack_frontier,
            "attack_backup_local_repair_next_step": str(bridge_repair_verdict["next_step_now"]),
            "attack_backup_repair_watch_active": bool(promoted_backup_risk_watch["negative_window_watch"]),
            "attack_backup_local_repair_closed": bool(bridge_repair_verdict["completed_local_repair_axes_failed"]),
            "reason": (
                "The next attack iteration should shift to a new-family search from the defensive hold seed, "
                "because the active backup still carries a negative-window watch, the completed local bridge repairs failed, and the trend-dip primary retest has already closed without beating the anchor."
            ),
        },
    }
    return report


def _render_markdown(report: dict) -> str:
    primary = report["next_experiment_brief"]["primary_attack_experiment"]
    secondary = report["next_experiment_brief"]["secondary_attack_experiment"]
    return "\n".join(
        [
            "# BTC 1d Attack Next Experiment Brief",
            "",
            f"- Attack frontier: `{report['attack_frontier']}`",
            f"- Attack backup: `{report['attack_backup']}`",
            f"- Defensive hold: `{report['defensive_hold']}`",
            f"- Attack backup repair next step: `{report['experiment_verdict']['attack_backup_local_repair_next_step']}`",
            f"- Next attack new-family seed: `{report['experiment_verdict']['next_attack_new_family_seed']}`",
            f"- Secondary upside candidate: `{report['experiment_verdict']['secondary_upside_candidate']}`",
            f"- Reason: {report['experiment_verdict']['reason']}",
            "",
            "## Primary Attack Experiment",
            f"- Label: `{primary['label']}`",
            f"- Family: `{primary['family']}`",
            f"- Priority read: `{primary['priority_read']}`",
            f"- Candidate stage: `{primary['candidate_stage_status']}`",
            f"- Base: `{primary['base_cagr']:.4f}` CAGR / `{primary['base_mdd']:.4f}` MDD / Sharpe `{primary['base_sharpe']:.4f}`",
            f"- Gap to attack main: CAGR `{primary['cagr_gap_to_attack_main_pct']:.2f}%`, MDD `{primary['mdd_gap_to_attack_main_pct']:.2f}%`",
            f"- Hypothesis: {primary['hypothesis']}",
            f"- Mutation focus: `{' | '.join(primary['mutation_focus'])}`",
            (
                "- Success gate: "
                f"`{primary['success_gate']['target_role']}` | improve `{primary['success_gate']['must_improve']}` | "
                f"MDD gap <= `{primary['success_gate']['ceiling_mdd_gap_to_attack_main_pct']}`"
            ),
            (
                "- Conversion context: "
                f"`{primary['conversion_context']['family_verdict']}` | best variant `{primary['conversion_context']['best_variant_label']}`"
            ),
            "",
            "## Secondary Experiment",
            f"- Label: `{secondary['label']}`",
            f"- Family: `{secondary['family']}`",
            f"- Priority read: `{secondary['priority_read']}`",
            f"- Candidate stage: `{secondary['candidate_stage_status']}`",
            f"- Base: `{secondary['base_cagr']:.4f}` CAGR / `{secondary['base_mdd']:.4f}` MDD / Sharpe `{secondary['base_sharpe']:.4f}`",
            f"- Gap to attack main: CAGR `{secondary['cagr_gap_to_attack_main_pct']:.2f}%`, MDD `{secondary['mdd_gap_to_attack_main_pct']:.2f}%`",
            f"- Hypothesis: {secondary['hypothesis']}",
            f"- Mutation focus: `{' | '.join(secondary['mutation_focus'])}`",
            (
                "- Conversion context: "
                f"`{secondary['conversion_context']['family_verdict']}` | best variant `{secondary['conversion_context']['best_variant_label']}`"
            ),
            "",
        ]
    )


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_attack_next_experiment_brief_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_attack_next_experiment_brief_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_attack_next_experiment_brief_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_attack_next_experiment_brief_latest.md"
    json_payload = json.dumps(report, indent=2)
    md_payload = _render_markdown(report)
    json_path.write_text(json_payload, encoding="utf-8")
    md_path.write_text(md_payload, encoding="utf-8")
    latest_json.write_text(json_payload, encoding="utf-8")
    latest_md.write_text(md_payload, encoding="utf-8")
    print(
        json.dumps(
            {
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "latest_json_path": str(latest_json),
                "latest_md_path": str(latest_md),
                "report": report,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
