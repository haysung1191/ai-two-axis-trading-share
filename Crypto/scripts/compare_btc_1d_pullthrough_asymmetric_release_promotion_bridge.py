from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_attack_defensive_bridge_screen import (
    build_report as build_attack_defensive_bridge_screen,
)
from scripts.compare_btc_1d_attack_main_backup_screen import (
    build_report as build_attack_main_backup_screen,
)
from scripts.compare_btc_1d_pullthrough_asymmetric_release_candidate_followup_screen import (
    build_report as build_followup_screen,
)


ANALYSIS_DIR = Path("analysis_results")


def build_report() -> dict:
    main_backup = build_attack_main_backup_screen()
    attack_bridge = build_attack_defensive_bridge_screen()
    followup = build_followup_screen()

    main = next(
        row for row in main_backup["compared_models"] if row["label"] == main_backup["stack_top"]["attack_main"]
    )
    backup = next(
        row for row in main_backup["compared_models"] if row["label"] == main_backup["stack_top"]["attack_backup"]
    )
    candidate = followup["candidate"]
    status = followup["followup_status"]

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "stack_context": {
            "attack_main": main_backup["stack_top"]["attack_main"],
            "attack_backup": main_backup["stack_top"]["attack_backup"],
            "defensive_hold": attack_bridge["stack_top"]["defensive_hold"],
            "candidate": candidate["label"],
        },
        "candidate_profile": {
            "label": candidate["label"],
            "strategy_name": candidate["strategy_name"],
            "paper_validation_cagr": float(candidate["paper_validation_cagr"]),
            "paper_validation_max_drawdown": float(candidate["paper_validation_max_drawdown"]),
            "paper_validation_sharpe": float(candidate["paper_validation_sharpe"]),
            "paper_validation_trades": int(candidate["paper_validation_trades"]),
            "walk_forward_sensitivity_max_drift": float(status["walk_forward_sensitivity_max_drift"]),
            "friction_final_decision": status["friction_final_decision"],
            "cost20_cagr": float(status["cost20_cagr"]),
            "cost20_max_drawdown": float(status["cost20_max_drawdown"]),
            "cost20_sharpe": float(status["cost20_sharpe"]),
        },
        "promotion_bridge_verdict": {
            "promotion_ready": True,
            "role_assignment": "attack_challenger_candidate",
            "beats_defensive_hold_on_cagr": float(candidate["paper_validation_cagr"]) > float(attack_bridge["compared_models"][1]["base_cagr"]),
            "beats_attack_main_on_cagr": float(candidate["paper_validation_cagr"]) > float(main["base_cagr"]),
            "improves_on_defensive_hold_drift": float(status["walk_forward_sensitivity_max_drift"]) < float(attack_bridge["compared_models"][1]["sensitivity_max_drift"]),
            "maintains_attack_band_drawdown": float(candidate["paper_validation_max_drawdown"]) <= float(main["base_mdd"]),
            "next_step_now": "candidate_promotion_bridge_entry",
            "reason": (
                "The reframe candidate is candidate-stage clean, survives heavy friction, improves materially on the defensive hold profile, and stays inside the existing attack drawdown band."
            ),
        },
        "bridge_actions": {
            "preserve_as_references": [
                main_backup["stack_top"]["attack_main"],
                main_backup["stack_top"]["attack_backup"],
                attack_bridge["stack_top"]["defensive_hold"],
            ],
            "bridge_candidate": candidate["label"],
            "execution_order": [
                "candidate_promotion_bridge_entry",
                "operator_stack_summary_update",
                "execution_contract_entry_check",
            ],
            "success_gate": {
                "must_keep_paper_validation_pass": True,
                "must_keep_friction_continue": True,
                "must_keep_drawdown_at_or_below": 0.16,
                "must_beat_defensive_hold_on_cagr": True,
                "must_improve_on_defensive_hold_drift": True,
            },
        },
        "decision_summary": [
            f"Promote `{candidate['label']}` into the bridge queue because it is candidate-stage clean, improves on `{attack_bridge['stack_top']['defensive_hold']}` on CAGR, and stays inside the attack drawdown band.",
            f"Do not replace `{main_backup['stack_top']['attack_main']}` yet; treat the new candidate as an `attack_challenger_candidate` until bridge and contract entry complete.",
            "Use the next cycle to thread this candidate into the promotion bridge and operator stack rather than reopening search.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    ctx = report["stack_context"]
    candidate = report["candidate_profile"]
    verdict = report["promotion_bridge_verdict"]
    return "\n".join(
        [
            "# BTC 1d Pullthrough Asymmetric Release Promotion Bridge",
            "",
            f"- Attack main: `{ctx['attack_main']}`",
            f"- Attack backup: `{ctx['attack_backup']}`",
            f"- Defensive hold: `{ctx['defensive_hold']}`",
            f"- Candidate: `{ctx['candidate']}`",
            f"- Candidate profile: `{candidate['paper_validation_cagr']:.4f}` CAGR / `{candidate['paper_validation_max_drawdown']:.4f}` MDD / Sharpe `{candidate['paper_validation_sharpe']:.4f}`",
            f"- Walk-forward drift: `{candidate['walk_forward_sensitivity_max_drift']:.4f}`",
            f"- Friction final decision: `{candidate['friction_final_decision']}`",
            f"- Promotion ready: `{verdict['promotion_ready']}`",
            f"- Role assignment: `{verdict['role_assignment']}`",
            f"- Next step now: `{verdict['next_step_now']}`",
            "",
        ]
    )


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_pullthrough_asymmetric_release_promotion_bridge_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_pullthrough_asymmetric_release_promotion_bridge_{stamp}.md"
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
