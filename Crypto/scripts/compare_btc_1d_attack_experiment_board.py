from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_attack_main_backup_screen import (
    build_report as build_attack_stack_screen,
)
from scripts.compare_btc_1d_attack_challenger_rotation_review import (
    build_report as build_attack_challenger_rotation_review,
)
from scripts.compare_btc_1d_attack_challenger_validation_review import (
    build_report as build_attack_challenger_validation_review,
)
from scripts.compare_btc_1d_attack_challenger_promotion_review import (
    build_report as build_attack_challenger_promotion_review,
)
from scripts.compare_btc_1d_attack_challenger_rotation_application_readiness import (
    build_report as build_attack_challenger_rotation_application_readiness,
)
from scripts.compare_btc_1d_post_spike_hold36_drift_repair_candidates import (
    build_report as build_hold36_drift_repair_candidates,
)


ANALYSIS_DIR = Path("analysis_results")


def _sort_board_rows(compared_models: list[dict]) -> list[dict]:
    role_priority = {
        "attack_main": 0,
        "attack_backup": 1,
        "attack_challenger": 2,
    }
    rows: list[dict] = []
    for model in sorted(compared_models, key=lambda item: role_priority.get(item["role"], 99)):
        row = {
            "slot": model["role"],
            "label": model["label"],
            "cagr": model.get("cagr", model.get("base_cagr")),
            "max_drawdown": model.get("max_drawdown", model.get("base_mdd")),
            "sharpe": model.get("sharpe", model.get("base_sharpe")),
            "cost20_cagr": model["cost20_cagr"],
            "cost20_mdd": model["cost20_mdd"],
            "cost20_sharpe": model["cost20_sharpe"],
            "sensitivity_max_drift": model["sensitivity_max_drift"],
            "board_status": (
                "active_reference"
                if model["role"] == "attack_main"
                else "keep_ready"
                if model["role"] == "attack_backup"
                else "experiment_challenger"
            ),
        }
        if "negative_walk_forward_windows" in model:
            row["negative_walk_forward_windows"] = list(model["negative_walk_forward_windows"])
        if "idle_walk_forward_windows" in model:
            row["idle_walk_forward_windows"] = list(model["idle_walk_forward_windows"])
        rows.append(row)
    return rows


def _recommend_board_research_step(board_rows: list[dict]) -> dict[str, str]:
    try:
        application_readiness = build_attack_challenger_rotation_application_readiness()
        readiness = application_readiness["application_readiness"]
        mapping = application_readiness["approved_candidate_mapping"]
        if readiness.get("rotation_already_applied"):
            pass
        elif not readiness["ready_to_apply_rotation"] and mapping["approved_attack_challenger"]:
            return {
                "target_slot": "attack_challenger",
                "target_label": str(mapping["approved_attack_challenger"]),
                "next_research_step_now": str(readiness["next_step_now"]),
                "reason": str(readiness["reason"]),
            }
    except FileNotFoundError:
        pass

    try:
        promotion_review = build_attack_challenger_promotion_review()
        verdict = promotion_review["promotion_review"]
        if verdict.get("rotation_already_applied"):
            pass
        elif verdict["promote_attack_challenger_now"]:
            return {
                "target_slot": "attack_challenger",
                "target_label": str(verdict["approved_attack_challenger"]),
                "next_research_step_now": str(verdict["next_step_now"]),
                "reason": str(verdict["reason"]),
            }
    except FileNotFoundError:
        pass

    try:
        validation_review = build_attack_challenger_validation_review()
        verdict = validation_review["validation_review"]
        if verdict.get("rotation_already_applied"):
            pass
        elif verdict["approve_rotation_now"]:
            return {
                "target_slot": "attack_challenger",
                "target_label": str(verdict["candidate_label"]),
                "next_research_step_now": str(verdict["next_step_now"]),
                "reason": str(verdict["reason"]),
            }
    except FileNotFoundError:
        pass

    try:
        drift_repair = build_hold36_drift_repair_candidates()
        verdict = drift_repair["drift_repair_verdict"]
        top_candidate = str(verdict.get("top_candidate", ""))
        active_suffix = board_rows[2]["label"].removeprefix("post_spike_")
        if verdict["top_candidate_beats_active_rotation_gate"] and not active_suffix.endswith(top_candidate):
            return {
                "target_slot": "attack_challenger",
                "target_label": top_candidate,
                "next_research_step_now": str(verdict["next_step_now"]),
                "reason": str(verdict["reason"]),
            }
    except FileNotFoundError:
        pass

    try:
        rotation_review = build_attack_challenger_rotation_review()
        review = rotation_review["rotation_review"]
        current_rotation_reference = str(rotation_review.get("active_challenger_reference", {}).get("label", ""))
        if current_rotation_reference and current_rotation_reference != board_rows[2]["label"]:
            pass
        elif review["open_rotation_review"]:
            return {
                "target_slot": "attack_challenger",
                "target_label": str(review["proposed_attack_challenger"]),
                "next_research_step_now": str(review["next_step_now"]),
                "reason": str(review["reason"]),
            }
    except FileNotFoundError:
        pass

    challenger = next(row for row in board_rows if row["slot"] == "attack_challenger")
    negative_windows = list(challenger.get("negative_walk_forward_windows", []))
    idle_windows = list(challenger.get("idle_walk_forward_windows", []))
    if not negative_windows and idle_windows:
        return {
            "target_slot": "attack_challenger",
            "target_label": str(challenger["label"]),
            "next_research_step_now": "expand_post_spike_trend_family_to_recover_idle_windows",
            "reason": (
                f"{challenger['label']} cleared negative walk-forward windows, but idle "
                f"windows {idle_windows} still leave attack-side CAGR on the table."
            ),
        }
    return {
        "target_slot": "attack_backup",
        "target_label": str(challenger["label"]),
        "next_research_step_now": "pressure_test_frontier_bridge_backup_against_main",
        "reason": (
            "The board has no clean idle-window recovery target, so keep pressure-testing "
            "the active backup against the main stack."
        ),
    }


