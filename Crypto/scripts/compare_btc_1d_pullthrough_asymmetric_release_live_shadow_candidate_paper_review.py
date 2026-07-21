from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.compare_btc_1d_pullthrough_asymmetric_release_live_governed_shadow_entry import (
    build_report as build_live_governed_shadow_entry_report,
)


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build_report(analysis_dir: Path = ANALYSIS_DIR) -> dict:
    governed_shadow_entry = build_live_governed_shadow_entry_report(analysis_dir=analysis_dir)
    operating_index = _load_json(analysis_dir / "btc_1d_operating_index_latest.json")
    operating_brief = _load_json(analysis_dir / "btc_1d_operating_brief_latest.json")
    dashboard = _load_json(analysis_dir / "btc_1d_operator_dashboard_latest.json")

    context = dict(governed_shadow_entry.get("stack_context", {}) or {})
    candidate = dict(governed_shadow_entry.get("candidate_profile", {}) or {})
    entry_requirements = dict(
        governed_shadow_entry.get("challenger_live_governed_shadow_entry_requirements", {})
        or {}
    )
    entry_verdict = dict(
        governed_shadow_entry.get("challenger_live_governed_shadow_entry_verdict", {}) or {}
    )
    dashboard_summary = dict(dashboard.get("dashboard_summary", {}) or {})

    paper_review_requirements = {
        "challenger_live_governed_shadow_entry_ready": bool(
            entry_verdict.get("challenger_live_governed_shadow_entry_ready", False)
        ),
        "operator_verdict_shadow_monitoring_ready": (
            str(operating_index.get("operator_verdict", "")) == "shadow_monitoring_ready"
        ),
        "operating_index_live_governed_shadow_entry_ready": bool(
            operating_index.get("attack_challenger_live_governed_shadow_entry_ready", False)
        ),
        "operating_brief_live_governed_shadow_entry_ready": bool(
            operating_brief.get("attack_challenger_live_governed_shadow_entry_ready", False)
        ),
        "dashboard_live_governed_shadow_entry_ready": bool(
            dashboard_summary.get("attack_challenger_live_governed_shadow_entry_ready", False)
        ),
        "queue_lane_mirrored": (
            bool(str(operating_index.get("attack_challenger_live_governed_shadow_entry_lane", "")))
            and str(operating_index.get("attack_challenger_live_governed_shadow_entry_lane", ""))
            == str(operating_brief.get("attack_challenger_live_governed_shadow_entry_lane", ""))
            == str(
                dashboard_summary.get("attack_challenger_live_governed_shadow_entry_lane", "")
            )
        ),
        "promotion_chain_still_green": bool(
            entry_requirements.get("promotion_chain_still_green", False)
        ),
    }
    paper_review_ready = all(paper_review_requirements.values())
    paper_review_lane = (
        "challenger_live_shadow_candidate_paper_queue"
        if paper_review_ready
        else "challenger_live_shadow_candidate_paper_repair_hold"
    )
    next_step_now = (
        "challenger_live_shadow_candidate_governance_lock"
        if paper_review_ready
        else "repair_challenger_live_shadow_candidate_paper_review"
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
            "paper_validation_sharpe": float(candidate.get("paper_validation_sharpe", 0.0)),
            "paper_validation_trades": int(candidate.get("paper_validation_trades", 0)),
            "walk_forward_sensitivity_max_drift": float(
                candidate.get("walk_forward_sensitivity_max_drift", 0.0)
            ),
            "friction_final_decision": str(candidate.get("friction_final_decision", "")),
        },
        "challenger_live_shadow_candidate_paper_review_requirements": paper_review_requirements,
        "challenger_live_shadow_candidate_paper_review_verdict": {
            "challenger_live_shadow_candidate_paper_review_ready": paper_review_ready,
            "challenger_live_shadow_candidate_paper_review_lane": paper_review_lane,
            "next_step_now": next_step_now,
            "reason": (
                "Governed shadow entry is green and every operator-facing mirror agrees, so the challenger can enter shadow candidate paper review."
                if paper_review_ready
                else "The challenger cleared governed shadow entry, but the shadow candidate paper review mirrors are not fully aligned yet."
            ),
        },
        "decision_summary": [
            f"Treat `{context.get('attack_challenger_candidate', candidate.get('label', ''))}` as the active challenger shadow candidate paper-review target.",
            (
                "Advance to `challenger_live_shadow_candidate_governance_lock` because governed shadow entry and operator-facing mirrors are all green."
                if paper_review_ready
                else "Do not advance into shadow candidate paper review until all paper-review requirements are green."
            ),
            f"Keep `{context.get('attack_main', '')}` and `{context.get('attack_backup', '')}` as references while the challenger completes shadow candidate paper review.",
        ],
    }


def _render_markdown(report: dict) -> str:
    context = report["stack_context"]
    candidate = report["candidate_profile"]
    requirements = report["challenger_live_shadow_candidate_paper_review_requirements"]
    verdict = report["challenger_live_shadow_candidate_paper_review_verdict"]
    return "\n".join(
        [
            "# BTC 1d Pullthrough Asymmetric Release Challenger Live Shadow Candidate Paper Review",
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
            f"- Challenger live shadow candidate paper review ready: `{verdict['challenger_live_shadow_candidate_paper_review_ready']}`",
            f"- Queue lane: `{verdict['challenger_live_shadow_candidate_paper_review_lane']}`",
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
        / f"btc_1d_pullthrough_asymmetric_release_live_shadow_candidate_paper_review_{stamp}.json"
    )
    md_path = (
        ANALYSIS_DIR
        / f"btc_1d_pullthrough_asymmetric_release_live_shadow_candidate_paper_review_{stamp}.md"
    )
    latest_json = (
        ANALYSIS_DIR
        / "btc_1d_pullthrough_asymmetric_release_live_shadow_candidate_paper_review_latest.json"
    )
    latest_md = (
        ANALYSIS_DIR
        / "btc_1d_pullthrough_asymmetric_release_live_shadow_candidate_paper_review_md_latest.md"
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
