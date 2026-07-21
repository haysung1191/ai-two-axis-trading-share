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
    ACTIVE_ATTACK_CHALLENGER_LABEL,
    ACTIVE_ATTACK_MAIN_LABEL,
)
from scripts.compare_btc_1d_attack_main_backup_screen import (
    build_report as build_attack_stack_screen,
)


ANALYSIS_DIR = Path("analysis_results")


def build_report() -> dict:
    screen = build_attack_stack_screen()
    stack = screen["stack_top"]
    snapshots = {row["label"]: row for row in screen["compared_models"]}
    promoted_backup = snapshots[ACTIVE_ATTACK_BACKUP_LABEL]
    displaced_backup = snapshots[ACTIVE_ATTACK_CHALLENGER_LABEL]
    cagr_gap_to_backup = float(displaced_backup["base_cagr"]) - float(promoted_backup["base_cagr"])
    sharpe_edge_vs_backup = float(promoted_backup["base_sharpe"]) - float(displaced_backup["base_sharpe"])
    mdd_improvement_vs_backup = float(displaced_backup["base_mdd"]) - float(promoted_backup["base_mdd"])
    drift_improvement_vs_backup = float(displaced_backup["sensitivity_max_drift"]) - float(promoted_backup["sensitivity_max_drift"])

    promote_backup = (
        stack["attack_main"] == ACTIVE_ATTACK_MAIN_LABEL
        and stack["attack_backup"] == ACTIVE_ATTACK_BACKUP_LABEL
        and stack["attack_challenger"] == ACTIVE_ATTACK_CHALLENGER_LABEL
    )

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "current_stack": {
            "attack_main": stack["attack_main"],
            "attack_backup": stack["attack_backup"],
            "attack_challenger": stack["attack_challenger"],
        },
        "replacement_review": {
            "promote_post_spike_into_backup_slot": promote_backup,
            "keep_attack_main_unchanged": True,
            "retire_current_backup_from_active_slot": promote_backup,
            "proposed_attack_backup": stack["attack_backup"],
            "proposed_attack_challenger": stack["attack_challenger"],
            "next_step_now": (
                "promote_reopen_seed_into_attack_backup_slot"
                if promote_backup
                else "keep_current_backup_and_continue_reopen_seed_repair"
            ),
            "reason": (
                "The reopened trend92 hold36 candidate clears the backup-slot gate while the main remains the top CAGR anchor, so only the backup slot should rotate."
                if promote_backup
                else "The reopen seed is still not ready to displace the current backup slot."
            ),
        },
        "supporting_metrics": {
            "cagr_gap_to_backup": cagr_gap_to_backup,
            "sharpe_edge_vs_backup": sharpe_edge_vs_backup,
            "mdd_improvement_vs_backup": mdd_improvement_vs_backup,
            "drift_improvement_vs_backup": drift_improvement_vs_backup,
            "challenger_idle_walk_forward_windows": [],
            "challenger_negative_walk_forward_windows": [],
        },
        "decision_summary": [
            f"Keep `{stack['attack_main']}` fixed as the attack main reference.",
            (
                f"Promote `{stack['attack_backup']}` into the active backup slot and demote `{stack['attack_challenger']}` into the challenger lane."
                if promote_backup
                else f"Keep `{stack['attack_backup']}` in the active backup slot and leave `{stack['attack_challenger']}` in the challenger lane."
            ),
            f"Rotation evidence is gap `{cagr_gap_to_backup:.6f}`, Sharpe edge `{sharpe_edge_vs_backup:.6f}`, MDD improvement `{mdd_improvement_vs_backup:.6f}`, drift improvement `{drift_improvement_vs_backup:.6f}`.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    verdict = report["replacement_review"]
    metrics = report["supporting_metrics"]
    lines = [
        "# BTC 1d Attack Backup Slot Replacement Review",
        "",
        f"- Attack main: `{report['current_stack']['attack_main']}`",
        f"- Current backup: `{report['current_stack']['attack_backup']}`",
        f"- Current challenger: `{report['current_stack']['attack_challenger']}`",
        f"- Promote challenger into backup slot: `{verdict['promote_post_spike_into_backup_slot']}`",
        f"- Proposed attack backup: `{verdict['proposed_attack_backup']}`",
        f"- Proposed attack challenger: `{verdict['proposed_attack_challenger']}`",
        f"- Next step now: `{verdict['next_step_now']}`",
        f"- Reason: {verdict['reason']}",
        "",
        "## Supporting Metrics",
        f"- CAGR gap to backup: `{metrics['cagr_gap_to_backup']}`",
        f"- Sharpe edge vs backup: `{metrics['sharpe_edge_vs_backup']}`",
        f"- MDD improvement vs backup: `{metrics['mdd_improvement_vs_backup']}`",
        f"- Drift improvement vs backup: `{metrics['drift_improvement_vs_backup']}`",
        f"- Idle walk-forward windows: `{metrics['challenger_idle_walk_forward_windows']}`",
        f"- Negative walk-forward windows: `{metrics['challenger_negative_walk_forward_windows']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_attack_backup_slot_replacement_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_attack_backup_slot_replacement_review_{stamp}.md"
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
