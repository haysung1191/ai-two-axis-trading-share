from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


ANALYSIS_DIR = Path("analysis_results")
EXIT_COMPRESSION_PATH = ANALYSIS_DIR / "btc_1d_trend_dip_reversal_breakout_exit_compression_batch_20260419T140432Z.json"
VALIDATION_PATHS = [
    ANALYSIS_DIR / "btc_1d_trend_dip_reversal_breakout_v3_exit_compression_volume_lookback_16_seeded_paper_validation_20260419T141020Z.json",
    ANALYSIS_DIR / "btc_1d_trend_dip_reversal_breakout_v8_exit_compression_structure_stack_seeded_paper_validation_20260419T141034Z.json",
]
REPAIR_PATHS = [
    ANALYSIS_DIR / "btc_1d_trend_dip_reversal_breakout_overfitting_repair_batch_20260419T141708Z.json",
    ANALYSIS_DIR / "btc_1d_trend_dip_reversal_breakout_overfitting_repair_batch_20260419T145446Z.json",
    ANALYSIS_DIR / "btc_1d_trend_dip_reversal_breakout_overfitting_repair_batch_20260419T150227Z.json",
]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _float(row: dict, key: str) -> float:
    return float(row[key])


def _best_keep(rows: list[dict]) -> dict:
    keep_rows = [row for row in rows if row.get("decision") == "KEEP"]
    if not keep_rows:
        raise ValueError("No KEEP rows available in exit-compression report.")
    return max(
        keep_rows,
        key=lambda row: (
            _float(row, "sharpe"),
            _float(row, "cagr"),
            -_float(row, "max_drawdown"),
        ),
    )


def _best_by_cagr(rows: list[dict]) -> dict:
    return max(
        rows,
        key=lambda row: (
            _float(row, "cagr"),
            _float(row, "sharpe"),
            -_float(row, "max_drawdown"),
        ),
    )


def _best_by_sensitivity(rows: list[dict]) -> dict:
    viable_rows = [
        row
        for row in rows
        if _float(row, "cagr") >= 0.18 and _float(row, "sharpe") >= 0.9
    ]
    search_rows = viable_rows or rows
    return min(
        search_rows,
        key=lambda row: (
            _float(row, "sensitivity_max_drift"),
            _float(row, "max_drawdown"),
            -_float(row, "cagr"),
        ),
    )


def _best_final_attempt(rows: list[dict]) -> dict:
    return min(
        rows,
        key=lambda row: (
            len(row.get("failed_gates", [])),
            _float(row, "max_drawdown"),
            -_float(row, "sharpe"),
            -_float(row, "cagr"),
        ),
    )


def _row_snapshot(row: dict) -> dict:
    snapshot = {
        "variant_label": row["variant_label"],
        "strategy_name": row["strategy_name"],
        "decision": row.get("decision"),
        "sharpe": _float(row, "sharpe"),
        "cagr": _float(row, "cagr"),
        "max_drawdown": _float(row, "max_drawdown"),
        "failed_gates": list(row.get("failed_gates", [])),
        "parameters": dict(row.get("parameters", {})),
    }
    if "sensitivity_max_drift" in row:
        snapshot["sensitivity_max_drift"] = _float(row, "sensitivity_max_drift")
    if "unstable_parameters" in row:
        snapshot["unstable_parameters"] = list(row.get("unstable_parameters", []))
    return snapshot


def _validation_snapshot(row: dict) -> dict:
    decision = row["decision_record"]
    return {
        "artifact_label": row["config"]["artifact_label"],
        "strategy_name": row["config"]["strategy_name"],
        "decision": decision["decision"],
        "failed_gates": list(decision["failed_gates"]),
        "sharpe": float(decision["key_metrics"]["sharpe"]),
        "cagr": float(decision["key_metrics"]["cagr"]),
        "max_drawdown": float(decision["key_metrics"]["max_drawdown"]),
    }


