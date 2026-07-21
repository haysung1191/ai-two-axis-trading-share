from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_attack_experiment_spec import build_report as build_experiment_spec
from scripts.compare_btc_1d_attack_next_experiment_brief import (
    build_report as build_attack_next_experiment_brief,
)
from scripts.compare_btc_1d_spike_reversal_secondary_promotion_screen import (
    build_report as build_secondary_promotion_screen,
)
from scripts.compare_btc_1d_trend_dip_candidate_validation_review import (
    build_report as build_trend_dip_candidate_validation_review,
)
from scripts.compare_btc_1d_trend_dip_attack_reopen_screen import (
    build_report as build_trend_dip_reopen_screen,
)


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _latest_primary_queue_step() -> dict | None:
    path = ANALYSIS_DIR / "btc_1d_attack_primary_queue_step_latest.json"
    if not path.exists():
        return None
    return _load_json(path)


def _fallback_trend_validation(reason: str) -> dict:
    return {
        "validation_review_verdict": {
            "all_reviewed_candidates_failed": True,
            "next_step_now": "hold_primary_anchor_missing_archived_artifacts",
            "reason": reason,
        }
    }


def _fallback_secondary(reason: str) -> dict:
    return {
        "secondary_branch_candidate": {"label": "secondary_unavailable"},
        "secondary_branch_verdict": {
            "promotion_status": "blocked_missing_archived_artifacts",
            "promotion_ready": False,
            "next_required_gate": "regenerate_archived_artifacts",
            "reason": reason,
        },
    }


