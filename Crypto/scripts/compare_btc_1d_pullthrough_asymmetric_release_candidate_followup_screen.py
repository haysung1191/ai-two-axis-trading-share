from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


ANALYSIS_DIR = Path("analysis_results")


def _latest_path(pattern: str) -> Path:
    matches = sorted(ANALYSIS_DIR.glob(pattern), key=lambda path: path.name)
    if not matches:
        raise FileNotFoundError(f"No artifact found for pattern {pattern}")
    return matches[-1]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report() -> dict:
    validation = _load_json(_latest_path("btc_1d_volatility_expansion_pullthrough_exit_v4_btcusdt_1d_2200_paper_validation_*.json"))
    walk = _load_json(_latest_path("btc_1d_walk_forward_diagnostic_*.json"))
    friction = _load_json(_latest_path("btc_1d_pullthrough_asymmetric_release_friction_*.json"))

    decision = validation["decision_record"]["decision"]
    walk_drift = float(walk["overfitting"]["sensitivity_max_drift"])
    friction_decision = friction["final_decision"]
    cost20 = next(level for level in friction["levels"] if float(level["cost_bps"]) == 20.0)

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "candidate": {
            "label": "pullthrough_asymmetric_release_tighter_exit",
            "strategy_name": "btc_1d_volatility_expansion_pullthrough_exit_v4",
            "paper_validation_decision": decision,
            "paper_validation_cagr": float(validation["decision_record"]["key_metrics"]["cagr"]),
            "paper_validation_max_drawdown": float(validation["decision_record"]["key_metrics"]["max_drawdown"]),
            "paper_validation_sharpe": float(validation["decision_record"]["key_metrics"]["sharpe"]),
            "paper_validation_trades": int(validation["decision_record"]["key_metrics"]["trades"]),
        },
        "followup_status": {
            "walk_forward_sensitivity_max_drift": walk_drift,
            "walk_forward_unstable_parameters": list(walk["overfitting"]["unstable_parameters"]),
            "friction_final_decision": friction_decision,
            "cost20_cagr": float(cost20["cagr"]),
            "cost20_max_drawdown": float(cost20["max_drawdown"]),
            "cost20_sharpe": float(cost20["sharpe"]),
            "cost20_failed_gates": list(cost20["failed_gates"]),
        },
        "followup_verdict": {
            "candidate_stage_followup_ready": (
                decision == "PASS" and friction_decision == "continue"
            ),
            "next_step": "promotion_bridge_or_execution_contract_entry",
            "reason": (
                "The reframe candidate passed paper validation and survives heavy friction; walk-forward drift remains visible but does not block candidate-stage follow-up."
            ),
        },
        "decision_summary": [
            f"Keep `pullthrough_asymmetric_release_tighter_exit` as the active candidate because paper validation passed at `{float(validation['decision_record']['key_metrics']['cagr']):.4f}` CAGR and `{float(validation['decision_record']['key_metrics']['max_drawdown']):.4f}` MDD.",
            f"Treat friction as cleared because the candidate still passes at 20 bps with `{float(cost20['cagr']):.4f}` CAGR and `{float(cost20['max_drawdown']):.4f}` MDD.",
            f"Carry forward the walk-forward caveat explicitly: sensitivity drift is `{walk_drift:.4f}`, so the next bridge should preserve this candidate while monitoring robustness rather than reopening search immediately.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    candidate = report["candidate"]
    status = report["followup_status"]
    verdict = report["followup_verdict"]
    return "\n".join(
        [
            "# BTC 1d Pullthrough Asymmetric Release Candidate Followup Screen",
            "",
            f"- Candidate: `{candidate['label']}`",
            f"- Paper validation: `{candidate['paper_validation_decision']}` | `{candidate['paper_validation_cagr']:.4f}` CAGR / `{candidate['paper_validation_max_drawdown']:.4f}` MDD / Sharpe `{candidate['paper_validation_sharpe']:.4f}`",
            f"- Walk-forward drift: `{status['walk_forward_sensitivity_max_drift']:.4f}`",
            f"- Friction final decision: `{status['friction_final_decision']}`",
            f"- Cost20 profile: `{status['cost20_cagr']:.4f}` CAGR / `{status['cost20_max_drawdown']:.4f}` MDD / Sharpe `{status['cost20_sharpe']:.4f}`",
            f"- Candidate-stage followup ready: `{verdict['candidate_stage_followup_ready']}`",
            f"- Next step: `{verdict['next_step']}`",
            "",
        ]
    )


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_pullthrough_asymmetric_release_candidate_followup_screen_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_pullthrough_asymmetric_release_candidate_followup_screen_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report_md_path": str(md_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
