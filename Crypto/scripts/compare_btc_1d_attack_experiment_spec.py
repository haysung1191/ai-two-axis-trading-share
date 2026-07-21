from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_attack_next_experiment_brief import (
    build_report as build_next_experiment_brief,
)


ANALYSIS_DIR = Path("analysis_results")


def _load_attack_rule_seed(analysis_dir: Path = ANALYSIS_DIR) -> dict[str, Any]:
    path = analysis_dir / "btc_1d_attack_common_rules_latest.json"
    if not path.exists():
        return {
            "available": False,
            "artifact_path": str(path),
            "leader_count": 0,
            "priority_hints": [],
            "recommended_attack_rule_seed": {},
        }
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "available": True,
        "artifact_path": str(path),
        "leader_count": int(payload.get("leader_count", 0)),
        "priority_hints": list(payload.get("priority_hints", [])),
        "recommended_attack_rule_seed": dict(payload.get("recommended_attack_rule_seed", {})),
    }


def build_report() -> dict:
    next_brief = build_next_experiment_brief()
    attack_seed = _load_attack_rule_seed()
    primary = dict(next_brief["next_experiment_brief"]["primary_attack_experiment"])
    secondary = dict(next_brief["next_experiment_brief"]["secondary_attack_experiment"])

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "experiment_spec": {
            "track": "aggressive_model_development",
            "primary_label": primary["label"],
            "primary_family": primary["family"],
            "primary_hypothesis": primary["hypothesis"],
            "primary_goal": "compress_drawdown_without_losing_attack_candidate_relevance",
            "secondary_label": secondary["label"],
            "secondary_family": secondary["family"],
            "secondary_role": "follow_after_primary_retest",
        },
        "attack_rule_seed": attack_seed,
        "mutation_plan": {
            "primary_mutation_axes": [
                {
                    "axis": "exit_shape",
                    "reason": "Current near-miss already has candidate-stage evidence, so exit compression is the highest-value first pass.",
                    "runner": "python scripts/run_btc_1d_trend_dip_reversal_breakout_exit_compression_batch.py --analysis-dir analysis_results --periods 2200 --apply-attack-seed",
                    "seed_alignment": {
                        "trend_ema_window": attack_seed["recommended_attack_rule_seed"].get("trend_ema_window"),
                        "stop_ema_window": attack_seed["recommended_attack_rule_seed"].get("stop_ema_window"),
                        "max_hold_bars": attack_seed["recommended_attack_rule_seed"].get("max_hold_bars"),
                    },
                },
                {
                    "axis": "exit_symmetry",
                    "reason": "The current candidate already uses symmetry v4 framing, so symmetry retuning is the second pass to preserve attack profile while shrinking drawdown.",
                    "runner": "python scripts/run_btc_1d_trend_dip_reversal_breakout_exit_symmetry_batch.py --analysis-dir analysis_results --periods 2200",
                    "seed_alignment": {
                        "trend_ema_window": attack_seed["recommended_attack_rule_seed"].get("trend_ema_window"),
                        "min_volume_ratio": attack_seed["recommended_attack_rule_seed"].get("min_volume_ratio"),
                        "volume_lookback": attack_seed["recommended_attack_rule_seed"].get("volume_lookback"),
                    },
                },
            ],
            "validation_sequence": [
                {
                    "step": "candidate_validation",
                    "runner": "python scripts/validate_btc_1d_trend_dip_reversal_breakout_tsmh_candidate.py --periods 2200",
                },
                {
                    "step": "walk_forward",
                    "runner": "python scripts/run_btc_1d_walk_forward_trend_dip_reversal_breakout_tsmh_candidate.py --periods 2200",
                },
                {
                    "step": "friction",
                    "runner": "python scripts/validate_btc_1d_trend_dip_reversal_breakout_tsmh_friction.py --analysis-dir analysis_results --periods 2200",
                },
            ],
        },
        "success_gate": {
            "primary_target_role": primary["success_gate"]["target_role"],
            "must_improve": primary["success_gate"]["must_improve"],
            "ceiling_mdd_gap_to_attack_main_pct": primary["success_gate"]["ceiling_mdd_gap_to_attack_main_pct"],
            "floor_validation_depth": primary["success_gate"]["floor_validation_depth"],
            "keep_secondary_deferred_until_primary_complete": True,
        },
        "decision_summary": [
            f"Run exit compression first for {primary['label']} because the bottleneck is drawdown, not missing gross CAGR.",
            f"Run exit symmetry second for {primary['label']} if compression alone does not close the MDD gap enough.",
            (
                "Keep the primary retest anchored to the current attack seed: "
                f"trend EMA `{attack_seed['recommended_attack_rule_seed'].get('trend_ema_window', 'n/a')}`, "
                f"volume lookback `{attack_seed['recommended_attack_rule_seed'].get('volume_lookback', 'n/a')}`, "
                f"min volume ratio `{attack_seed['recommended_attack_rule_seed'].get('min_volume_ratio', 'n/a')}`."
            ),
            f"Do not promote {secondary['label']} ahead of the primary retest; keep it as the secondary upside branch only after the primary sequence completes.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    spec = report["experiment_spec"]
    attack_seed = report["attack_rule_seed"]
    plan = report["mutation_plan"]
    gate = report["success_gate"]
    lines = [
        "# BTC 1d Attack Experiment Spec",
        "",
        f"- Track: `{spec['track']}`",
        f"- Primary label: `{spec['primary_label']}`",
        f"- Primary family: `{spec['primary_family']}`",
        f"- Primary goal: `{spec['primary_goal']}`",
        f"- Secondary label: `{spec['secondary_label']}`",
        f"- Secondary role: `{spec['secondary_role']}`",
        "",
        "## Attack Rule Seed",
        f"- Available: `{attack_seed['available']}`",
        f"- Leader count: `{attack_seed['leader_count']}`",
        f"- Artifact path: `{attack_seed['artifact_path']}`",
        (
            "- Seed params: "
            + ", ".join(
                f"`{key}={value}`" for key, value in attack_seed["recommended_attack_rule_seed"].items()
            )
            if attack_seed["recommended_attack_rule_seed"]
            else "- Seed params: `n/a`"
        ),
        "",
        "## Mutation Plan",
    ]
    for row in plan["primary_mutation_axes"]:
        lines.extend(
            [
                f"- Axis: `{row['axis']}`",
                f"  runner: `{row['runner']}`",
                (
                    "  seed_alignment: "
                    + ", ".join(f"`{key}={value}`" for key, value in row["seed_alignment"].items())
                ),
                f"  reason: {row['reason']}",
            ]
        )
    lines.extend(["", "## Validation Sequence"])
    for row in plan["validation_sequence"]:
        lines.append(f"- `{row['step']}`: `{row['runner']}`")
    lines.extend(
        [
            "",
            "## Success Gate",
            f"- target_role: `{gate['primary_target_role']}`",
            f"- must_improve: `{gate['must_improve']}`",
            f"- ceiling_mdd_gap_to_attack_main_pct: `{gate['ceiling_mdd_gap_to_attack_main_pct']}`",
            f"- floor_validation_depth: `{gate['floor_validation_depth']}`",
            f"- keep_secondary_deferred_until_primary_complete: `{gate['keep_secondary_deferred_until_primary_complete']}`",
            "",
        ]
    )
    lines.extend(f"- {line}" for line in report["decision_summary"])
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_attack_experiment_spec_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_attack_experiment_spec_{stamp}.md"
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