def build_report() -> dict:
    experiment_spec = build_experiment_spec()
    next_brief = build_attack_next_experiment_brief()
    trend_dip = build_trend_dip_reopen_screen()
    try:
        trend_dip_validation = build_trend_dip_candidate_validation_review()
    except FileNotFoundError as exc:
        trend_dip_validation = _fallback_trend_validation(str(exc))
    try:
        secondary = build_secondary_promotion_screen()
    except FileNotFoundError as exc:
        secondary = _fallback_secondary(str(exc))
    latest_primary_step = _latest_primary_queue_step()

    primary_spec = experiment_spec["experiment_spec"]
    mutation_plan = experiment_spec["mutation_plan"]
    success_gate = experiment_spec["success_gate"]
    reopen_verdict = trend_dip["reopen_verdict"]
    secondary_verdict = secondary["secondary_branch_verdict"]
    backup_repair_context = next_brief["attack_backup_repair_context"]
    trend_validation_verdict = trend_dip_validation["validation_review_verdict"]
    symmetry_completed = bool(latest_primary_step) and str(latest_primary_step.get("step")) == "exit_symmetry_batch"
    symmetry_holds_anchor = symmetry_completed and str(
        ((latest_primary_step or {}).get("step_verdict", {}) or {}).get("next_step", "")
    ) == "hold_primary_anchor"

    queue = [
        {
            "order": 1,
            "phase": "primary_reopen",
            "step": "exit_compression_batch",
            "runner": mutation_plan["primary_mutation_axes"][0]["runner"],
            "status": "completed_fail_validation" if trend_validation_verdict["all_reviewed_candidates_failed"] else "run_now",
            "reason": (
                "Exit compression already produced stronger raw candidates, but the reviewed survivors failed candidate validation."
                if trend_validation_verdict["all_reviewed_candidates_failed"]
                else "Primary bottleneck is now outside the closed bridge-backup local repair neighborhood, "
                "so trend-dip exit compression is the first planned mutation axis."
            ),
        },
        {
            "order": 2,
            "phase": "primary_reopen",
            "step": "exit_symmetry_batch",
            "runner": mutation_plan["primary_mutation_axes"][1]["runner"],
            "status": (
                "completed_hold_anchor"
                if symmetry_holds_anchor
                else "run_now"
                if trend_validation_verdict["all_reviewed_candidates_failed"]
                else "conditional_next"
            ),
            "reason": (
                "Exit symmetry completed and also failed to beat the current anchor, so the primary lane should now hold the anchor."
                if symmetry_holds_anchor
                else "Exit symmetry is now the active next step because the reviewed compression survivors failed candidate validation."
                if trend_validation_verdict["all_reviewed_candidates_failed"]
                else f"Current reopen anchor remains `{reopen_verdict['preferred_variant_label']}` from "
                f"`{reopen_verdict['preferred_mutation_family']}`, so symmetry stays the second pass if compression alone is insufficient."
            ),
        },
        {
            "order": 3,
            "phase": "primary_validation",
            "step": mutation_plan["validation_sequence"][0]["step"],
            "runner": mutation_plan["validation_sequence"][0]["runner"],
            "status": "after_primary_mutation_win",
            "reason": "Only validate candidate-stage depth after a mutation beats the current drawdown anchor.",
        },
        {
            "order": 4,
            "phase": "primary_validation",
            "step": mutation_plan["validation_sequence"][1]["step"],
            "runner": mutation_plan["validation_sequence"][1]["runner"],
            "status": "after_candidate_validation",
            "reason": "Walk-forward remains downstream from candidate validation in the primary retest path.",
        },
        {
            "order": 5,
            "phase": "primary_validation",
            "step": mutation_plan["validation_sequence"][2]["step"],
            "runner": mutation_plan["validation_sequence"][2]["runner"],
            "status": "after_walk_forward",
            "reason": "Friction is the last gate before any attack reopen promotion.",
        },
        {
            "order": 6,
            "phase": "secondary_branch",
            "step": "spike_reversal_reopen",
            "runner": "deferred",
            "status": "blocked",
            "reason": (
                f"Secondary branch stays `{secondary_verdict['promotion_status']}` until "
                f"`{secondary_verdict['next_required_gate']}` is cleared."
            ),
        },
    ]

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "queue_summary": {
            "track": primary_spec["track"],
            "primary_label": primary_spec["primary_label"],
            "secondary_label": primary_spec["secondary_label"],
            "next_step_now": (
                "hold_primary_anchor"
                if symmetry_holds_anchor
                else queue[1]["step"]
                if trend_validation_verdict["all_reviewed_candidates_failed"]
                else queue[0]["step"]
            ),
            "next_runner_now": (
                "hold_current_anchor_no_further_primary_mutation"
                if symmetry_holds_anchor
                else queue[1]["runner"]
                if trend_validation_verdict["all_reviewed_candidates_failed"]
                else queue[0]["runner"]
            ),
            "attack_backup_label": backup_repair_context["attack_backup_label"],
            "attack_backup_negative_window_watch": backup_repair_context["negative_window_watch"],
            "attack_backup_negative_walk_forward_windows": list(backup_repair_context["negative_walk_forward_windows"]),
            "attack_backup_local_repair_next_step": backup_repair_context["bridge_backup_local_repair_next_step"],
            "trend_dip_validation_next_step": trend_validation_verdict["next_step_now"],
            "attack_seed_available": experiment_spec["attack_rule_seed"]["available"],
            "attack_seed_params": experiment_spec["attack_rule_seed"]["recommended_attack_rule_seed"],
            "secondary_branch_status": secondary_verdict["promotion_status"],
            "secondary_branch_blocked": not secondary_verdict["promotion_ready"],
            "primary_success_gate": {
                "must_improve": success_gate["must_improve"],
                "target_role": success_gate["primary_target_role"],
            },
        },
        "execution_queue": queue,
        "queue_verdict": {
            "active_lane": "primary_trend_dip_reopen",
            "secondary_lane": "deferred_spike_reversal_upside_branch",
            "ready_to_run_now": (
                "hold_current_anchor_no_further_primary_mutation"
                if symmetry_holds_anchor
                else queue[1]["runner"]
                if trend_validation_verdict["all_reviewed_candidates_failed"]
                else queue[0]["runner"]
            ),
            "block_secondary_until": secondary_verdict["next_required_gate"],
            "reason": (
                "The trend-dip retest stayed primary through exit symmetry, but symmetry also failed to beat the anchor, so the correct state is to hold the current anchor and stop primary mutation expansion here."
                if symmetry_holds_anchor
                else "The trend-dip retest stays primary, but the reviewed exit-compression survivors failed candidate validation, so the queue now advances to exit symmetry."
                if trend_validation_verdict["all_reviewed_candidates_failed"]
                else "The trend-dip retest has the highest validation depth and now sits immediately after the closed bridge-backup local repair lane, "
                "while spike reversal remains blocked by friction and candidate-stage promotion."
            ),
        },
        "decision_summary": [
            f"`{backup_repair_context['attack_backup_label']}` still carries negative windows `{backup_repair_context['negative_walk_forward_windows']}`, and its local repair next step is `{backup_repair_context['bridge_backup_local_repair_next_step']}`.",
            (
                "Exit symmetry also failed to improve the anchor, so the primary trend-dip lane should hold `tighter_stop_mid_hold` and stop mutation expansion here."
                if symmetry_holds_anchor
                else
                "Reviewed exit-compression survivors all failed candidate validation, so the primary queue should advance to exit symmetry."
                if trend_validation_verdict["all_reviewed_candidates_failed"]
                else f"Run `{queue[0]['step']}` first for `{primary_spec['primary_label']}`."
            ),
            (
                "Keep the queue aligned to the current attack seed "
                f"`{experiment_spec['attack_rule_seed']['recommended_attack_rule_seed']}`."
            ),
            f"Keep `{primary_spec['secondary_label']}` deferred until `{secondary_verdict['next_required_gate']}`.",
            "Do not branch execution across primary and secondary lanes at the same time; finish the primary retest queue first.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    summary = report["queue_summary"]
    verdict = report["queue_verdict"]
    lines = [
        "# BTC 1d Attack Execution Queue",
        "",
        f"- Track: `{summary['track']}`",
        f"- Primary label: `{summary['primary_label']}`",
        f"- Secondary label: `{summary['secondary_label']}`",
        f"- Next step now: `{summary['next_step_now']}`",
        f"- Next runner now: `{summary['next_runner_now']}`",
        f"- Attack backup: `{summary['attack_backup_label']}`",
        f"- Attack backup negative-window watch: `{summary['attack_backup_negative_window_watch']}`",
        f"- Attack backup negative windows: `{summary['attack_backup_negative_walk_forward_windows']}`",
        f"- Attack backup local repair next step: `{summary['attack_backup_local_repair_next_step']}`",
        f"- Trend dip validation next step: `{summary['trend_dip_validation_next_step']}`",
        f"- Attack seed available: `{summary['attack_seed_available']}`",
        f"- Attack seed params: `{summary['attack_seed_params']}`",
        f"- Secondary branch status: `{summary['secondary_branch_status']}`",
        f"- Secondary branch blocked: `{summary['secondary_branch_blocked']}`",
        f"- Queue verdict: `{verdict['active_lane']}`",
        f"- Reason: {verdict['reason']}",
        "",
        "## Execution Queue",
    ]
    for row in report["execution_queue"]:
        lines.extend(
            [
                f"- `{row['order']}. {row['step']}` | status=`{row['status']}`",
                f"  runner: `{row['runner']}`",
                f"  reason: {row['reason']}",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_attack_execution_queue_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_attack_execution_queue_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_attack_execution_queue_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_attack_execution_queue_latest.md"
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
