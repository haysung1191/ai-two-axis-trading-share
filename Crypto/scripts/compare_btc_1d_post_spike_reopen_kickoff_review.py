from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_post_spike_reopen_candidate_review import (
    build_report as build_reopen_candidate_review,
)


ANALYSIS_DIR = Path("analysis_results")


def _classify_seed(candidate: dict) -> str:
    if str(candidate.get("source")) == "repair_winner_stage_review":
        return "repair_winner_seed"
    if bool(candidate.get("exact_hit", False)):
        return "frontier_exact_hit_seed"
    if bool(candidate.get("drift_guardrail_passed", False)):
        return "frontier_guardrail_seed"
    return "frontier_gap_only_seed"


def build_report() -> dict:
    reopen = build_reopen_candidate_review()
    candidates = list(reopen["reopen_candidates"])
    preferred_seed_label = str(reopen["reopen_gate"]["preferred_reopen_seed"])

    preferred_seed = next(
        (candidate for candidate in candidates if str(candidate["candidate_label"]) == preferred_seed_label),
        candidates[0],
    )

    backup_seed = next(
        (
            candidate
            for candidate in candidates
            if str(candidate["candidate_label"]) != preferred_seed_label
            and (
                bool(candidate.get("candidate_stage_ready", False))
                or bool(candidate.get("drift_guardrail_passed", False))
                or int(candidate.get("negative_window_count", 0)) == 0
            )
        ),
        candidates[1] if len(candidates) > 1 else preferred_seed,
    )
    next_step_now = (
        "launch_exact_hit_rotation_review"
        if bool(preferred_seed.get("exact_hit", False)) or str(reopen["reopen_gate"].get("next_step_now")) == "promote_exact_hit_into_rotation_review"
        else "launch_reopen_seed_validation_cycle"
    )
    execution_order = (
        [
            f"promote::{preferred_seed_label}",
            f"rotation_review::{preferred_seed_label}",
            f"compare_against::{backup_seed['candidate_label']}",
        ]
        if next_step_now == "launch_exact_hit_rotation_review"
        else [
            f"revalidate::{preferred_seed_label}",
            f"compare_against::{backup_seed['candidate_label']}",
        ]
    )

    kickoff = {
        "preferred_seed_label": preferred_seed_label,
        "preferred_seed_class": _classify_seed(preferred_seed),
        "preferred_seed_source": str(preferred_seed["source"]),
        "preferred_seed_stage_ready": bool(preferred_seed.get("candidate_stage_ready", False)),
        "backup_seed_label": str(backup_seed["candidate_label"]),
        "backup_seed_class": _classify_seed(backup_seed),
        "backup_seed_source": str(backup_seed["source"]),
        "next_step_now": next_step_now,
        "execution_order": execution_order,
    }

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "kickoff_reference": {
            "attack_main": reopen["reopen_reference"]["attack_main"],
            "promoted_backup": reopen["reopen_reference"]["promoted_backup"],
            "monitoring_candidate": reopen["reopen_reference"]["monitoring_candidate"],
            "current_hold36_line_closed": reopen["reopen_reference"]["current_hold36_line_closed"],
        },
        "reopen_kickoff": kickoff,
        "preferred_seed_metrics": {
            "candidate_label": str(preferred_seed["candidate_label"]),
            "base_cagr": float(preferred_seed["base_cagr"]),
            "base_sharpe": float(preferred_seed["base_sharpe"]),
            "base_max_drawdown": float(preferred_seed["base_max_drawdown"]),
            "sensitivity_max_drift": float(preferred_seed["sensitivity_max_drift"]),
            "negative_window_count": int(preferred_seed["negative_window_count"]),
        },
        "backup_seed_metrics": {
            "candidate_label": str(backup_seed["candidate_label"]),
            "base_cagr": float(backup_seed["base_cagr"]),
            "base_sharpe": float(backup_seed["base_sharpe"]),
            "base_max_drawdown": float(backup_seed["base_max_drawdown"]),
            "sensitivity_max_drift": float(backup_seed["sensitivity_max_drift"]),
            "negative_window_count": int(backup_seed["negative_window_count"]),
        },
        "decision_summary": [
            (
                f"Preferred reopen seed is `{preferred_seed_label}` and should move into rotation review first."
                if next_step_now == "launch_exact_hit_rotation_review"
                else f"Preferred reopen seed is `{preferred_seed_label}` and should be validated first."
            ),
            f"Backup reopen seed is `{backup_seed['candidate_label']}` and should be compared immediately after the preferred seed.",
            (
                "The current hold36 local axis family already produced an exact hit, so the workflow should shift from reopen search to promotion review."
                if next_step_now == "launch_exact_hit_rotation_review"
                else "The current hold36 local axis family remains closed, so the reopen path should start from external seeds rather than additional hold36 tweaks."
            ),
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    kickoff = report["reopen_kickoff"]
    preferred = report["preferred_seed_metrics"]
    backup = report["backup_seed_metrics"]
    lines = [
        "# BTC 1d Post-Spike Reopen Kickoff Review",
        "",
        f"- Attack main: `{report['kickoff_reference']['attack_main']}`",
        f"- Promoted backup: `{report['kickoff_reference']['promoted_backup']}`",
        f"- Monitoring candidate: `{report['kickoff_reference']['monitoring_candidate']}`",
        f"- Current hold36 line closed: `{report['kickoff_reference']['current_hold36_line_closed']}`",
        f"- Preferred seed: `{kickoff['preferred_seed_label']}`",
        f"- Preferred seed class: `{kickoff['preferred_seed_class']}`",
        f"- Backup seed: `{kickoff['backup_seed_label']}`",
        f"- Next step now: `{kickoff['next_step_now']}`",
        "",
        "## Preferred Seed",
        f"- CAGR=`{preferred['base_cagr']}` Sharpe=`{preferred['base_sharpe']}` MDD=`{preferred['base_max_drawdown']}` drift=`{preferred['sensitivity_max_drift']}`",
        "",
        "## Backup Seed",
        f"- CAGR=`{backup['base_cagr']}` Sharpe=`{backup['base_sharpe']}` MDD=`{backup['base_max_drawdown']}` drift=`{backup['sensitivity_max_drift']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_post_spike_reopen_kickoff_review_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_post_spike_reopen_kickoff_review_{stamp}.md"
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
