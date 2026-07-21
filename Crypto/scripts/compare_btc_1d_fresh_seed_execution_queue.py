from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_fresh_seed_priority_screen import build_report as build_fresh_seed_priority


ANALYSIS_DIR = Path("analysis_results")

FAMILY_RUNNERS = {
    "post_spike_consolidation_breakout": {
        "reopen_batch": "python scripts/run_btc_1d_post_spike_consolidation_breakout_high_cagr_batch.py --analysis-dir analysis_results --periods 2200",
        "candidate_validation": "python scripts/validate_btc_1d_post_spike_consolidation_breakout_candidate.py --periods 2200",
        "stage_review": "python scripts/compare_btc_1d_post_spike_consolidation_breakout_candidate_stage_review.py",
    },
    "impulse_flag_breakout": {
        "reopen_batch": "python scripts/run_btc_1d_impulse_flag_breakout_high_cagr_batch.py --analysis-dir analysis_results --periods 2200",
    },
    "narrow_range_expansion_drift": {
        "reopen_batch": "python scripts/run_btc_1d_narrow_range_expansion_drift_high_cagr_batch.py --analysis-dir analysis_results --periods 2200",
    },
}


def _runner_for_family(family: str) -> dict:
    if family in FAMILY_RUNNERS:
        return FAMILY_RUNNERS[family]
    script_path = ROOT / "scripts" / f"run_btc_1d_{family}_high_cagr_batch.py"
    if script_path.exists():
        return {
            "reopen_batch": f"python scripts/{script_path.name} --analysis-dir analysis_results --periods 2200",
        }
    raise KeyError(f"No fresh-seed runner mapped for family: {family}")


def _build_lane(
    *,
    row: dict,
    rank: int,
    status: str,
) -> list[dict]:
    runners = _runner_for_family(row["family"])
    steps = [
        {
            "order": 1,
            "family": row["family"],
            "seed_variant": row["variant_label"],
            "priority_rank": rank,
            "phase": "seed_reopen",
            "step": "reopen_batch",
            "runner": runners["reopen_batch"],
            "status": status,
            "reason": (
                "Run the family batch first to reopen the highest-priority broad seed under the current 2200-bar attack search frame."
                if rank == 1
                else "Keep the secondary family ready as the next alternate broad seed if the primary reopen stalls."
            ),
        }
    ]

    if "candidate_validation" in runners:
        steps.append(
            {
                "order": 2,
                "family": row["family"],
                "seed_variant": row["variant_label"],
                "priority_rank": rank,
                "phase": "candidate_validation",
                "step": "candidate_validation",
                "runner": runners["candidate_validation"],
                "status": "after_reopen_batch" if rank == 1 else "deferred",
                "reason": "Validate candidate-stage depth only after the reopened seed produces a winner worth carrying forward.",
            }
        )
    if "walk_forward_repair" in runners:
        steps.append(
            {
                "order": 3,
                "family": row["family"],
                "seed_variant": row["variant_label"],
                "priority_rank": rank,
                "phase": "walk_forward_repair",
                "step": "walk_forward_repair",
                "runner": runners["walk_forward_repair"],
                "status": "after_candidate_validation" if rank == 1 else "deferred",
                "reason": "Walk-forward repair stays downstream from candidate validation so the queue does not over-invest in an unproven reopen branch.",
            }
        )
    if "stage_review" in runners:
        steps.append(
            {
                "order": 4,
                "family": row["family"],
                "seed_variant": row["variant_label"],
                "priority_rank": rank,
                "phase": "stage_review",
                "step": "stage_review",
                "runner": runners["stage_review"],
                "status": "after_walk_forward_repair" if rank == 1 else "deferred",
                "reason": "Close the lane with a stage review so the reopened family can be compared back against the active attack board.",
            }
        )
    return steps


def build_report() -> dict:
    priority = build_fresh_seed_priority()
    primary, secondary = priority["priority_rows"]

    primary_lane = _build_lane(row=primary, rank=1, status="run_now")
    secondary_lane = _build_lane(row=secondary, rank=2, status="standby")
    execution_queue = primary_lane + secondary_lane

    next_step = execution_queue[0]
    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "queue_summary": {
            "queue_lane": priority["fresh_seed_scope"]["queue_lane"],
            "next_step_now": next_step["step"],
            "next_runner_now": next_step["runner"],
            "primary_seed_family": primary["family"],
            "primary_seed_variant": primary["variant_label"],
            "secondary_seed_family": secondary["family"],
            "secondary_seed_variant": secondary["variant_label"],
            "excluded_families": list(priority["fresh_seed_scope"]["excluded_families"]),
            "queue_mode": "fresh_seed_attack_restart",
        },
        "seed_snapshot": {
            "primary": {
                "family": primary["family"],
                "variant_label": primary["variant_label"],
                "attack_conversion_label": primary["attack_conversion_label"],
                "cagr": float(primary["cagr"]),
                "max_drawdown": float(primary["max_drawdown"]),
                "sharpe": float(primary["sharpe"]),
            },
            "secondary": {
                "family": secondary["family"],
                "variant_label": secondary["variant_label"],
                "attack_conversion_label": secondary["attack_conversion_label"],
                "cagr": float(secondary["cagr"]),
                "max_drawdown": float(secondary["max_drawdown"]),
                "sharpe": float(secondary["sharpe"]),
            },
        },
        "execution_queue": execution_queue,
        "queue_verdict": {
            "active_lane": primary["family"],
            "secondary_lane": secondary["family"],
            "ready_to_run_now": next_step["runner"],
            "next_step_now": next_step["step"],
            "advance_condition": "primary fresh-seed reopen must produce a candidate worth validating before the queue spends budget on the secondary family",
            "reason": (
                "The exhausted practical-adjacent board already forced a fresh-seed search, and post-spike consolidation breakout is the strongest surviving broad family with an identified alternate behind it."
            ),
        },
        "decision_summary": [
            f"Run `{primary['family']}` first because it is the primary fresh seed selected by the broader attack conversion board.",
            f"Keep `{secondary['family']}` on standby as the backup fresh seed, not as a parallel lane.",
            "Do not reopen exhausted practical-adjacent lanes while the fresh-seed restart queue is active.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    summary = report["queue_summary"]
    verdict = report["queue_verdict"]
    lines = [
        "# BTC 1d Fresh Seed Execution Queue",
        "",
        f"- Queue lane: `{summary['queue_lane']}`",
        f"- Queue mode: `{summary['queue_mode']}`",
        f"- Primary seed family: `{summary['primary_seed_family']}`",
        f"- Secondary seed family: `{summary['secondary_seed_family']}`",
        f"- Next step now: `{summary['next_step_now']}`",
        f"- Next runner now: `{summary['next_runner_now']}`",
        f"- Reason: {verdict['reason']}",
        "",
        "## Execution Queue",
    ]
    for row in report["execution_queue"]:
        lines.extend(
            [
                f"- `{row['family']}` | `{row['phase']}` | status=`{row['status']}`",
                f"  step: `{row['step']}`",
                f"  runner: `{row['runner']}`",
                f"  reason: {row['reason']}",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_fresh_seed_execution_queue_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_fresh_seed_execution_queue_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_fresh_seed_execution_queue_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_fresh_seed_execution_queue_md_latest.md"
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
                "report": report,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
