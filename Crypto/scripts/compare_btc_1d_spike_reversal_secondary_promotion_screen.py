from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_attack_next_experiment_brief import (
    build_report as build_next_experiment_brief,
)


ANALYSIS_DIR = Path("analysis_results")
HIGH_CAGR_BATCH_PATH = (
    ANALYSIS_DIR / "btc_1d_volatility_spike_reversal_continuation_high_cagr_batch_20260415T171339Z.json"
)
FRICTION_PATH = (
    ANALYSIS_DIR / "btc_1d_volatility_spike_reversal_continuation_tightstop_friction_20260415T181604Z.json"
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _best_by_upside(rows: list[dict]) -> dict:
    return max(rows, key=lambda row: (float(row["cagr"]), -float(row["max_drawdown"]), float(row["sharpe"])))


def _validation_snapshot_from_friction(friction: dict) -> dict:
    baseline_level = min(friction["levels"], key=lambda row: float(row["cost_bps"]))
    validation_path = ROOT / str(baseline_level["analysis_result_json"])
    validation = _load_json(validation_path)
    metrics = validation["decision_record"]["key_metrics"]
    return {
        "cost_bps": float(baseline_level["cost_bps"]),
        "decision": validation["decision_record"]["decision"],
        "failed_gates": list(validation["decision_record"]["failed_gates"]),
        "strategy_name": validation["config"]["strategy_name"],
        "cagr": float(metrics["cagr"]),
        "max_drawdown": float(metrics["max_drawdown"]),
        "sharpe": float(metrics["sharpe"]),
        "win_rate": float(metrics["win_rate"]),
        "completed_trades": float(metrics["completed_trades"]),
        "validation_json": str(validation_path.relative_to(ROOT)),
    }


def build_report() -> dict:
    next_brief = build_next_experiment_brief()
    batch = _load_json(HIGH_CAGR_BATCH_PATH)
    friction = _load_json(FRICTION_PATH)

    best_variant = _best_by_upside(batch["results"])
    validation_snapshot = _validation_snapshot_from_friction(friction)
    primary = next_brief["next_experiment_brief"]["primary_attack_experiment"]
    secondary = next_brief["next_experiment_brief"]["secondary_attack_experiment"]

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "primary_attack_reference": {
            "label": primary["label"],
            "family": primary["family"],
            "candidate_stage_status": primary["candidate_stage_status"],
            "base_cagr": primary["base_cagr"],
            "base_mdd": primary["base_mdd"],
            "base_sharpe": primary["base_sharpe"],
        },
        "secondary_branch_candidate": {
            "label": secondary["label"],
            "family": secondary["family"],
            "candidate_stage_status": secondary["candidate_stage_status"],
            "best_batch_variant_label": best_variant["variant_label"],
            "best_batch_strategy_name": best_variant["strategy_name"],
            "best_batch_cagr": float(best_variant["cagr"]),
            "best_batch_max_drawdown": float(best_variant["max_drawdown"]),
            "best_batch_sharpe": float(best_variant["sharpe"]),
            "best_batch_completed_trades": int(best_variant["completed_trades"]),
        },
        "validation_snapshot": validation_snapshot,
        "friction_summary": {
            "final_decision": friction["final_decision"],
            "decision_reason": friction["decision_reason"],
            "cost_levels_bps": list(friction["cost_levels_bps"]),
            "all_levels_failed": all(str(level["decision"]).upper() == "FAIL" for level in friction["levels"]),
        },
        "secondary_branch_verdict": {
            "promotion_status": "secondary_upside_branch_only",
            "promotion_ready": False,
            "outranks_primary_attack_retest": False,
            "next_required_gate": "friction_pass_and_candidate_stage_promotion",
            "reason": (
                "The spike-reversal branch still fails the friction stack under every tested cost level, "
                "so it remains a secondary upside branch and does not outrank the trend-dip retest path."
            ),
        },
        "decision_summary": [
            (
                f"Keep `{secondary['label']}` as the secondary upside branch because its best batch variant "
                f"`{best_variant['variant_label']}` still ends in friction `pause`."
            ),
            (
                f"Do not promote the spike-reversal branch ahead of `{primary['label']}` because the next missing proof is "
                "friction pass plus candidate-stage promotion depth, not raw CAGR."
            ),
            (
                "Use the slower-trend batch result as the upside reference, but treat the tighter-stop validation path as "
                "the real promotion gate before any attack conversion."
            ),
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    primary = report["primary_attack_reference"]
    secondary = report["secondary_branch_candidate"]
    validation = report["validation_snapshot"]
    friction = report["friction_summary"]
    verdict = report["secondary_branch_verdict"]
    return "\n".join(
        [
            "# BTC 1d Spike Reversal Secondary Promotion Screen",
            "",
            f"- Primary reference: `{primary['label']}`",
            f"- Secondary branch: `{secondary['label']}`",
            f"- Best upside batch variant: `{secondary['best_batch_variant_label']}` | `{secondary['best_batch_cagr']:.4f}` CAGR / `{secondary['best_batch_max_drawdown']:.4f}` MDD / Sharpe `{secondary['best_batch_sharpe']:.4f}`",
            f"- Validation snapshot: `{validation['strategy_name']}` | `{validation['cagr']:.4f}` CAGR / `{validation['max_drawdown']:.4f}` MDD / Sharpe `{validation['sharpe']:.4f}`",
            f"- Friction final decision: `{friction['final_decision']}`",
            f"- Promotion status: `{verdict['promotion_status']}`",
            f"- Promotion ready: `{verdict['promotion_ready']}`",
            f"- Outranks primary attack retest: `{verdict['outranks_primary_attack_retest']}`",
            f"- Next required gate: `{verdict['next_required_gate']}`",
            f"- Reason: {verdict['reason']}",
            "",
        ]
    )


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_spike_reversal_secondary_promotion_screen_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_spike_reversal_secondary_promotion_screen_{stamp}.md"
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
