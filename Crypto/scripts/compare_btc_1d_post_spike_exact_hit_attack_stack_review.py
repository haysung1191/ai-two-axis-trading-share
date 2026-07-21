from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.attack_active_stack import (
    ACTIVE_ATTACK_BACKUP_LABEL,
    ACTIVE_ATTACK_MAIN_LABEL,
)
from scripts.compare_btc_1d_attack_main_backup_screen import (
    build_report as build_attack_stack_screen,
)
from scripts.compare_btc_1d_post_spike_exact_hit_rotation_review import (
    build_report as build_exact_hit_rotation_review,
)


ANALYSIS_DIR = Path("analysis_results")


def build_report() -> dict:
    stack = build_attack_stack_screen()
    rotation = build_exact_hit_rotation_review()
    snapshots = {row["label"]: row for row in stack["compared_models"]}

    attack_main = dict(snapshots[ACTIVE_ATTACK_MAIN_LABEL])
    promoted_backup = dict(snapshots[ACTIVE_ATTACK_BACKUP_LABEL])
    exact_hit = dict(rotation["frontier_exact_hit_review"])
    cost20 = dict(rotation["cost20_confirmation_review"])
    gate = dict(rotation["rotation_gate"])

    exact_hit_label = str(exact_hit["preferred_exact_hit_variant_label"])
    backup_label = str(promoted_backup["label"])

    base_cagr_edge_vs_backup = float(exact_hit["base_cagr"]) - float(promoted_backup["base_cagr"])
    base_sharpe_edge_vs_backup = float(exact_hit["base_sharpe"]) - float(promoted_backup["base_sharpe"])
    base_mdd_improvement_vs_backup = float(promoted_backup["base_mdd"]) - float(exact_hit["base_max_drawdown"])
    drift_improvement_vs_backup = float(promoted_backup["sensitivity_max_drift"]) - float(exact_hit["sensitivity_max_drift"])
    cost20_cagr_edge_vs_backup = float(cost20["base_cagr"]) - float(promoted_backup["cost20_cagr"])
    cost20_sharpe_edge_vs_backup = float(cost20["base_sharpe"]) - float(promoted_backup["cost20_sharpe"])
    cost20_mdd_improvement_vs_backup = float(promoted_backup["cost20_mdd"]) - float(cost20["base_max_drawdown"])

    base_cagr_gap_to_main = float(attack_main["base_cagr"]) - float(exact_hit["base_cagr"])
    cost20_cagr_gap_to_main = float(attack_main["cost20_cagr"]) - float(cost20["base_cagr"])
    sharpe_edge_vs_main = float(exact_hit["base_sharpe"]) - float(attack_main["base_sharpe"])
    mdd_improvement_vs_main = float(attack_main["base_mdd"]) - float(exact_hit["base_max_drawdown"])
    drift_improvement_vs_main = float(attack_main["sensitivity_max_drift"]) - float(exact_hit["sensitivity_max_drift"])

    backup_replacement_gate = {
        "require_rotation_review_ready": True,
        "require_base_cagr_edge_vs_backup_non_negative": 0.0,
        "require_base_sharpe_edge_vs_backup_non_negative": 0.0,
        "require_base_mdd_improvement_vs_backup_non_negative": 0.0,
        "require_drift_improvement_vs_backup_non_negative": 0.0,
        "require_cost20_cagr_edge_vs_backup_non_negative": 0.0,
    }
    exact_hit_has_backup_pressure = (
        bool(gate["rotation_review_ready"])
        and base_cagr_edge_vs_backup >= backup_replacement_gate["require_base_cagr_edge_vs_backup_non_negative"]
        and base_sharpe_edge_vs_backup >= backup_replacement_gate["require_base_sharpe_edge_vs_backup_non_negative"]
        and base_mdd_improvement_vs_backup >= backup_replacement_gate["require_base_mdd_improvement_vs_backup_non_negative"]
        and drift_improvement_vs_backup >= backup_replacement_gate["require_drift_improvement_vs_backup_non_negative"]
    )
    promote_exact_hit_to_backup_now = (
        exact_hit_has_backup_pressure
        and cost20_cagr_edge_vs_backup >= backup_replacement_gate["require_cost20_cagr_edge_vs_backup_non_negative"]
    )

    main_replacement_gate = {
        "required_min_sharpe_edge": 0.15,
        "required_min_mdd_improvement": 0.05,
        "required_min_drift_improvement": 0.15,
        "allowed_max_base_cagr_gap": 0.04,
        "allowed_max_cost20_cagr_gap": 0.06,
    }
    exact_hit_has_main_pressure = (
        bool(gate["rotation_review_ready"])
        and sharpe_edge_vs_main > main_replacement_gate["required_min_sharpe_edge"]
        and mdd_improvement_vs_main > main_replacement_gate["required_min_mdd_improvement"]
        and drift_improvement_vs_main > main_replacement_gate["required_min_drift_improvement"]
    )
    open_attack_main_replacement_review = (
        promote_exact_hit_to_backup_now
        and exact_hit_has_main_pressure
        and base_cagr_gap_to_main <= main_replacement_gate["allowed_max_base_cagr_gap"]
        and cost20_cagr_gap_to_main <= main_replacement_gate["allowed_max_cost20_cagr_gap"]
    )

    next_step_now = (
        "open_attack_main_replacement_review"
        if open_attack_main_replacement_review
        else "open_exact_hit_backup_replacement_review"
        if promote_exact_hit_to_backup_now
        else "keep_promoted_backup_and_monitor_exact_hit"
    )
    reason = (
        "The exact-hit candidate is now strong enough on both base quality and cost20 retention to replace the current backup and open main-replacement review."
        if open_attack_main_replacement_review
        else "The exact-hit candidate is strong enough to replace the current backup, but it is not yet close enough to the active main for main-replacement review."
        if promote_exact_hit_to_backup_now
        else "The exact-hit candidate improves base CAGR, Sharpe, drawdown, and drift versus the promoted backup, but its 20bps CAGR is still slightly weaker, so it should stay in monitoring rather than replace the current backup."
    )

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "attack_stack_reference": {
            "attack_main": str(attack_main["label"]),
            "promoted_backup": backup_label,
            "exact_hit_candidate": exact_hit_label,
            "rotation_review_json": str(rotation["cost20_confirmation_review"]["diagnostic_json"] or ""),
            "stack_screen_attack_main": str(attack_main["label"]),
        },
        "exact_hit_vs_promoted_backup": {
            "promoted_backup_label": backup_label,
            "exact_hit_candidate_label": exact_hit_label,
            "base_cagr_edge_vs_backup": base_cagr_edge_vs_backup,
            "base_sharpe_edge_vs_backup": base_sharpe_edge_vs_backup,
            "base_mdd_improvement_vs_backup": base_mdd_improvement_vs_backup,
            "drift_improvement_vs_backup": drift_improvement_vs_backup,
            "cost20_cagr_edge_vs_backup": cost20_cagr_edge_vs_backup,
            "cost20_sharpe_edge_vs_backup": cost20_sharpe_edge_vs_backup,
            "cost20_mdd_improvement_vs_backup": cost20_mdd_improvement_vs_backup,
        },
        "exact_hit_vs_attack_main": {
            "attack_main_label": str(attack_main["label"]),
            "exact_hit_candidate_label": exact_hit_label,
            "base_cagr_gap_to_main": base_cagr_gap_to_main,
            "cost20_cagr_gap_to_main": cost20_cagr_gap_to_main,
            "sharpe_edge_vs_main": sharpe_edge_vs_main,
            "mdd_improvement_vs_main": mdd_improvement_vs_main,
            "drift_improvement_vs_main": drift_improvement_vs_main,
        },
        "backup_replacement_gate": backup_replacement_gate,
        "main_replacement_gate": main_replacement_gate,
        "exact_hit_stack_verdict": {
            "rotation_review_ready": bool(gate["rotation_review_ready"]),
            "exact_hit_has_backup_pressure": exact_hit_has_backup_pressure,
            "promote_exact_hit_to_backup_now": promote_exact_hit_to_backup_now,
            "exact_hit_has_main_pressure": exact_hit_has_main_pressure,
            "open_attack_main_replacement_review": open_attack_main_replacement_review,
            "keep_current_promoted_backup": not promote_exact_hit_to_backup_now,
            "next_step_now": next_step_now,
            "reason": reason,
        },
        "decision_summary": [
            f"Exact-hit candidate `{exact_hit_label}` is now attached to the active attack stack comparison, not just the post-spike reopen lane.",
            (
                f"It improves the current promoted backup on base CAGR `{base_cagr_edge_vs_backup:.6f}`, Sharpe `{base_sharpe_edge_vs_backup:.6f}`, MDD `{base_mdd_improvement_vs_backup:.6f}`, and drift `{drift_improvement_vs_backup:.6f}`."
                if exact_hit_has_backup_pressure
                else f"It does not cleanly improve the current promoted backup on every base-quality axis yet."
            ),
            (
                f"It still trails the promoted backup on 20bps CAGR by `{abs(cost20_cagr_edge_vs_backup):.6f}`, so the correct next step is monitoring rather than immediate backup replacement."
                if not promote_exact_hit_to_backup_now
                else "It retains enough cost20 performance to open backup replacement review."
            ),
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    backup = report["exact_hit_vs_promoted_backup"]
    main = report["exact_hit_vs_attack_main"]
    verdict = report["exact_hit_stack_verdict"]
    lines = [
        "# BTC 1d Post-Spike Exact-Hit Attack Stack Review",
        "",
        f"- Attack main: `{report['attack_stack_reference']['attack_main']}`",
        f"- Promoted backup: `{report['attack_stack_reference']['promoted_backup']}`",
        f"- Exact-hit candidate: `{report['attack_stack_reference']['exact_hit_candidate']}`",
        f"- Promote exact hit to backup now: `{verdict['promote_exact_hit_to_backup_now']}`",
        f"- Open attack main replacement review: `{verdict['open_attack_main_replacement_review']}`",
        f"- Next step now: `{verdict['next_step_now']}`",
        "",
        "## Vs Promoted Backup",
        f"- Base CAGR edge: `{backup['base_cagr_edge_vs_backup']}`",
        f"- Base Sharpe edge: `{backup['base_sharpe_edge_vs_backup']}`",
        f"- Base MDD improvement: `{backup['base_mdd_improvement_vs_backup']}`",
        f"- Drift improvement: `{backup['drift_improvement_vs_backup']}`",
        f"- Cost20 CAGR edge: `{backup['cost20_cagr_edge_vs_backup']}`",
        "",
        "## Vs Attack Main",
        f"- Base CAGR gap: `{main['base_cagr_gap_to_main']}`",
        f"- Cost20 CAGR gap: `{main['cost20_cagr_gap_to_main']}`",
        f"- Sharpe edge: `{main['sharpe_edge_vs_main']}`",
        f"- MDD improvement: `{main['mdd_improvement_vs_main']}`",
        f"- Drift improvement: `{main['drift_improvement_vs_main']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_exact_hit_attack_stack_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_spike_exact_hit_attack_stack_review_{stamp}.md"
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
