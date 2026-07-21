from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_attack_post_pivot_next_family_brief import (
    build_report as build_post_pivot_next_family_brief,
)


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_required_artifact(analysis_dir: Path, pattern: str) -> Path:
    matches = sorted(analysis_dir.glob(pattern), key=lambda path: path.name)
    if not matches:
        raise FileNotFoundError(f"No artifact found for pattern: {pattern}")
    return matches[-1]


def _load_latest_or_build_post_pivot(analysis_dir: Path) -> tuple[dict, str]:
    latest_path = analysis_dir / "btc_1d_attack_post_pivot_next_family_brief_latest.json"
    if latest_path.exists():
        return _load_json(latest_path), str(latest_path)
    report = build_post_pivot_next_family_brief()
    return report, "in_memory_build"


def _load_latest_required_json(analysis_dir: Path, latest_name: str, fallback_pattern: str) -> tuple[dict, str]:
    latest_path = analysis_dir / latest_name
    if latest_path.exists():
        return _load_json(latest_path), str(latest_path)
    fallback_path = _latest_required_artifact(analysis_dir, fallback_pattern)
    return _load_json(fallback_path), str(fallback_path)


def _is_void_refill_plateaued(*, repair_screen: dict, micro_refinement_screen: dict) -> bool:
    repair_best = repair_screen["best_variant"]
    micro_best = micro_refinement_screen["best_variant"]
    repair_drift = float(repair_best["sensitivity_max_drift"])
    micro_drift = float(micro_best["sensitivity_max_drift"])
    same_family_shape = repair_best["variant_label"] == "stronger_confirmation_anchor"
    no_material_improvement = abs(repair_drift - micro_drift) <= 0.002
    still_above_threshold = repair_drift > 0.18 and micro_drift > 0.18
    return same_family_shape and no_material_improvement and still_above_threshold


