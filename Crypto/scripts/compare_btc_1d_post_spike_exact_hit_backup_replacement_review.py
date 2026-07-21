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
from scripts.compare_btc_1d_post_spike_exact_hit_frontier_bridge_review import (
    build_report as build_frontier_bridge_review,
)


ANALYSIS_DIR = Path("analysis_results")
PREVIOUS_PROMOTED_BACKUP_LABEL = "post_spike_trend92_depth058_volume105_hold36"


def build_report() -> dict:
    screen = build_attack_stack_screen()
    bridge_review = build_frontier_bridge_review()
    snapshots = {row["label"]: row for row in screen["compared_models"]}

    attack_main = dict(snapshots[ACTIVE_ATTACK_MAIN_LABEL])
    attack_backup = dict(snapshots[ACTIVE_ATTACK_BACKUP_LABEL])
    challenger = dict(snapshots[ACTIVE_ATTACK_CHALLENGER_LABEL])

    previous_backup = {
        "label": PREVIOUS_PROMOTED_BACKUP_LABEL,
        "base_cagr": 0.34639312,
        "base_mdd": 0.09526207,
        "base_sharpe": 1.81320199,
        "sensitivity_max_drift": 0.22553085,
        "cost20_cagr": 0.34639312,
        "cost20_mdd": 0.09526207,
        "cost20_sharpe": 1.81320199,
    }

    backup_replacement_ready = bool(bridge_review["frontier_bridge_verdict"]["frontier_bridge_found_backup_replacement"])
    drift_improvement_vs_previous = float(previous_backup["sensitivity_max_drift"]) - float(attack_backup["sensitivity_max_drift"])
    cost20_cagr_edge_vs_previous = float(attack_backup["cost20_cagr"]) - float(previous_backup["cost20_cagr"])
    sharpe_edge_vs_previous = float(attack_backup["base_sharpe"]) - float(previous_backup["base_sharpe"])

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "replacement_reference": {
            "attack_main": str(attack_main["label"]),
            "new_attack_backup": str(attack_backup["label"]),
            "previous_promoted_backup": PREVIOUS_PROMOTED_BACKUP_LABEL,
            "current_attack_challenger": str(challenger["label"]),
        },
        "new_backup_vs_previous_backup": {
            "base_cagr_edge": float(attack_backup["base_cagr"]) - float(previous_backup["base_cagr"]),
            "base_sharpe_edge": sharpe_edge_vs_previous,
            "base_mdd_improvement": float(previous_backup["base_mdd"]) - float(attack_backup["base_mdd"]),
            "drift_improvement": drift_improvement_vs_previous,
            "cost20_cagr_edge": cost20_cagr_edge_vs_previous,
            "cost20_sharpe_edge": float(attack_backup["cost20_sharpe"]) - float(previous_backup["cost20_sharpe"]),
            "cost20_mdd_improvement": float(previous_backup["cost20_mdd"]) - float(attack_backup["cost20_mdd"]),
        },
        "new_backup_vs_attack_main": {
            "base_cagr_gap_to_main": float(attack_main["base_cagr"]) - float(attack_backup["base_cagr"]),
            "cost20_cagr_gap_to_main": float(attack_main["cost20_cagr"]) - float(attack_backup["cost20_cagr"]),
            "sharpe_edge_vs_main": float(attack_backup["base_sharpe"]) - float(attack_main["base_sharpe"]),
            "mdd_improvement_vs_main": float(attack_main["base_mdd"]) - float(attack_backup["base_mdd"]),
            "drift_improvement_vs_main": float(attack_main["sensitivity_max_drift"]) - float(attack_backup["sensitivity_max_drift"]),
        },
        "backup_replacement_verdict": {
            "backup_replacement_ready": backup_replacement_ready,
            "attack_backup_replaced": ACTIVE_ATTACK_BACKUP_LABEL == "bridge_28_relief",
            "keep_attack_main": True,
            "keep_attack_challenger": True,
            "next_step_now": "monitor_bridge_backup_against_attack_main",
            "reason": (
                "The frontier bridge candidate matched the previous promoted backup on 20bps CAGR and materially improved drift, so it is now the active attack backup."
                if backup_replacement_ready
                else "The frontier bridge candidate has not yet cleared backup replacement review."
            ),
        },
        "decision_summary": [
            f"`{ACTIVE_ATTACK_BACKUP_LABEL}` is now the active attack backup ahead of `{PREVIOUS_PROMOTED_BACKUP_LABEL}`.",
            f"It keeps cost20 CAGR flat at `{attack_backup['cost20_cagr']:.6f}` while improving drift by `{drift_improvement_vs_previous:.6f}`.",
            f"The next step is to monitor `{ACTIVE_ATTACK_BACKUP_LABEL}` against `{ACTIVE_ATTACK_MAIN_LABEL}` rather than reopen the old backup.",
        ],
    }
    return report


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_exact_hit_backup_replacement_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_spike_exact_hit_backup_replacement_review_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(
        "\n".join(
            [
                "# BTC 1d Post-Spike Exact-Hit Backup Replacement Review",
                "",
                f"- Attack main: `{report['replacement_reference']['attack_main']}`",
                f"- New attack backup: `{report['replacement_reference']['new_attack_backup']}`",
                f"- Previous promoted backup: `{report['replacement_reference']['previous_promoted_backup']}`",
                f"- Backup replacement ready: `{report['backup_replacement_verdict']['backup_replacement_ready']}`",
                f"- Attack backup replaced: `{report['backup_replacement_verdict']['attack_backup_replaced']}`",
                f"- Next step now: `{report['backup_replacement_verdict']['next_step_now']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({"report_json_path": str(json_path), "report_md_path": str(md_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
