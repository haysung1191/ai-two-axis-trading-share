from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_attack_pivot_screen import build_report as build_attack_pivot_screen
from scripts.compare_btc_1d_spike_reversal_secondary_promotion_screen import (
    build_report as build_secondary_promotion_screen,
)


ANALYSIS_DIR = Path("analysis_results")
FRICTION_PATH = (
    ANALYSIS_DIR / "btc_1d_volatility_spike_reversal_continuation_tightstop_friction_20260415T181604Z.json"
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report() -> dict:
    pivot = build_attack_pivot_screen()
    secondary = build_secondary_promotion_screen()
    friction = _load_json(FRICTION_PATH)

    baseline_level = min(friction["levels"], key=lambda row: float(row["cost_bps"]))
    worst_level = max(friction["levels"], key=lambda row: float(row["cost_bps"]))
    secondary_lane = secondary["secondary_branch_candidate"]
    pivot_verdict = pivot["pivot_verdict"]

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "secondary_candidate": {
            "label": secondary_lane["label"],
            "family": secondary_lane["family"],
            "best_batch_variant_label": secondary_lane["best_batch_variant_label"],
            "best_batch_cagr": float(secondary_lane["best_batch_cagr"]),
            "best_batch_max_drawdown": float(secondary_lane["best_batch_max_drawdown"]),
            "best_batch_sharpe": float(secondary_lane["best_batch_sharpe"]),
        },
        "current_friction_blocker": {
            "final_decision": friction["final_decision"],
            "decision_reason": friction["decision_reason"],
            "baseline_cost_bps": float(baseline_level["cost_bps"]),
            "baseline_failed_gates": list(baseline_level["failed_gates"]),
            "baseline_cagr": float(baseline_level["cagr"]),
            "baseline_max_drawdown": float(baseline_level["max_drawdown"]),
            "worst_cost_bps": float(worst_level["cost_bps"]),
            "worst_failed_gates": list(worst_level["failed_gates"]),
        },
        "repair_brief": {
            "track": "aggressive_model_development",
            "pivot_source": pivot_verdict["next_model_development_lane"],
            "repair_goal": "flip_spike_reversal_from_friction_pause_to_candidate_promotion_ready",
            "hypothesis": (
                "The spike-reversal upside branch is close enough on gross CAGR that the next value is not a new upside batch, "
                "but a friction-oriented repair loop that clears the current drawdown gate under the existing continuation framing."
            ),
            "mutation_focus": [
                "friction_first_drawdown_repair",
                "preserve_slower_trend_upside_reference",
                "candidate_stage_promotion_after_friction_flip",
            ],
            "execution_sequence": [
                {
                    "step": "candidate_repair_retest",
                    "runner": "python scripts/validate_btc_1d_volatility_spike_reversal_continuation_tightstop_candidate.py --periods 2200",
                },
                {
                    "step": "friction_retest",
                    "runner": "python scripts/validate_btc_1d_volatility_spike_reversal_continuation_tightstop_friction.py --analysis-dir analysis_results --periods 2200",
                },
                {
                    "step": "promotion_recheck",
                    "runner": "python scripts/compare_btc_1d_spike_reversal_secondary_promotion_screen.py",
                },
            ],
            "success_gate": {
                "must_flip_final_decision_from": friction["final_decision"],
                "must_clear_failed_gate": "backtest_max_drawdown",
                "must_unlock_next_gate": "candidate_stage_promotion",
                "do_not_overtake_primary_anchor_until": "promotion_ready=true",
            },
        },
        "decision_summary": [
            (
                f"Do not open a new upside batch yet; repair `{secondary_lane['label']}` first because the current blocker is "
                f"`{friction['final_decision']}` rather than missing raw CAGR."
            ),
            (
                f"Use `{secondary_lane['best_batch_variant_label']}` as the upside reference, but judge progress by whether "
                "`backtest_max_drawdown` disappears from the friction stack."
            ),
            "Only after friction flips away from `pause` should the secondary branch re-enter promotion comparison.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    candidate = report["secondary_candidate"]
    blocker = report["current_friction_blocker"]
    brief = report["repair_brief"]
    lines = [
        "# BTC 1d Secondary Friction Repair Brief",
        "",
        f"- Secondary candidate: `{candidate['label']}`",
        f"- Best batch variant: `{candidate['best_batch_variant_label']}` | `{candidate['best_batch_cagr']:.4f}` CAGR / `{candidate['best_batch_max_drawdown']:.4f}` MDD / Sharpe `{candidate['best_batch_sharpe']:.4f}`",
        f"- Current friction decision: `{blocker['final_decision']}`",
        f"- Baseline failed gates: `{', '.join(blocker['baseline_failed_gates'])}`",
        f"- Repair goal: `{brief['repair_goal']}`",
        f"- Hypothesis: {brief['hypothesis']}",
        "",
        "## Execution Sequence",
    ]
    for row in brief["execution_sequence"]:
        lines.append(f"- `{row['step']}`: `{row['runner']}`")
    lines.extend(
        [
            "",
            "## Success Gate",
            f"- must_flip_final_decision_from: `{brief['success_gate']['must_flip_final_decision_from']}`",
            f"- must_clear_failed_gate: `{brief['success_gate']['must_clear_failed_gate']}`",
            f"- must_unlock_next_gate: `{brief['success_gate']['must_unlock_next_gate']}`",
            f"- do_not_overtake_primary_anchor_until: `{brief['success_gate']['do_not_overtake_primary_anchor_until']}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_secondary_friction_repair_brief_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_secondary_friction_repair_brief_{stamp}.md"
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
