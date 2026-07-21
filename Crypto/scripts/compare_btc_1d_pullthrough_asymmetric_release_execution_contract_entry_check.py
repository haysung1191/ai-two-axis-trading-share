from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_pullthrough_asymmetric_release_bridge_entry_screen import (
    build_report as build_bridge_entry_report,
)


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    bridge_entry = build_bridge_entry_report(analysis_dir=analysis_dir)
    operating_index = _load_json(analysis_dir / "btc_1d_operating_index_latest.json")
    execution_contract = _load_json(analysis_dir / "btc_1d_execution_contract_screen_latest.json")
    meta_contract = _load_json(analysis_dir / "btc_1d_meta_contract_screen_latest.json")

    bridge_verdict = dict(bridge_entry.get("bridge_entry_verdict", {}) or {})
    bridge_requirements = dict(bridge_entry.get("bridge_entry_requirements", {}) or {})
    context = dict(bridge_entry.get("stack_context", {}) or {})
    candidate = dict(bridge_entry.get("candidate_profile", {}) or {})
    execution_verdict = dict(
        execution_contract.get("execution_contract_verdict", {}) or {}
    )
    meta_summary = dict(meta_contract.get("meta_contract_summary", {}) or {})
    meta_verdict = dict(meta_contract.get("meta_contract_verdict", {}) or {})

    entry_requirements = {
        "promotion_ready": bool(bridge_requirements.get("promotion_ready", False)),
        "bridge_entry_ready": bool(bridge_verdict.get("bridge_entry_ready", False)),
        "operator_verdict_shadow_monitoring_ready": (
            str(operating_index.get("operator_verdict", "")) == "shadow_monitoring_ready"
        ),
        "execution_contract_aligned": bool(
            execution_verdict.get("execution_contract_aligned", False)
        ),
        "meta_contract_aligned": bool(
            meta_verdict.get("contract_is_fully_aligned", False)
        ),
        "execution_contract_entry_scope_included": bool(
            meta_summary.get("execution_contract_entry_scope_included", False)
        ),
        "execution_contract_wording_lock_included": bool(
            meta_summary.get("execution_contract_wording_lock_included", False)
        ),
        "execution_contract_symmetry_lock_included": bool(
            meta_summary.get("execution_contract_symmetry_lock_included", False)
        ),
    }
    entry_ready = all(entry_requirements.values())
    queue_lane = (
        "challenger_execution_contract_queue"
        if entry_ready
        else "execution_contract_entry_repair_hold"
    )
    next_step_now = (
        "candidate_operator_stack_handoff"
        if entry_ready
        else "repair_execution_contract_entry_requirements"
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
        "execution_contract_entry_requirements": entry_requirements,
        "execution_contract_entry_verdict": {
            "execution_contract_entry_ready": entry_ready,
            "execution_contract_queue_lane": queue_lane,
            "next_step_now": next_step_now,
            "reason": (
                "Bridge entry is green and the execution/meta contract stack is fully aligned, so the challenger can hand off into operator-stack contract entry."
                if entry_ready
                else "The challenger cleared bridge entry, but execution/meta contract entry requirements are not fully aligned yet."
            ),
        },
        "decision_summary": [
            f"Treat `{context.get('attack_challenger_candidate', candidate.get('label', ''))}` as the active execution-contract entry candidate.",
            (
                "Advance to `candidate_operator_stack_handoff` because bridge entry, execution contract, and meta contract gates are all green."
                if entry_ready
                else "Do not hand off the challenger into execution-contract entry until execution/meta contract requirements are all green."
            ),
            f"Keep `{context.get('attack_main', '')}` and `{context.get('attack_backup', '')}` as references while the challenger completes contract entry."
        ],
    }


def _render_markdown(report: dict) -> str:
    context = report["stack_context"]
    candidate = report["candidate_profile"]
    requirements = report["execution_contract_entry_requirements"]
    verdict = report["execution_contract_entry_verdict"]
    return "\n".join(
        [
            "# BTC 1d Pullthrough Asymmetric Release Execution Contract Entry Check",
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
            f"- Execution contract entry ready: `{verdict['execution_contract_entry_ready']}`",
            f"- Queue lane: `{verdict['execution_contract_queue_lane']}`",
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
        / f"btc_1d_pullthrough_asymmetric_release_execution_contract_entry_check_{stamp}.json"
    )
    md_path = (
        ANALYSIS_DIR
        / f"btc_1d_pullthrough_asymmetric_release_execution_contract_entry_check_{stamp}.md"
    )
    latest_json = (
        ANALYSIS_DIR
        / "btc_1d_pullthrough_asymmetric_release_execution_contract_entry_check_latest.json"
    )
    latest_md = (
        ANALYSIS_DIR
        / "btc_1d_pullthrough_asymmetric_release_execution_contract_entry_check_md_latest.md"
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