def build_report() -> dict:
    exit_compression = _load_json(EXIT_COMPRESSION_PATH)
    validations = [_load_json(path) for path in VALIDATION_PATHS]
    repairs = [_load_json(path) for path in REPAIR_PATHS]

    stage1_best = _best_keep(exit_compression["results"])
    validation_rows = [_validation_snapshot(row) for row in validations]
    repair_rows = [item for report in repairs for item in report["results"]]

    best_cagr_repair = _best_by_cagr(repair_rows)
    best_sensitivity_repair = _best_by_sensitivity(repair_rows)
    final_attempt = _best_final_attempt(repairs[-1]["results"])

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "family": {
            "label": "trend_dip_reversal_breakout",
            "status": "exhausted_for_now",
            "handoff_action": "switch_to_next_attack_family_search",
        },
        "stage1_summary": {
            "survivor_labels": list(exit_compression["stage1_survivors"]),
            "best_stage1_candidate": _row_snapshot(stage1_best),
        },
        "candidate_validation_summary": {
            "validated_candidates": validation_rows,
            "all_failed": all(row["decision"] == "FAIL" for row in validation_rows),
            "shared_failed_gates": sorted(set.intersection(*(set(row["failed_gates"]) for row in validation_rows))),
        },
        "repair_summary": {
            "best_cagr_repair": _row_snapshot(best_cagr_repair),
            "best_sensitivity_repair": _row_snapshot(best_sensitivity_repair),
            "final_exit_repair_attempt": _row_snapshot(final_attempt),
        },
        "exhaustion_verdict": {
            "verdict": "pause_family",
            "primary_blockers": [
                "candidate validation still fails on drawdown and overfitting gates",
                "stop24 branch improves CAGR but remains above the drawdown bar",
                "faster88 branch improves sensitivity but breaks the return-quality balance",
                "latest exit-side repair still does not clear the combined gate set",
            ],
            "do_not_continue_conditions": [
                "do not spend the next cycle on more reversal_strength_threshold micro-tuning",
                "do not spend the next cycle on stop24 entry micro-adjustments that preserve the same state",
                "do not keep pushing faster88 exit tweaks without a new structural hypothesis",
            ],
            "next_transition_hint": "freeze this family as exhausted and move the attack search to a distinct next-family lane",
        },
        "decision_summary": [
            f"Stage1 reopened the family through `{stage1_best['variant_label']}`, but both promoted candidates failed identical validation gates.",
            f"`{best_cagr_repair['variant_label']}` is the best return-side repair, but it still sits above the target drawdown line.",
            f"`{best_sensitivity_repair['variant_label']}` is the best sensitivity repair, but it does not preserve the attack-quality return profile.",
            f"`{final_attempt['variant_label']}` is the closest latest exit-side attempt, and it still fails the combined promotion criteria.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    stage1 = report["stage1_summary"]["best_stage1_candidate"]
    repair = report["repair_summary"]
    verdict = report["exhaustion_verdict"]
    lines = [
        "# BTC 1d Trend Dip Family Handoff",
        "",
        f"- Family: `{report['family']['label']}`",
        f"- Status: `{report['family']['status']}`",
        f"- Handoff action: `{report['family']['handoff_action']}`",
        f"- Best stage1 candidate: `{stage1['variant_label']}` | `{stage1['cagr']:.4f}` CAGR / `{stage1['max_drawdown']:.4f}` MDD / Sharpe `{stage1['sharpe']:.4f}`",
        f"- Best CAGR repair: `{repair['best_cagr_repair']['variant_label']}` | `{repair['best_cagr_repair']['cagr']:.4f}` CAGR / `{repair['best_cagr_repair']['max_drawdown']:.4f}` MDD / drift `{repair['best_cagr_repair']['sensitivity_max_drift']:.4f}`",
        f"- Best sensitivity repair: `{repair['best_sensitivity_repair']['variant_label']}` | drift `{repair['best_sensitivity_repair']['sensitivity_max_drift']:.4f}` / `{repair['best_sensitivity_repair']['cagr']:.4f}` CAGR / `{repair['best_sensitivity_repair']['max_drawdown']:.4f}` MDD",
        f"- Final exit-side attempt: `{repair['final_exit_repair_attempt']['variant_label']}`",
        "",
        "## Blockers",
    ]
    for item in verdict["primary_blockers"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Do Not Continue"])
    for item in verdict["do_not_continue_conditions"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_trend_dip_family_handoff_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_trend_dip_family_handoff_{stamp}.md"
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
