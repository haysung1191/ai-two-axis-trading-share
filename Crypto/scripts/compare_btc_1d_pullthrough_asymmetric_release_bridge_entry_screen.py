from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_pullthrough_asymmetric_release_promotion_bridge import (
    build_report as build_promotion_bridge_report,
)


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    promotion_bridge = build_promotion_bridge_report()
    operating_index = _load_json(analysis_dir / "btc_1d_operating_index_latest.json")
    latest_summary = _load_json(analysis_dir / "btc_1d_latest_summary_latest.json")

    verdict = promotion_bridge["promotion_bridge_verdict"]
    candidate = promotion_bridge["candidate_profile"]
    context = promotion_bridge["stack_context"]

    bridge_entry_requirements = {
        "promotion_ready": bool(verdict["promotion_ready"]),
        "role_is_attack_challenger_candidate": (
            str(verdict["role_assignment"]) == "attack_challenger_candidate"
        ),
        "beats_defensive_hold_on_cagr": bool(verdict["beats_defensive_hold_on_cagr"]),
        "improves_on_defensive_hold_drift": bool(
            verdict["improves_on_defensive_hold_drift"]
        ),
        "maintains_attack_band_drawdown": bool(
            verdict["maintains_attack_band_drawdown"]
        ),
        "contract_health_aligned": bool(
            operating_index.get("contract_health_aligned", False)
        ),
        "execution_contract_aligned": bool(
            operating_index.get("execution_contract_aligned", False)
        ),
        "paper_execution_contract_aligned": bool(
            operating_index.get("paper_execution_contract_aligned", False)
        ),
        "paper_ledger_consistent": bool(
            operating_index.get("paper_ledger_consistent", False)
        ),
    }
    bridge_entry_ready = all(bridge_entry_requirements.values())

    next_step_now = (
        "execution_contract_entry_check"
        if bridge_entry_ready
        else "repair_operator_stack_before_bridge_entry"
    )
    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "stack_context": {
            "attack_main": context["attack_main"],
            "attack_backup": context["attack_backup"],
            "defensive_hold": context["defensive_hold"],
            "attack_challenger_candidate": context["candidate"],
            "operator_verdict": operating_index.get("operator_verdict", ""),
            "shadow_decision": latest_summary.get("shadow_decision", ""),
        },
        "candidate_profile": {
            "label": candidate["label"],
            "paper_validation_cagr": float(candidate["paper_validation_cagr"]),
            "paper_validation_max_drawdown": float(
                candidate["paper_validation_max_drawdown"]
            ),
            "paper_validation_sharpe": float(candidate["paper_validation_sharpe"]),
            "paper_validation_trades": int(candidate["paper_validation_trades"]),
            "walk_forward_sensitivity_max_drift": float(
                candidate["walk_forward_sensitivity_max_drift"]
            ),
            "friction_final_decision": str(candidate["friction_final_decision"]),
        },
        "bridge_entry_requirements": bridge_entry_requirements,
        "bridge_entry_verdict": {
            "bridge_entry_ready": bridge_entry_ready,
            "bridge_queue_lane": (
                "attack_challenger_queue" if bridge_entry_ready else "bridge_repair_hold"
            ),
            "execution_contract_entry_check_ready": bridge_entry_ready,
            "next_step_now": next_step_now,
            "reason": (
                "The challenger is promotion-ready and the operator stack is aligned, so it can enter the attack challenger bridge queue."
                if bridge_entry_ready
                else "The challenger remains bridge-worthy, but the operator stack or bridge requirements are not fully aligned yet."
            ),
        },
        "decision_summary": [
            f"Treat `{context['candidate']}` as the active attack challenger bridge entry candidate.",
            (
                "Advance to `execution_contract_entry_check` because promotion and operator-stack gates are simultaneously green."
                if bridge_entry_ready
                else "Do not enter execution-contract checks until the bridge entry requirements are all green."
            ),
            f"Keep `{context['attack_main']}` and `{context['attack_backup']}` as references while the challenger enters the queue.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    context = report["stack_context"]
    candidate = report["candidate_profile"]
    verdict = report["bridge_entry_verdict"]
    requirements = report["bridge_entry_requirements"]
    return "\n".join(
        [
            "# BTC 1d Pullthrough Asymmetric Release Bridge Entry Screen",
            "",
            f"- Attack main: `{context['attack_main']}`",
            f"- Attack backup: `{context['attack_backup']}`",
            f"- Defensive hold: `{context['defensive_hold']}`",
            f"- Attack challenger: `{context['attack_challenger_candidate']}`",
            f"- Operator verdict: `{context['operator_verdict']}`",
            f"- Shadow decision: `{context['shadow_decision']}`",
            f"- Challenger profile: `{candidate['paper_validation_cagr']:.4f}` CAGR / `{candidate['paper_validation_max_drawdown']:.4f}` MDD / Sharpe `{candidate['paper_validation_sharpe']:.4f}`",
            f"- Walk-forward drift: `{candidate['walk_forward_sensitivity_max_drift']:.4f}`",
            f"- Friction final decision: `{candidate['friction_final_decision']}`",
            f"- Bridge entry ready: `{verdict['bridge_entry_ready']}`",
            f"- Bridge queue lane: `{verdict['bridge_queue_lane']}`",
            f"- Next step now: `{verdict['next_step_now']}`",
            "",
            "## Requirements",
            *(f"- {key}: `{value}`" for key, value in requirements.items()),
            "",
        ]
    )


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_pullthrough_asymmetric_release_bridge_entry_screen_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_pullthrough_asymmetric_release_bridge_entry_screen_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    latest_json = ANALYSIS_DIR / "btc_1d_pullthrough_asymmetric_release_bridge_entry_screen_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_pullthrough_asymmetric_release_bridge_entry_screen_md_latest.md"
    latest_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    latest_md.write_text(_render_markdown(report), encoding="utf-8")
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
