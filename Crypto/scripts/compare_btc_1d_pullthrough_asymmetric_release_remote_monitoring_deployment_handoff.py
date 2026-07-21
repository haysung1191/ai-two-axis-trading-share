from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.btc_1d_handoff_constants import (
    ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP,
    ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_REPAIR_LANE,
    ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_REPAIR_NEXT_STEP,
    ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE,
)

ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    governance_entry = _load_json(
        analysis_dir
        / "btc_1d_pullthrough_asymmetric_release_live_shadow_locked_release_governance_entry_latest.json"
    )
    operating_index = _load_json(analysis_dir / "btc_1d_operating_index_latest.json")
    operating_brief = _load_json(analysis_dir / "btc_1d_operating_brief_latest.json")
    dashboard = _load_json(analysis_dir / "btc_1d_operator_dashboard_latest.json")

    context = dict(governance_entry.get("stack_context", {}) or {})
    candidate = dict(governance_entry.get("candidate_profile", {}) or {})
    prior_requirements = dict(
        governance_entry.get(
            "challenger_live_shadow_locked_release_governance_entry_requirements", {}
        )
        or {}
    )
    prior_verdict = dict(
        governance_entry.get(
            "challenger_live_shadow_locked_release_governance_entry_verdict", {}
        )
        or {}
    )
    dashboard_summary = dict(dashboard.get("dashboard_summary", {}) or {})
    development = dict(dashboard.get("development", {}) or {})
    dashboard_next_actions = list(development.get("next_actions", []) or [])

    handoff_requirements = {
        "challenger_live_shadow_locked_release_governance_entry_ready": bool(
            prior_verdict.get(
                "challenger_live_shadow_locked_release_governance_entry_ready", False
            )
        ),
        "operator_verdict_shadow_monitoring_ready": (
            str(operating_index.get("operator_verdict", "")) == "shadow_monitoring_ready"
        ),
        "dashboard_operator_verdict_shadow_monitoring_ready": (
            str(dashboard_summary.get("operator_verdict", ""))
            == "shadow_monitoring_ready"
        ),
        "dashboard_ready": bool(dashboard_summary.get("dashboard_ready", False)),
        "operating_index_governance_entry_ready": bool(
            operating_index.get(
                "attack_challenger_live_shadow_locked_release_governance_entry_ready",
                False,
            )
        ),
        "operating_brief_governance_entry_ready": bool(
            operating_brief.get(
                "attack_challenger_live_shadow_locked_release_governance_entry_ready",
                False,
            )
        ),
        "dashboard_governance_entry_ready": bool(
            dashboard_summary.get(
                "attack_challenger_live_shadow_locked_release_governance_entry_ready",
                False,
            )
        ),
        "governance_entry_lane_mirrored": (
            bool(
                str(
                    prior_verdict.get(
                        "challenger_live_shadow_locked_release_governance_entry_lane",
                        "",
                    )
                )
            )
            and str(
                prior_verdict.get(
                    "challenger_live_shadow_locked_release_governance_entry_lane",
                    "",
                )
            )
            == str(
                operating_index.get(
                    "attack_challenger_live_shadow_locked_release_governance_entry_lane",
                    "",
                )
            )
            == str(
                operating_brief.get(
                    "attack_challenger_live_shadow_locked_release_governance_entry_lane",
                    "",
                )
            )
            == str(
                dashboard_summary.get(
                    "attack_challenger_live_shadow_locked_release_governance_entry_lane",
                    "",
                )
            )
        ),
        "dashboard_next_actions_include_handoff": (
            "remote monitoring and deployment handoff"
            in dashboard_next_actions
            or ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP
            in dashboard_next_actions
        ),
        "promotion_chain_still_green": bool(
            prior_requirements.get("promotion_chain_still_green", False)
        ),
    }
    handoff_ready = all(handoff_requirements.values())
    handoff_lane = (
        ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_READY_LANE
        if handoff_ready
        else ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_REPAIR_LANE
    )
    next_step_now = (
        ATTACK_CHALLENGER_DEPLOYMENT_MONITORING_NEXT_STEP
        if handoff_ready
        else ATTACK_CHALLENGER_REMOTE_MONITORING_DEPLOYMENT_HANDOFF_REPAIR_NEXT_STEP
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
        "remote_monitoring_deployment_handoff_requirements": handoff_requirements,
        "remote_monitoring_deployment_handoff_verdict": {
            "remote_monitoring_deployment_handoff_ready": handoff_ready,
            "remote_monitoring_deployment_handoff_lane": handoff_lane,
            "next_step_now": next_step_now,
            "reason": (
                "Locked-release governance entry is green across all operator-facing mirrors, so the challenger can hand off into deployment monitoring."
                if handoff_ready
                else "Governance-entry state is not yet mirrored cleanly enough to complete the remote-monitoring deployment handoff."
            ),
        },
        "decision_summary": [
            f"Treat `{context.get('attack_challenger_candidate', candidate.get('label', ''))}` as the active deployment-monitoring challenger.",
            (
                "Advance to `deployment monitoring active` because governance entry, dashboard readiness, and operator-facing mirrors are all green."
                if handoff_ready
                else "Do not declare deployment monitoring active until the handoff mirrors are fully aligned."
            ),
            f"Keep `{context.get('attack_main', '')}` and `{context.get('attack_backup', '')}` as reference candidates while the challenger is monitored."
        ],
    }


def _render_markdown(report: dict) -> str:
    context = report["stack_context"]
    candidate = report["candidate_profile"]
    requirements = report["remote_monitoring_deployment_handoff_requirements"]
    verdict = report["remote_monitoring_deployment_handoff_verdict"]
    return "\n".join(
        [
            "# BTC 1d Pullthrough Asymmetric Release Remote Monitoring Deployment Handoff",
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
            f"- Remote monitoring deployment handoff ready: `{verdict['remote_monitoring_deployment_handoff_ready']}`",
            f"- Handoff lane: `{verdict['remote_monitoring_deployment_handoff_lane']}`",
            f"- Next step now: `{verdict['next_step_now']}`",
            "",
            "## Requirements",
            *(f"- {key}: `{value}`" for key, value in requirements.items()),
            "",
        ]
    )


def main() -> int:
    report = build_report()
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = (
        ANALYSIS_DIR
        / f"btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_{stamp}.json"
    )
    md_path = (
        ANALYSIS_DIR
        / f"btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_{stamp}.md"
    )
    latest_json = (
        ANALYSIS_DIR
        / "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_latest.json"
    )
    latest_md = (
        ANALYSIS_DIR
        / "btc_1d_pullthrough_asymmetric_release_remote_monitoring_deployment_handoff_md_latest.md"
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
