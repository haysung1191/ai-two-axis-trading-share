from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_attack_experiment_board import build_report as build_attack_board
from scripts.compare_btc_1d_attack_main_backup_screen import (
    build_report as build_attack_main_backup_screen,
)


ANALYSIS_DIR = Path("analysis_results")


def _find_row(rows: list[dict], slot: str) -> dict:
    return next(row for row in rows if row["slot"] == slot)


def build_report() -> dict:
    board = build_attack_board()
    main_backup = build_attack_main_backup_screen()

    challenger = _find_row(board["attack_experiment_board"], "attack_challenger")
    backup_screen_row = next(
        row for row in main_backup["compared_models"] if row["role"] == "attack_backup"
    )

    cagr_gap = float(backup_screen_row["base_cagr"]) - float(challenger["cagr"])
    sharpe_edge = float(challenger["sharpe"]) - float(backup_screen_row["base_sharpe"])
    mdd_edge = float(backup_screen_row["base_mdd"]) - float(challenger["max_drawdown"])
    drift_edge = float(backup_screen_row["sensitivity_max_drift"]) - float(challenger["sensitivity_max_drift"])
    has_clean_walk_forward = not challenger.get("negative_walk_forward_windows") and len(challenger.get("idle_walk_forward_windows", [])) <= 1

    rotation_gate = {
        "required_min_sharpe_edge": 0.03,
        "required_min_mdd_improvement": 0.02,
        "allowed_max_cagr_gap": 0.08,
        "required_clean_walk_forward": True,
    }

    rotation_ready = (
        sharpe_edge >= rotation_gate["required_min_sharpe_edge"]
        and mdd_edge >= rotation_gate["required_min_mdd_improvement"]
        and cagr_gap <= rotation_gate["allowed_max_cagr_gap"]
        and has_clean_walk_forward
    )

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "rotation_reference": {
            "attack_backup": backup_screen_row["label"],
            "attack_challenger": challenger["label"],
            "attack_main": board["stack_reference"]["attack_main"],
        },
        "rotation_metrics": {
            "backup_base_cagr": float(backup_screen_row["base_cagr"]),
            "challenger_cagr": float(challenger["cagr"]),
            "cagr_gap_to_backup": cagr_gap,
            "backup_base_mdd": float(backup_screen_row["base_mdd"]),
            "challenger_mdd": float(challenger["max_drawdown"]),
            "mdd_improvement_vs_backup": mdd_edge,
            "backup_base_sharpe": float(backup_screen_row["base_sharpe"]),
            "challenger_sharpe": float(challenger["sharpe"]),
            "sharpe_edge_vs_backup": sharpe_edge,
            "backup_drift": float(backup_screen_row["sensitivity_max_drift"]),
            "challenger_drift": float(challenger["sensitivity_max_drift"]),
            "drift_improvement_vs_backup": drift_edge,
            "challenger_idle_walk_forward_windows": list(challenger.get("idle_walk_forward_windows", [])),
            "challenger_negative_walk_forward_windows": list(challenger.get("negative_walk_forward_windows", [])),
        },
        "rotation_gate": rotation_gate,
        "rotation_verdict": {
            "challenger_rotation_ready": rotation_ready,
            "keep_current_backup": not rotation_ready,
            "challenger_status": "hold_as_attack_challenger_only" if not rotation_ready else "promote_into_attack_backup_slot",
            "next_step_now": "improve_post_spike_cagr_without_losing_quality" if not rotation_ready else "run_backup_slot_replacement_review",
            "reason": (
                "The challenger is cleaner on Sharpe, drawdown, and drift, but the CAGR gap to the current backup is still too large for rotation."
                if not rotation_ready
                else "The challenger clears the quality edge and the CAGR gap threshold, so backup-slot promotion review can start."
            ),
        },
        "decision_summary": [
            f"Compare `{challenger['label']}` against `{backup_screen_row['label']}` for backup-slot rotation, not against the attack main.",
            f"Current CAGR gap to backup is `{cagr_gap:.6f}`, while the allowed maximum gap is `{rotation_gate['allowed_max_cagr_gap']:.2f}`.",
            f"Current quality edge is Sharpe `{sharpe_edge:.6f}`, MDD `{mdd_edge:.6f}`, drift `{drift_edge:.6f}` in favor of the challenger.",
            (
                "The challenger now clears the backup-slot gate, so the next step is replacement review rather than another CAGR-recovery batch."
                if rotation_ready
                else "Keep the challenger on the board, but treat the next mutation target as CAGR recovery rather than another board-promotion step."
            ),
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    verdict = report["rotation_verdict"]
    metrics = report["rotation_metrics"]
    gate = report["rotation_gate"]
    lines = [
        "# BTC 1d Post-Spike Attack Backup Rotation Spec",
        "",
        f"- Attack backup: `{report['rotation_reference']['attack_backup']}`",
        f"- Attack challenger: `{report['rotation_reference']['attack_challenger']}`",
        f"- Rotation ready: `{verdict['challenger_rotation_ready']}`",
        f"- Keep current backup: `{verdict['keep_current_backup']}`",
        f"- Challenger status: `{verdict['challenger_status']}`",
        f"- Next step now: `{verdict['next_step_now']}`",
        f"- Reason: {verdict['reason']}",
        "",
        "## Metrics",
        f"- CAGR gap to backup: `{metrics['cagr_gap_to_backup']}`",
        f"- Sharpe edge vs backup: `{metrics['sharpe_edge_vs_backup']}`",
        f"- MDD improvement vs backup: `{metrics['mdd_improvement_vs_backup']}`",
        f"- Drift improvement vs backup: `{metrics['drift_improvement_vs_backup']}`",
        f"- Idle walk-forward windows: `{metrics['challenger_idle_walk_forward_windows']}`",
        f"- Negative walk-forward windows: `{metrics['challenger_negative_walk_forward_windows']}`",
        "",
        "## Rotation Gate",
        f"- required_min_sharpe_edge: `{gate['required_min_sharpe_edge']}`",
        f"- required_min_mdd_improvement: `{gate['required_min_mdd_improvement']}`",
        f"- allowed_max_cagr_gap: `{gate['allowed_max_cagr_gap']}`",
        f"- required_clean_walk_forward: `{gate['required_clean_walk_forward']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_attack_backup_rotation_spec_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_spike_attack_backup_rotation_spec_{stamp}.md"
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