def build_report() -> dict:
    screen = build_attack_stack_screen()
    board_rows = _sort_board_rows(screen["compared_models"])
    research_focus = _recommend_board_research_step(board_rows)

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "stack_reference": {
            "attack_main": screen["stack_top"]["attack_main"],
            "attack_backup": screen["stack_top"]["attack_backup"],
            "candidate_challenger": screen["stack_top"]["attack_challenger"],
        },
        "attack_experiment_board": board_rows,
        "attack_research_focus": research_focus,
        "board_verdict": {
            "active_attack_main": screen["stack_top"]["attack_main"],
            "active_attack_backup": screen["stack_top"]["attack_backup"],
            "active_attack_challenger": screen["stack_top"]["attack_challenger"],
            "board_ready": True,
            "replace_attack_main_now": False,
            "replace_attack_backup_now": False,
            "next_step_now": "monitor_active_post_spike_challenger_against_attack_stack",
            "next_research_step_now": research_focus["next_research_step_now"],
            "reason": "The active board keeps ratio112 as main and bridge_28_relief as backup while holding the approved trend960 post-spike variant in the live challenger lane because it improved quality without overtaking the stack on CAGR.",
        },
        "decision_summary": [
            f"Keep `{screen['stack_top']['attack_main']}` as the active attack main reference.",
            f"Keep `{screen['stack_top']['attack_backup']}` in the active attack backup lane.",
            f"Keep `{screen['stack_top']['attack_challenger']}` on the experiment board as the next challenger slot.",
            "Use the next cycle to monitor whether the approved trend960 post-spike challenger can pressure the active stack without giving back its quality edge.",
            f"Next attack research step: `{research_focus['next_research_step_now']}`.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    verdict = report["board_verdict"]
    lines = [
        "# BTC 1d Attack Experiment Board",
        "",
        f"- Active attack main: `{verdict['active_attack_main']}`",
        f"- Active attack backup: `{verdict['active_attack_backup']}`",
        f"- Active attack challenger: `{verdict['active_attack_challenger']}`",
        f"- Board ready: `{verdict['board_ready']}`",
        f"- Replace attack main now: `{verdict['replace_attack_main_now']}`",
        f"- Replace attack backup now: `{verdict['replace_attack_backup_now']}`",
        f"- Next step now: `{verdict['next_step_now']}`",
        f"- Next research step now: `{verdict['next_research_step_now']}`",
        f"- Reason: {verdict['reason']}",
        "",
        "## Board",
    ]
    for row in report["attack_experiment_board"]:
        lines.extend(
            [
                f"- `{row['slot']}` | `{row['label']}` | status=`{row['board_status']}`",
                f"  CAGR=`{row['cagr']}` Sharpe=`{row['sharpe']}` MDD=`{row['max_drawdown']}`",
                f"  20bps CAGR=`{row['cost20_cagr']}` Sharpe=`{row['cost20_sharpe']}` MDD=`{row['cost20_mdd']}`",
                f"  drift=`{row['sensitivity_max_drift']}`",
            ]
        )
        if "negative_walk_forward_windows" in row:
            lines.append(f"  negative_walk_forward_windows=`{row['negative_walk_forward_windows']}`")
        if "idle_walk_forward_windows" in row:
            lines.append(f"  idle_walk_forward_windows=`{row['idle_walk_forward_windows']}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_attack_experiment_board_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_attack_experiment_board_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_attack_experiment_board_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_attack_experiment_board_md_latest.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_payload = _render_markdown(report)
    md_path.write_text(md_payload, encoding="utf-8")
    latest_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    latest_md.write_text(md_payload, encoding="utf-8")
    print(
        json.dumps(
            {
                "report_json_path": str(json_path),
                "report_md_path": str(md_path),
                "latest_json_path": str(latest_json),
                "latest_md_path": str(latest_md),
                "report": report,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
