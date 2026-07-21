from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_pullthrough_asymmetric_release_execution_contract_entry_check import (
    build_report as build_execution_contract_entry_report,
)


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    entry_check = build_execution_contract_entry_report(analysis_dir=analysis_dir)
    operating_index = _load_json(analysis_dir / "btc_1d_operating_index_latest.json")
    operating_brief = _load_json(analysis_dir / "btc_1d_operating_brief_latest.json")
    dashboard = _load_json(analysis_dir / "btc_1d_operator_dashboard_latest.json")

    context = dict(entry_check.get("stack_context", {}) or {})
    candidate = dict(entry_check.get("candidate_profile", {}) or {})
    entry_requirements = dict(
        entry_check.get("execution_contract_entry_requirements", {}) or {}
    )
    entry_verdict = dict(
        entry_check.get("execution_contract_entry_verdict", {}) or {}
    )
    dashboard_summary = dict(dashboard.get("dashboard_summary", {}) or {})

    handoff_requirements = {
        "execution_contract_entry_ready": bool(
            entry_verdict.get("execution_contract_entry_ready", False)
        ),
        "operator_verdict_shadow_monitoring_ready": (
            str(operating_index.get("operator_verdict", "")) == "shadow_monitoring_ready"
        ),
        "operating_index_contract_entry_ready": bool(
            operating_index.get("attack_challenger_execution_contract_entry_ready", False)
        ),
        "operating_brief_contract_entry_ready": bool(
            operating_brief.get("attack_challenger_execution_contract_entry_ready", False)
        ),
        "dashboard_contract_entry_ready": bool(
            dashboard_summary.get("attack_challenger_execution_contract_entry_ready", False)
        ),
        "queue_lane_mirrored": (
            str(operating_index.get("attack_challenger_execution_contract_queue_lane", ""))
            == str(entry_verdict.get("execution_contract_queue_lane", ""))
            == str(operating_brief.get("attack_challenger_execution_contract_queue_lane", ""))
            == str(dashboard_summary.get("attack_challenger_execution_contract_queue_lane", ""))
        ),
        "promotion_chain_still_green": all(entry_requirements.values()),
    }
    handoff_ready = all(handoff_requirements.values())
    handoff_lane = (
        "operator_stack_handoff_queue" if handoff_ready else "operator_stack_repair_hold"
    )
    next_step_now = (
        "operator_runbook_candidate_entry"
        if handoff_ready
        else "repair_operator_stack_handoff_requirements"
    )

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "stack_context": {
            "attack_main": context.get("attack_main", ""),
            "attack_backup": context.get("attack_backup", ""),
            "defensive_hold": context.get("defensive_hold", ""),
            "attack_challenger_candidate": context.get(
                "attack_challenger_candidate", candidate.get("label", "")
            ),
            "operator_verdict": operating_index.get("operator_verdict", ""),
            "shadow_decision": context.get("shadow_decision", ""),
        },
        "candidate_profile": {
            "label": candidate.get("label", ""),
            "paper_validation_cagr": float(candidate.get("paper_validation_cagr", 0.0)),
            "paper_validation_max_drawdown": float(
                candidate.get("paper_validation_max_drawdown", 0.0)
            ),
            "paper_validation_sharpe": float(
                candidate.get("paper_validation_sharpe", 0.0)
            ),
            "paper_validation_trades": int(candidate.get("paper_validation_trades", 0)),
            "walk_forward_sensitivity_max_drift": float(
                candidate.get("walk_forward_sensitivity_max_drift", 0.0)
            ),
            "friction_final_decision": str(candidate.get("friction_final_decision", "")),
        },
        "operator_stack_handoff_requirements": handoff_requirements,
        "operator_stack_handoff_verdict": {
            "operator_stack_handoff_ready": handoff_ready,
            "operator_stack_handoff_lane": handoff_lane,
            "next_step_now": next_step_now,
            "reason": (
                "Execution-contract entry is green and the operator-facing stack mirrors that state consistently, so the challenger can enter the operator runbook."
                if handoff_ready
                else "The challenger cleared execution-contract entry, but the operator-facing handoff mirrors are not fully aligned yet."
            ),
        },
        "decision_summary": [
            f"Treat `{context.get('attack_challenger_candidate', candidate.get('label', ''))}` as the active operator-stack handoff candidate.",
            (
                "Advance to `operator_runbook_candidate_entry` because execution-contract entry and operator-facing mirrors are all green."
                if handoff_ready
                else "Do not enter the operator runbook until operator-stack handoff requirements are all green."
            ),
            f"Keep `{context.get('attack_main', '')}` and `{context.get('attack_backup', '')}` as references while the challenger completes operator handoff.",
        ],
    }


def _render_markdown(report: dict) -> str:
    context = report["stack_context"]
    candidate = report["candidate_profile"]
    requirements = report["operator_stack_handoff_requirements"]
    verdict = report["operator_stack_handoff_verdict"]
    return "\n".join(
        [
            "# BTC 1d Pullthrough Asymmetric Release Operator Stack Handoff",
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
            f"- Operator stack handoff ready: `{verdict['operator_stack_handoff_ready']}`",
            f"- Handoff lane: `{verdict['operator_stack_handoff_lane']}`",
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
    json_path = (
        ANALYSIS_DIR
        / f"btc_1d_pullthrough_asymmetric_release_operator_stack_handoff_{stamp}.json"
    )
    md_path = (
        ANALYSIS_DIR
        / f"btc_1d_pullthrough_asymmetric_release_operator_stack_handoff_{stamp}.md"
    )
    latest_json = (
        ANALYSIS_DIR
        / "btc_1d_pullthrough_asymmetric_release_operator_stack_handoff_latest.json"
    )
    latest_md = (
        ANALYSIS_DIR
        / "btc_1d_pullthrough_asymmetric_release_operator_stack_handoff_md_latest.md"
    )
    json_payload = json.dumps(report, indent=2)
    md_payload = _render_markdown(report)
    json_path.write_text(json_payload, encoding="utf-8")
    md_path.write_text(md_payload, encoding="utf-8")
    latest_json.write_text(json_payload, encoding="utf-8")
    latest_md.write_text(md_payload, encoding="utf-8")
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
