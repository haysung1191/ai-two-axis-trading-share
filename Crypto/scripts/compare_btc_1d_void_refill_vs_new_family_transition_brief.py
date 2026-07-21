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
from scripts.compare_btc_1d_new_family_search_queue import build_report as build_new_family_search_queue


ANALYSIS_DIR = Path("analysis_results")
PRACTICAL_ADJACENT_PATH = ANALYSIS_DIR / "btc_1d_defensive_practical_adjacent_screen_20260415T214130Z.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report() -> dict:
    post_pivot = build_post_pivot_next_family_brief()
    queue = build_new_family_search_queue()
    adjacent = _load_json(PRACTICAL_ADJACENT_PATH)

    seed_label = post_pivot["next_family_brief"]["selected_seed_label"]
    seed_row = next(row for row in adjacent["ranked_candidates"] if row["label"] == seed_label)
    void_lane = queue["next_family_lane"]
    plateau = queue["plateau_assessment"]
    validation = queue["current_validation_snapshot"]

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "transition_summary": {
            "plateau_lane_label": void_lane["label"],
            "deferred_seed_label": seed_label,
            "transition_mode": "hold_plateau_lane_open_distinct_seed_search",
        },
        "plateau_lane": {
            "label": void_lane["label"],
            "category": void_lane["category"],
            "base_cagr": float(void_lane["base_cagr"]),
            "base_mdd": float(void_lane["base_mdd"]),
            "base_sharpe": float(void_lane["base_sharpe"]),
            "oos_cagr": float(void_lane["oos_cagr"]),
            "oos_mdd": float(void_lane["oos_mdd"]),
            "oos_sharpe": float(void_lane["oos_sharpe"]),
            "base_drift": float(void_lane["sensitivity_max_drift"]),
            "latest_repair_variant": plateau["repair_best_variant"],
            "latest_repair_drift": float(plateau["repair_best_drift"]),
            "latest_validation_decision": validation["decision"],
            "latest_failed_gates": list(validation["failed_gates"]),
        },
        "deferred_seed": {
            "label": seed_row["label"],
            "category": seed_row["category"],
            "base_cagr": float(seed_row["base_cagr"]),
            "base_mdd": float(seed_row["base_mdd"]),
            "base_sharpe": float(seed_row["base_sharpe"]),
            "oos_cagr": float(seed_row["oos_cagr"]),
            "oos_mdd": float(seed_row["oos_mdd"]),
            "oos_sharpe": float(seed_row["oos_sharpe"]),
            "base_drift": float(seed_row["sensitivity_max_drift"]),
            "unstable_parameters": list(seed_row["unstable_parameters"]),
            "completed_trades": int(seed_row["completed_trades"]),
        },
        "transition_verdict": {
            "open_now": seed_row["label"],
            "hold_in_reserve": void_lane["label"],
            "open_mode": "distinct_next_family_mutation_search",
            "hold_mode": "plateaued_candidate_hold",
            "reason": (
                "The pullthrough seed still dominates the practical-adjacent board on base quality, while the void-refill lane has now re-confirmed the same repaired drift ceiling and should be treated as a plateaued hold rather than the next open-ended repair loop."
            ),
            "why_seed_wins_now": [
                "higher base CAGR than the plateaued void-refill lane",
                "lower base drawdown with better base Sharpe",
                "stronger OOS profile on the practical-adjacent board",
                "not yet consumed as an immediate repair loop because it is being held out for distinct family mutation search",
            ],
            "why_void_refill_is_held_not_reopened": [
                "latest repair and prior micro-refinement converge to the same drift zone near 0.2425",
                "latest validation still fails on overfitting gates",
                "current hypothesis set no longer shows material sensitivity contraction",
            ],
            "next_step_now": "derive_distinct_attack_family_from_pullthrough_seed",
            "reopen_void_refill_only_if": "a materially different structural hypothesis exists beyond the current stronger-confirmation and refill-buffer repair axis",
        },
        "decision_summary": [
            f"Open the next attack-family search from `{seed_row['label']}` because it remains the highest-quality practical-adjacent seed and has not yet been consumed as the active mutation lane.",
            f"Keep `{void_lane['label']}` as a plateaued candidate hold, not as the next repair loop, because its best repaired drift stays pinned near `{plateau['repair_best_drift']:.4f}`.",
            "Only reopen void-refill if a new structural hypothesis appears; otherwise the next cycle should spend its search budget on a distinct seed-derived family.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    plateau_lane = report["plateau_lane"]
    seed = report["deferred_seed"]
    verdict = report["transition_verdict"]
    lines = [
        "# BTC 1d Void Refill vs New Family Transition Brief",
        "",
        f"- Open now: `{verdict['open_now']}`",
        f"- Hold in reserve: `{verdict['hold_in_reserve']}`",
        f"- Transition mode: `{report['transition_summary']['transition_mode']}`",
        f"- Reason: {verdict['reason']}",
        "",
        "## Plateau Lane",
        f"- Label: `{plateau_lane['label']}`",
        f"- Base: `{plateau_lane['base_cagr']:.4f}` CAGR / `{plateau_lane['base_mdd']:.4f}` MDD / Sharpe `{plateau_lane['base_sharpe']:.4f}`",
        f"- OOS: `{plateau_lane['oos_cagr']:.4f}` CAGR / `{plateau_lane['oos_mdd']:.4f}` MDD / Sharpe `{plateau_lane['oos_sharpe']:.4f}`",
        f"- Base drift: `{plateau_lane['base_drift']:.4f}`",
        f"- Latest repair: `{plateau_lane['latest_repair_variant']}` | drift `{plateau_lane['latest_repair_drift']:.4f}`",
        f"- Latest validation: `{plateau_lane['latest_validation_decision']}` | failed `{', '.join(plateau_lane['latest_failed_gates'])}`",
        "",
        "## Deferred Seed",
        f"- Label: `{seed['label']}`",
        f"- Base: `{seed['base_cagr']:.4f}` CAGR / `{seed['base_mdd']:.4f}` MDD / Sharpe `{seed['base_sharpe']:.4f}`",
        f"- OOS: `{seed['oos_cagr']:.4f}` CAGR / `{seed['oos_mdd']:.4f}` MDD / Sharpe `{seed['oos_sharpe']:.4f}`",
        f"- Base drift: `{seed['base_drift']:.4f}`",
        f"- Completed trades: `{seed['completed_trades']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_void_refill_vs_new_family_transition_brief_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_void_refill_vs_new_family_transition_brief_{stamp}.md"
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
