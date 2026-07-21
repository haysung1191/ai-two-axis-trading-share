from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _practical_main() -> dict:
    gate_path = ANALYSIS_DIR / "btc_1d_practical_promotion_gate_latest.json"
    scorecard_path = ANALYSIS_DIR / "btc_1d_practical_scorecard_latest.json"

    gate = _load_json(gate_path)
    scorecard = _load_json(scorecard_path)

    summary = scorecard["summary"]
    stats = scorecard["statistical_defense"]
    regime = scorecard["regime"]["regimes"]
    concentration = scorecard["concentration"]["trade_concentration"]

    return {
        "label": "lower_atr_window_tighter_stop",
        "track": "practical_main",
        "status": gate["decision"],
        "status_label": gate["status_label"],
        "base_cagr": float(summary["carry_metrics"]["cagr"]),
        "base_mdd": float(summary["carry_metrics"]["max_drawdown"]),
        "base_sharpe": float(summary["carry_metrics"]["sharpe"]),
        "oos_cagr": None,
        "oos_mdd": None,
        "oos_sharpe": None,
        "sensitivity_max_drift": None,
        "unstable_parameters": [],
        "cost20_cagr": float(summary["friction_20bps_metrics"]["cagr"]),
        "cost20_mdd": float(summary["friction_20bps_metrics"]["max_drawdown"]),
        "cost20_sharpe": float(summary["friction_20bps_metrics"]["sharpe"]),
        "psr": float(stats["psr"]),
        "dsr": float(stats["dsr"]),
        "range_regime_sharpe": float(regime["range"]["sharpe"]),
        "top_5_trade_share": float(concentration["top_5_trade_share"]),
        "caveats": list(gate["caveats"]),
        "substitute_read": "current_practical_anchor",
    }


def _pullthrough_hold() -> dict:
    walk_path = ANALYSIS_DIR / "btc_1d_walk_forward_diagnostic_20260415T212625Z.json"
    friction_path = ANALYSIS_DIR / "btc_1d_volatility_expansion_pullthrough_shorthold_friction_20260415T212654Z.json"
    paper_path = ANALYSIS_DIR / "btc_1d_volatility_expansion_pullthrough_exit_v3_btcusdt_1d_2200_paper_validation_20260415T212545Z.json"

    walk = _load_json(walk_path)
    friction = _load_json(friction_path)
    paper = _load_json(paper_path)

    base = walk["base_metrics"]
    overfitting = walk["overfitting"]
    oos = overfitting["oos_metrics"]
    top_cost = next(level for level in friction["levels"] if float(level["cost_bps"]) == 20.0)

    return {
        "label": "volatility_expansion_pullthrough_shorter_hold",
        "track": "defensive_practical_adjacent",
        "status": "research_hold",
        "status_label": "candidate_stage_hold",
        "base_cagr": float(base["cagr"]),
        "base_mdd": float(base["max_drawdown"]),
        "base_sharpe": float(base["sharpe"]),
        "oos_cagr": float(oos["cagr"]),
        "oos_mdd": float(oos["max_drawdown"]),
        "oos_sharpe": float(oos["sharpe"]),
        "sensitivity_max_drift": float(overfitting["sensitivity_max_drift"]),
        "unstable_parameters": list(overfitting["unstable_parameters"]),
        "cost20_cagr": float(top_cost["cagr"]),
        "cost20_mdd": float(top_cost["max_drawdown"]),
        "cost20_sharpe": float(top_cost["sharpe"]),
        "psr": None,
        "dsr": None,
        "range_regime_sharpe": None,
        "top_5_trade_share": None,
        "caveats": list(paper["decision_record"]["failed_gates"]),
        "substitute_read": "not_practical_substitute",
    }


def build_report() -> dict:
    practical = _practical_main()
    hold = _pullthrough_hold()

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "compared_models": [practical, hold],
        "practical_anchor": practical["label"],
        "nearest_research_hold": hold["label"],
        "decision_summary": [
            "Pullthrough shorter-hold is the nearest defensive research hold, but it is not a practical substitute for the current BTC-only practical anchor.",
            "The practical main still dominates on promotion readiness because it already has explicit practical gate evidence, while pullthrough remains blocked at candidate-stage sensitivity.",
        ],
        "overlap_verdict": {
            "is_practical_substitute": False,
            "preferred_practical_model": practical["label"],
            "preferred_defensive_research_hold": hold["label"],
            "reason": "pullthrough shorter-hold has respectable drawdown control, but weaker OOS and no practical promotion path compared with the current practical main.",
        },
    }
    return report


def _render_markdown(report: dict) -> str:
    lines = [
        "# BTC 1d Practical Overlap Screen",
        "",
        f"- Practical anchor: `{report['practical_anchor']}`",
        f"- Nearest research hold: `{report['nearest_research_hold']}`",
        f"- Practical substitute: `{report['overlap_verdict']['is_practical_substitute']}`",
        f"- Reason: {report['overlap_verdict']['reason']}",
        "",
    ]
    for row in report["compared_models"]:
        lines.extend(
            [
                f"## {row['label']}",
                f"- track: `{row['track']}`",
                f"- status_label: `{row['status_label']}`",
                f"- base: `{row['base_cagr']:.4f}` CAGR / `{row['base_mdd']:.4f}` MDD / Sharpe `{row['base_sharpe']:.4f}`",
                f"- OOS Sharpe: `{row['oos_sharpe'] if row['oos_sharpe'] is not None else 'n/a'}`",
                f"- sensitivity drift: `{row['sensitivity_max_drift'] if row['sensitivity_max_drift'] is not None else 'n/a'}`",
                f"- cost20 Sharpe: `{row['cost20_sharpe']:.4f}`",
                f"- substitute_read: `{row['substitute_read']}`",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_practical_overlap_screen_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_practical_overlap_screen_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report_md_path": str(md_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
