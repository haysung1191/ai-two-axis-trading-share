from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_fresh_seed_execution_queue import (
    build_report as build_fresh_seed_execution_queue,
)
from scripts.compare_btc_1d_new_family_search_queue import (
    build_report as build_new_family_search_queue,
)


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_latest_or_build(
    *,
    latest_name: str,
    build_fallback,
) -> tuple[dict, str]:
    latest_path = ANALYSIS_DIR / latest_name
    if latest_path.exists():
        return _load_json(latest_path), str(latest_path)
    return build_fallback(), "in_memory_build"


def build_report() -> dict:
    new_family_queue, new_family_queue_artifact_path = _load_latest_or_build(
        latest_name="btc_1d_new_family_search_queue_latest.json",
        build_fallback=build_new_family_search_queue,
    )
    fresh_seed_queue, fresh_seed_queue_artifact_path = _load_latest_or_build(
        latest_name="btc_1d_fresh_seed_execution_queue_latest.json",
        build_fallback=build_fresh_seed_execution_queue,
    )

    plateau = new_family_queue["plateau_assessment"]
    verdict = new_family_queue["queue_verdict"]
    next_family_lane = new_family_queue["next_family_lane"]
    fresh_summary = fresh_seed_queue["queue_summary"]
    fresh_verdict = fresh_seed_queue["queue_verdict"]
    primary_seed = fresh_seed_queue["seed_snapshot"]["primary"]

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "post_void_queue_summary": {
            "new_family_queue_artifact_path": new_family_queue_artifact_path,
            "fresh_seed_queue_artifact_path": fresh_seed_queue_artifact_path,
            "post_pivot_seed": new_family_queue["search_queue_summary"]["post_pivot_seed"],
            "void_lane": next_family_lane["label"],
            "void_lane_verdict": verdict["next_step_now"],
            "void_lane_plateaued": plateau["plateaued"],
            "exhausted_families": list(fresh_summary["excluded_families"]),
            "queue_mode": "plateau_compare_to_fresh_seed_restart",
        },
        "selected_broad_search_seed": {
            "family": primary_seed["family"],
            "variant_label": primary_seed["variant_label"],
            "attack_conversion_label": primary_seed["attack_conversion_label"],
            "base_cagr": float(primary_seed["cagr"]),
            "base_mdd": float(primary_seed["max_drawdown"]),
            "base_sharpe": float(primary_seed["sharpe"]),
            "artifact_path": next(
                row["runner"]
                for row in fresh_seed_queue["execution_queue"]
                if row["family"] == primary_seed["family"] and row["phase"] == "seed_reopen"
            ),
        },
        "comparison_context": {
            "plateaued_lane_label": next_family_lane["label"],
            "plateaued_lane_cagr": float(next_family_lane["base_cagr"]),
            "plateaued_lane_mdd": float(next_family_lane["base_mdd"]),
            "plateaued_lane_sharpe": float(next_family_lane["base_sharpe"]),
            "plateaued_lane_sensitivity_max_drift": float(next_family_lane["sensitivity_max_drift"]),
            "plateau_reason": plateau["reason"],
            "fresh_seed_family": primary_seed["family"],
            "fresh_seed_variant": primary_seed["variant_label"],
            "fresh_seed_cagr": float(primary_seed["cagr"]),
            "fresh_seed_mdd": float(primary_seed["max_drawdown"]),
            "fresh_seed_sharpe": float(primary_seed["sharpe"]),
            "fresh_seed_reason": fresh_verdict["reason"],
        },
        "broad_search_queue": {
            "selection_logic": [
                "only open broad-search restart after the practical-adjacent lane is explicitly plateaued",
                "reuse the current fresh-seed execution queue instead of inventing a separate stale broad-search branch",
                "keep the restart lane sequential: primary fresh seed first, backup seed only if the primary stalls",
            ],
            "next_step_now": fresh_summary["next_step_now"],
            "next_runner_now": fresh_summary["next_runner_now"],
            "working_hypothesis": "when the practical-adjacent lane is plateaued, restart the attack search from the strongest surviving broad family instead of reopening the same local repair neighborhood",
            "success_gate": {
                "must_come_from_plateaued_adjacent_lane": True,
                "must_reach_candidate_stage_evidence": True,
                "must_preserve_drawdown_control_vs_plateaued_lane": True,
                "must_outperform_local_repair_loop_on_upside_optionality": True,
            },
        },
        "queue_verdict": {
            "selected_family": primary_seed["family"],
            "selected_reason": (
                "The current practical-adjacent lane is explicitly plateaued at `compare_with_new_family_search`, so the next actionable branch should be the primary fresh-seed restart lane rather than another local void-refill repair."
            ),
            "next_step_now": fresh_summary["next_step_now"],
            "next_runner_now": fresh_summary["next_runner_now"],
            "advance_condition": fresh_verdict["advance_condition"],
        },
        "decision_summary": [
            f"Do not keep repairing `{next_family_lane['label']}` because the current queue already settled on `{verdict['next_step_now']}` with a plateaued adjacent lane.",
            f"Route the next broad search through `{primary_seed['family']}` because it is already the primary fresh seed in the current restart queue.",
            "Use the fresh-seed restart queue as the execution target for the compare step, instead of maintaining a separate stale broad-search branch.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    seed = report["selected_broad_search_seed"]
    summary = report["post_void_queue_summary"]
    context = report["comparison_context"]
    queue = report["broad_search_queue"]
    verdict = report["queue_verdict"]
    lines = [
        "# BTC 1d Post-Void New Family Queue",
        "",
        f"- Queue mode: `{summary['queue_mode']}`",
        f"- Void lane: `{summary['void_lane']}`",
        f"- Void lane verdict: `{summary['void_lane_verdict']}`",
        f"- Void lane plateaued: `{summary['void_lane_plateaued']}`",
        f"- Selected family: `{seed['family']}`",
        f"- Variant: `{seed['variant_label']}`",
        f"- Base: `{seed['base_cagr']:.4f}` CAGR / `{seed['base_mdd']:.4f}` MDD / Sharpe `{seed['base_sharpe']:.4f}`",
        f"- Next step now: `{queue['next_step_now']}`",
        f"- Next runner now: `{queue['next_runner_now']}`",
        f"- Selected reason: {verdict['selected_reason']}",
        "",
        "## Comparison Context",
        f"- Plateaued lane base: `{context['plateaued_lane_cagr']:.4f}` CAGR / `{context['plateaued_lane_mdd']:.4f}` MDD / Sharpe `{context['plateaued_lane_sharpe']:.4f}`",
        f"- Plateaued lane drift: `{context['plateaued_lane_sensitivity_max_drift']:.4f}`",
        f"- Plateau reason: {context['plateau_reason']}",
        f"- Fresh seed reason: {context['fresh_seed_reason']}",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_void_new_family_queue_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_void_new_family_queue_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_post_void_new_family_queue_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_post_void_new_family_queue_latest.md"
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
