from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_from_pullthrough() -> dict:
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
        "category": "defensive_practical_adjacent",
        "candidate_stage_evidence": True,
        "base_cagr": float(base["cagr"]),
        "base_mdd": float(base["max_drawdown"]),
        "base_sharpe": float(base["sharpe"]),
        "trade_count": int(base["trades"]),
        "completed_trades": int(paper["completed_trades"]),
        "oos_cagr": float(oos["cagr"]),
        "oos_mdd": float(oos["max_drawdown"]),
        "oos_sharpe": float(oos["sharpe"]),
        "sensitivity_max_drift": float(overfitting["sensitivity_max_drift"]),
        "unstable_parameters": list(overfitting["unstable_parameters"]),
        "cost20_cagr": float(top_cost["cagr"]),
        "cost20_mdd": float(top_cost["max_drawdown"]),
        "cost20_sharpe": float(top_cost["sharpe"]),
        "paper_failed_gates": list(paper["decision_record"]["failed_gates"]),
        "practical_adjacent_status": "candidate_stage_hold",
        "notes": [
            "Candidate-stage evidence exists.",
            "Drawdown and cost profile remain controlled.",
            "Promotion still blocked by overfitting sensitivity and thin trade count.",
        ],
    }


def _candidate_from_void_refill() -> dict:
    walk_path = ANALYSIS_DIR / "btc_1d_walk_forward_diagnostic_20260415T213821Z.json"
    friction_path = ANALYSIS_DIR / "btc_1d_shallow_liquidity_void_refill_friction_20260415T213854Z.json"
    paper_path = ANALYSIS_DIR / "btc_1d_shallow_liquidity_void_refill_continuation_exit_v1_btcusdt_1d_2200_paper_validation_20260415T213739Z.json"

    walk = _load_json(walk_path)
    friction = _load_json(friction_path)
    paper = _load_json(paper_path)

    base = walk["base_metrics"]
    overfitting = walk["overfitting"]
    oos = overfitting["oos_metrics"]
    top_cost = next(level for level in friction["levels"] if float(level["cost_bps"]) == 20.0)

    return {
        "label": "shallow_liquidity_void_refill_continuation_reference",
        "category": "defensive_practical_adjacent",
        "candidate_stage_evidence": True,
        "base_cagr": float(base["cagr"]),
        "base_mdd": float(base["max_drawdown"]),
        "base_sharpe": float(base["sharpe"]),
        "trade_count": int(base["trades"]),
        "completed_trades": int(paper["completed_trades"]),
        "oos_cagr": float(oos["cagr"]),
        "oos_mdd": float(oos["max_drawdown"]),
        "oos_sharpe": float(oos["sharpe"]),
        "sensitivity_max_drift": float(overfitting["sensitivity_max_drift"]),
        "unstable_parameters": list(overfitting["unstable_parameters"]),
        "cost20_cagr": float(top_cost["cagr"]),
        "cost20_mdd": float(top_cost["max_drawdown"]),
        "cost20_sharpe": float(top_cost["sharpe"]),
        "paper_failed_gates": list(paper["decision_record"]["failed_gates"]),
        "practical_adjacent_status": "candidate_stage_hold",
        "notes": [
            "Candidate-stage evidence now exists.",
            "Base drawdown and cost profile remain controlled.",
            "Still ranks below pullthrough because OOS and drift are weaker, with two unstable parameters.",
        ],
    }


def _rank_key(item: dict) -> tuple:
    candidate_stage_bonus = 1 if item["candidate_stage_evidence"] else 0
    oos_bonus = item["oos_sharpe"] if item["oos_sharpe"] is not None else -99.0
    drift_penalty = -(item["sensitivity_max_drift"] if item["sensitivity_max_drift"] is not None else 99.0)
    return (
        candidate_stage_bonus,
        oos_bonus,
        drift_penalty,
        float(item["base_sharpe"]),
        -float(item["base_mdd"]),
        float(item["base_cagr"]),
    )


def build_report() -> dict:
    candidates = [_candidate_from_pullthrough(), _candidate_from_void_refill()]
    ranked = sorted(candidates, key=_rank_key, reverse=True)

    top = ranked[0]
    comparison = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "candidate_count": len(ranked),
        "ranked_candidates": ranked,
        "top_practical_adjacent_candidate": top["label"],
        "top_status": top["practical_adjacent_status"],
        "decision_summary": [
            "Pullthrough shorter-hold ranks first because it already has candidate-stage evidence with acceptable OOS and controlled drawdown/cost.",
            "Void refill is now also a candidate-stage hold, but it ranks below pullthrough because OOS is weaker and sensitivity drift is higher.",
        ],
    }
    return comparison


def _render_markdown(report: dict) -> str:
    lines = [
        "# BTC 1d Defensive Practical-Adjacent Candidate Screen",
        "",
        f"- Top candidate: `{report['top_practical_adjacent_candidate']}`",
        f"- Top status: `{report['top_status']}`",
        "",
    ]
    for row in report["ranked_candidates"]:
        lines.extend(
            [
                f"## {row['label']}",
                f"- status: `{row['practical_adjacent_status']}`",
                f"- candidate_stage_evidence: `{row['candidate_stage_evidence']}`",
                f"- base: `{row['base_cagr']:.4f}` CAGR / `{row['base_mdd']:.4f}` MDD / Sharpe `{row['base_sharpe']:.4f}`",
                f"- trades: `{row['trade_count']}` / completed `{row['completed_trades']}`",
                f"- OOS Sharpe: `{row['oos_sharpe'] if row['oos_sharpe'] is not None else 'n/a'}`",
                f"- sensitivity drift: `{row['sensitivity_max_drift'] if row['sensitivity_max_drift'] is not None else 'n/a'}`",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_defensive_practical_adjacent_screen_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_defensive_practical_adjacent_screen_{stamp}.md"
    latest_json = ANALYSIS_DIR / "btc_1d_defensive_practical_adjacent_screen_latest.json"
    latest_md = ANALYSIS_DIR / "btc_1d_defensive_practical_adjacent_screen_latest.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    latest_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    latest_md.write_text(_render_markdown(report), encoding="utf-8")
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
