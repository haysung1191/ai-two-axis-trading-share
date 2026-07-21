from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_pullthrough_asymmetric_release_operator_stack_handoff import (
    build_report as build_operator_stack_handoff_report,
)


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    handoff = build_operator_stack_handoff_report(analysis_dir=analysis_dir)
    operating_index = _load_json(analysis_dir / "btc_1d_operating_index_latest.json")
    operating_brief = _load_json(analysis_dir / "btc_1d_operating_brief_latest.json")
    dashboard = _load_json(analysis_dir / "btc_1d_operator_dashboard_latest.json")

    context = dict(handoff.get("stack_context", {}) or {})
    candidate = dict(handoff.get("candidate_profile", {}) or {})
    handoff_requirements = dict(
        handoff.get("operator_stack_handoff_requirements", {}) or {}
    )
    handoff_verdict = dict(handoff.get("operator_stack_handoff_verdict", {}) or {})
    dashboard_summary = dict(dashboard.get("dashboard_summary", {}) or {})

    entry_requirements = {
        "operator_stack_handoff_ready": bool(
            handoff_verdict.get("operator_stack_handoff_ready", False)
        ),
        "operator_verdict_shadow_monitoring_ready": (
            str(operating_index.get("operator_verdict", "")) == "shadow_monitoring_ready"
        ),
        "operating_index_handoff_ready": bool(
            operating_index.get("attack_challenger_operator_stack_handoff_ready", False)
        ),
        "operating_brief_handoff_ready": bool(
            operating_brief.get("attack_challenger_operator_stack_handoff_ready", False)
        ),
        "dashboard_handoff_ready": bool(
            dashboard_summary.get("attack_challenger_operator_stack_handoff_ready", False)
        ),
        "queue_lane_mirrored": (
            str(operating_index.get("attack_challenger_operator_stack_handoff_lane", ""))
            == str(handoff_verdict.get("operator_stack_handoff_lane", ""))
            == str(operating_brief.get("attack_challenger_operator_stack_handoff_lane", ""))
            == str(
                dashboard_summary.get("attack_challenger_operator_stack_handoff_lane", "")
            )
        ),
        "promotion_chain_still_green": bool(
            handoff_requirements.get("promotion_chain_still_green", False)
        ),
    }
    entry_ready = all(entry_requirements.values())
    queue_lane = (
        "operator_runbook_candidate_queue"
        if entry_ready
        else "operator_runbook_candidate_repair_hold"
    )
    next_step_now = (
        "operator_runbook_execution_entry"
        if entry_ready
        else "repair_operator_runbook_candidate_entry_requirements"
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
        "operator_runbook_candidate_entry_requirements": entry_requirements,
        "operator_runbook_candidate_entry_verdict": {
            "operator_runbook_candidate_entry_ready": entry_ready,
            "operator_runbook_candidate_entry_lane": queue_lane,
            "next_step_now": next_step_now,
            "reason": (
                "Operator-stack handoff is green and every operator-facing mirror is aligned, so the challenger can enter the operator runbook candidate queue."
                if entry_ready
                else "The challenger cleared operator-stack handoff, but the runbook-entry mirrors are not fully aligned yet."
            ),
        },
        "decision_summary": [
            f"Treat `{context.get('attack_challenger_candidate', candidate.get('label', ''))}` as the active operator runbook entry candidate.",
            (
                "Advance to `operator_runbook_execution_entry` because handoff and operator-facing mirrors are all green."
                if entry_ready
                else "Do not enter the operator runbook candidate queue until all runbook-entry requirements are green."
            ),
            f"Keep `{context.get('attack_main', '')}` and `{context.get('attack_backup', '')}` as references while the challenger completes operator runbook entry.",
        ],
    }


def _render_markdown(report: dict) -> str:
    context = report["stack_context"]
    candidate = report["candidate_profile"]
    requirements = report["operator_runbook_candidate_entry_requirements"]
    verdict = report["operator_runbook_candidate_entry_verdict"]
    return "\n".join(
        [
            "# BTC 1d Pullthrough Asymmetric Release Operator Runbook Candidate Entry",
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
            f"- Operator runbook candidate entry ready: `{verdict['operator_runbook_candidate_entry_ready']}`",
            f"- Queue lane: `{verdict['operator_runbook_candidate_entry_lane']}`",
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
        / f"btc_1d_pullthrough_asymmetric_release_operator_runbook_candidate_entry_{stamp}.json"
    )
    md_path = (
        ANALYSIS_DIR
        / f"btc_1d_pullthrough_asymmetric_release_operator_runbook_candidate_entry_{stamp}.md"
    )
    latest_json = (
        ANALYSIS_DIR
        / "btc_1d_pullthrough_asymmetric_release_operator_runbook_candidate_entry_latest.json"
    )
    latest_md = (
        ANALYSIS_DIR
        / "btc_1d_pullthrough_asymmetric_release_operator_runbook_candidate_entry_md_latest.md"
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