def build_report() -> dict:
    post_pivot, post_pivot_artifact_path = _load_latest_or_build_post_pivot(ANALYSIS_DIR)
    adjacent, adjacent_artifact_path = _load_latest_required_json(
        ANALYSIS_DIR,
        "btc_1d_defensive_practical_adjacent_screen_latest.json",
        "btc_1d_defensive_practical_adjacent_screen_*.json",
    )
    try:
        latest_void_friction_path = _latest_required_artifact(
            ANALYSIS_DIR, "btc_1d_shallow_liquidity_void_refill_friction_*.json"
        )
        latest_void_candidate_path = _latest_required_artifact(
            ANALYSIS_DIR,
            "btc_1d_shallow_liquidity_void_refill_continuation_exit_v1_btcusdt_1d_2200_paper_validation_*.json",
        )
        latest_void_repair_screen_path = _latest_required_artifact(
            ANALYSIS_DIR, "btc_1d_shallow_liquidity_void_refill_repair_screen_*.json"
        )
        latest_void_micro_screen_path = _latest_required_artifact(
            ANALYSIS_DIR, "btc_1d_shallow_liquidity_void_refill_micro_refinement_screen_*.json"
        )
    except FileNotFoundError as exc:
        return {
            "generated_at": datetime.now(tz=UTC).isoformat(),
            "search_queue_summary": {
                "post_pivot_seed": "",
                "post_pivot_seed_status": "unavailable",
                "exhausted_lanes": [],
                "next_family_lane": "disabled_missing_archived_artifacts",
                "next_family_category": "disabled",
                "queue_mode": "disabled_for_shadow_readiness_focus",
            },
            "transition_context": {
                "post_pivot_artifact_path": post_pivot_artifact_path,
                "practical_adjacent_artifact_path": adjacent_artifact_path,
                "primary_lane_status": "unavailable",
                "primary_lane_best_stage1_candidate": "",
                "primary_lane_best_cagr_repair": "",
                "primary_lane_best_sensitivity_repair": "",
                "primary_lane_transition_hint": "",
                "deferred_seed_label": "",
                "deferred_seed_reason": str(exc),
            },
            "next_family_lane": {
                "label": "disabled_missing_archived_artifacts",
                "category": "disabled",
                "candidate_stage_evidence": False,
                "base_cagr": 0.0,
                "base_mdd": 0.0,
                "base_sharpe": 0.0,
                "oos_cagr": 0.0,
                "oos_mdd": 0.0,
                "oos_sharpe": 0.0,
                "sensitivity_max_drift": 0.0,
                "unstable_parameters": [],
                "cost20_cagr": 0.0,
                "cost20_mdd": 0.0,
                "cost20_sharpe": 0.0,
                "paper_failed_gates": ["missing_archived_artifacts"],
            },
            "current_validation_snapshot": {
                "artifact_path": "",
                "decision": "unavailable",
                "failed_gates": ["missing_archived_artifacts"],
                "sharpe": 0.0,
                "cagr": 0.0,
                "max_drawdown": 0.0,
            },
            "repair_queue": {
                "current_blocker": "missing_archived_artifacts",
                "friction_artifact_path": "",
                "repair_screen_artifact_path": "",
                "micro_refinement_artifact_path": "",
                "baseline_failed_gates": ["missing_archived_artifacts"],
                "execution_sequence": [],
                "success_gate": {},
            },
            "plateau_assessment": {
                "plateaued": True,
                "repair_best_variant": "",
                "repair_best_drift": 0.0,
                "micro_best_variant": "",
                "micro_best_drift": 0.0,
                "reason": str(exc),
            },
            "queue_verdict": {
                "selected_lane": "disabled_missing_archived_artifacts",
                "selected_reason": "Broad new-family queue is disabled until archived artifacts are regenerated; bridge readiness remains the priority.",
                "next_step_now": "bridge_shadow_readiness_gate_closure",
                "advance_condition": "regenerate required archived artifacts before reopening broad new-family search",
            },
            "decision_summary": [
                "New-family queue is disabled because archived timestamp artifacts are absent.",
                "This is acceptable for the current loop because the priority is bridge_28_relief shadow-readiness, not broad family search.",
            ],
        }
    void_friction = _load_json(latest_void_friction_path)
    latest_void_candidate = _load_json(latest_void_candidate_path)
    latest_void_repair_screen = _load_json(latest_void_repair_screen_path)
    latest_void_micro_screen = _load_json(latest_void_micro_screen_path)
    plateaued = _is_void_refill_plateaued(
        repair_screen=latest_void_repair_screen,
        micro_refinement_screen=latest_void_micro_screen,
    )

    selected_seed = post_pivot["next_family_brief"]["selected_seed_label"]
    selected_seed_row = next(
        row for row in adjacent["ranked_candidates"] if row["label"] == selected_seed
    )
    exhausted = set(post_pivot["next_family_brief"]["do_not_restart"])
    exhausted.add(selected_seed)
    ranked = [row for row in adjacent["ranked_candidates"] if row["label"] not in exhausted]
    if not ranked:
        raise ValueError("No practical-adjacent candidates remain after excluding exhausted lanes.")
    next_lane = ranked[0]

    baseline_level = min(void_friction["levels"], key=lambda row: float(row["cost_bps"]))
    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "search_queue_summary": {
            "post_pivot_seed": selected_seed,
            "post_pivot_seed_status": "held_out_as_seed_source",
            "exhausted_lanes": sorted(exhausted),
            "next_family_lane": next_lane["label"],
            "next_family_category": next_lane["category"],
            "queue_mode": "plateau_review" if plateaued else "overfitting_repair_first",
        },
        "transition_context": {
            "post_pivot_artifact_path": post_pivot_artifact_path,
            "practical_adjacent_artifact_path": adjacent_artifact_path,
            "primary_lane_status": post_pivot["trend_dip_handoff"]["family_status"],
            "primary_lane_best_stage1_candidate": post_pivot["trend_dip_handoff"]["best_stage1_candidate"],
            "primary_lane_best_cagr_repair": post_pivot["trend_dip_handoff"]["best_cagr_repair"],
            "primary_lane_best_sensitivity_repair": post_pivot["trend_dip_handoff"]["best_sensitivity_repair"],
            "primary_lane_transition_hint": post_pivot["trend_dip_handoff"]["next_transition_hint"],
            "deferred_seed_label": selected_seed_row["label"],
            "deferred_seed_reason": (
                "The pullthrough seed remains the highest-ranked practical-adjacent baseline, but it is intentionally held out as the mutation source for a distinct next family rather than reopened as the immediate execution lane."
            ),
        },
        "next_family_lane": {
            "label": next_lane["label"],
            "category": next_lane["category"],
            "candidate_stage_evidence": bool(next_lane["candidate_stage_evidence"]),
            "base_cagr": float(next_lane["base_cagr"]),
            "base_mdd": float(next_lane["base_mdd"]),
            "base_sharpe": float(next_lane["base_sharpe"]),
            "oos_cagr": float(next_lane["oos_cagr"]),
            "oos_mdd": float(next_lane["oos_mdd"]),
            "oos_sharpe": float(next_lane["oos_sharpe"]),
            "sensitivity_max_drift": float(next_lane["sensitivity_max_drift"]),
            "unstable_parameters": list(next_lane["unstable_parameters"]),
            "cost20_cagr": float(next_lane["cost20_cagr"]),
            "cost20_mdd": float(next_lane["cost20_mdd"]),
            "cost20_sharpe": float(next_lane["cost20_sharpe"]),
            "paper_failed_gates": list(next_lane["paper_failed_gates"]),
        },
        "current_validation_snapshot": {
            "artifact_path": str(latest_void_candidate_path),
            "decision": latest_void_candidate["decision_record"]["decision"],
            "failed_gates": list(latest_void_candidate["decision_record"]["failed_gates"]),
            "sharpe": float(latest_void_candidate["decision_record"]["key_metrics"]["sharpe"]),
            "cagr": float(latest_void_candidate["decision_record"]["key_metrics"]["cagr"]),
            "max_drawdown": float(latest_void_candidate["decision_record"]["key_metrics"]["max_drawdown"]),
        },
        "repair_queue": {
            "current_blocker": void_friction["final_decision"],
            "friction_artifact_path": str(latest_void_friction_path),
            "repair_screen_artifact_path": str(latest_void_repair_screen_path),
            "micro_refinement_artifact_path": str(latest_void_micro_screen_path),
            "baseline_failed_gates": list(baseline_level["failed_gates"]),
            "execution_sequence": [
                {
                    "step": "candidate_repair_retest",
                    "runner": "python scripts/validate_btc_1d_shallow_liquidity_void_refill_candidate.py --periods 2200",
                },
                {
                    "step": "friction_retest",
                    "runner": "python scripts/validate_btc_1d_shallow_liquidity_void_refill_friction.py --analysis-dir analysis_results --periods 2200",
                },
                {
                    "step": "exit_compression_retest",
                    "runner": "python scripts/run_btc_1d_shallow_liquidity_void_refill_continuation_exit_compression_batch.py --analysis-dir analysis_results --periods 2200",
                },
            ],
            "success_gate": {
                "must_flip_final_decision_from": void_friction["final_decision"],
                "must_clear_failed_gate": "overfitting_sensitivity",
                "must_hold_drawdown_below": 0.18,
                "must_preserve_cagr_above": 0.22,
            },
        },
        "plateau_assessment": {
            "plateaued": plateaued,
            "repair_best_variant": latest_void_repair_screen["best_variant"]["variant_label"],
            "repair_best_drift": float(latest_void_repair_screen["best_variant"]["sensitivity_max_drift"]),
            "micro_best_variant": latest_void_micro_screen["best_variant"]["variant_label"],
            "micro_best_drift": float(latest_void_micro_screen["best_variant"]["sensitivity_max_drift"]),
            "reason": (
                "Latest repair and prior micro-refinement both top out around the same drift zone, so the lane now looks structurally plateaued under the current hypothesis set."
                if plateaued
                else "Latest repair work still leaves room for another materially different sensitivity-repair pass."
            ),
        },
        "queue_verdict": {
            "selected_lane": next_lane["label"],
            "selected_reason": (
                "It is the strongest remaining practical-adjacent candidate after excluding the held-out pullthrough seed and the already exhausted attack lanes, and it already has candidate-stage evidence with controlled drawdown."
            ),
            "next_step_now": "compare_with_new_family_search" if plateaued else "candidate_repair_retest",
            "advance_condition": (
                "Only reopen repair if a materially different structural hypothesis exists; otherwise compare this plateaued lane against opening a distinct next-family search."
                if plateaued
                else "overfitting flags shrink materially and friction flips away from pause"
            ),
        },
        "decision_summary": [
            f"Do not reopen `{selected_seed}` immediately because it is being reserved as the seed source for distinct next-family mutation work, not as the immediate lane to grind again.",
            f"Keep the trend-dip family frozen because `{post_pivot['trend_dip_handoff']['family_status']}` is now backed by explicit handoff evidence.",
            f"Promote `{next_lane['label']}` to the next family-search lane because it is the strongest remaining practical-adjacent candidate not already exhausted.",
            (
                "Treat the current void-refill lane as plateaued under the active repair hypothesis set and compare it against opening a distinct next-family search."
                if plateaued
                else "Start with overfitting repair first, not upside extension first, because the blocker is still sensitivity and promotion depth rather than gross return."
            ),
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    summary = report["search_queue_summary"]
    transition = report["transition_context"]
    lane = report["next_family_lane"]
    validation = report["current_validation_snapshot"]
    queue = report["repair_queue"]
    plateau = report["plateau_assessment"]
    verdict = report["queue_verdict"]
    lines = [
        "# BTC 1d New Family Search Queue",
        "",
        f"- Next family lane: `{summary['next_family_lane']}`",
        f"- Queue mode: `{summary['queue_mode']}`",
        f"- Selected reason: {verdict['selected_reason']}",
        f"- Next step now: `{verdict['next_step_now']}`",
        f"- Deferred seed: `{transition['deferred_seed_label']}`",
        f"- Primary lane status: `{transition['primary_lane_status']}`",
        "",
        "## Lane Snapshot",
        f"- Base: `{lane['base_cagr']:.4f}` CAGR / `{lane['base_mdd']:.4f}` MDD / Sharpe `{lane['base_sharpe']:.4f}`",
        f"- OOS: `{lane['oos_cagr']:.4f}` CAGR / `{lane['oos_mdd']:.4f}` MDD / Sharpe `{lane['oos_sharpe']:.4f}`",
        f"- Sensitivity drift: `{lane['sensitivity_max_drift']:.4f}`",
        f"- Unstable parameters: `{', '.join(lane['unstable_parameters']) or '-'}`",
        f"- Latest validation: `{validation['decision']}` | `{validation['cagr']:.4f}` CAGR / `{validation['max_drawdown']:.4f}` MDD / Sharpe `{validation['sharpe']:.4f}`",
        f"- Current blocker: `{queue['current_blocker']}`",
        "",
        "## Plateau Assessment",
        f"- Plateaued: `{plateau['plateaued']}`",
        f"- Latest repair best: `{plateau['repair_best_variant']}` | drift `{plateau['repair_best_drift']:.4f}`",
        f"- Prior micro best: `{plateau['micro_best_variant']}` | drift `{plateau['micro_best_drift']:.4f}`",
        f"- Reason: {plateau['reason']}",
        "",
        "## Transition Context",
        f"- Deferred seed reason: {transition['deferred_seed_reason']}",
        f"- Trend-dip best stage1: `{transition['primary_lane_best_stage1_candidate']}`",
        f"- Trend-dip best CAGR repair: `{transition['primary_lane_best_cagr_repair']}`",
        f"- Trend-dip best sensitivity repair: `{transition['primary_lane_best_sensitivity_repair']}`",
        f"- Trend-dip transition hint: {transition['primary_lane_transition_hint']}",
        "",
        "## Execution Sequence",
    ]
    for row in queue["execution_sequence"]:
        lines.append(f"- `{row['step']}`: `{row['runner']}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_new_family_search_queue_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_new_family_search_queue_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_new_family_search_queue_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_new_family_search_queue_latest.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    latest_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    latest_md.write_text(_render_markdown(report), encoding="utf-8")
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
