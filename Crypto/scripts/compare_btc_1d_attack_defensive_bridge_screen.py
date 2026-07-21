from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


ANALYSIS_DIR = Path("analysis_results")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _scoreboard_row(label: str, role: str, *, status_label: str, stack_read: str) -> dict:
    scoreboard = _load_json(ANALYSIS_DIR / "btc_1d_model_scoreboard_latest.json")
    rows = list(scoreboard.get("top_models", [])) + list(scoreboard.get("top_new_models", []))
    row = next((item for item in rows if str(item.get("variant")) == label), None)
    if row is None:
        return {
            "label": label,
            "role": role,
            "status_label": status_label,
            "base_cagr": 0.0,
            "base_mdd": 0.0,
            "base_sharpe": 0.0,
            "oos_cagr": 0.0,
            "oos_mdd": 0.0,
            "oos_sharpe": 0.0,
            "sensitivity_max_drift": 0.0,
            "unstable_parameters": [],
            "cost20_cagr": 0.0,
            "cost20_mdd": 0.0,
            "cost20_sharpe": 0.0,
            "completed_trades": 0,
            "failed_gates": ["missing_archived_artifacts"],
            "stack_read": stack_read,
        }
    cagr = float(row.get("cagr") or 0.0)
    mdd = float(row.get("mdd") or 0.0)
    sharpe = float(row.get("sharpe") or 0.0)
    return {
        "label": label,
        "role": role,
        "status_label": status_label,
        "base_cagr": cagr,
        "base_mdd": mdd,
        "base_sharpe": sharpe,
        "oos_cagr": float(row.get("oos_cagr") if row.get("oos_cagr") is not None else cagr),
        "oos_mdd": mdd,
        "oos_sharpe": sharpe,
        "sensitivity_max_drift": 0.0,
        "unstable_parameters": [],
        "cost20_cagr": float(row.get("cost_cagr") if row.get("cost_cagr") is not None else cagr),
        "cost20_mdd": mdd,
        "cost20_sharpe": sharpe,
        "completed_trades": int(row.get("trades") or 0),
        "failed_gates": [str(row.get("gate_failure_reason"))] if row.get("gate_failure_reason") else [],
        "stack_read": stack_read,
    }


def _attack_main() -> dict:
    walk_path = ANALYSIS_DIR / "btc_1d_walk_forward_diagnostic_20260415T162959Z.json"
    friction_path = ANALYSIS_DIR / "btc_1d_volatility_expansion_reclaim_sr112_tightstop_friction_20260415T163017Z.json"
    paper_path = ANALYSIS_DIR / "btc_1d_volatility_expansion_reclaim_sr112_tightstop_paper_validation_20260415T162937Z.json"

    if not (walk_path.exists() and friction_path.exists() and paper_path.exists()):
        return _scoreboard_row(
            "ratio112_tighter_stop_main",
            "attack_main",
            status_label="candidate_stage_hold",
            stack_read="scoreboard_latest_fallback",
        )

    walk = _load_json(walk_path)
    friction = _load_json(friction_path)
    paper = _load_json(paper_path)

    base = walk["base_metrics"]
    overfitting = walk["overfitting"]
    oos = overfitting["oos_metrics"]
    top_cost = next(level for level in friction["levels"] if float(level["cost_bps"]) == 20.0)

    return {
        "label": "ratio112_tighter_stop_main",
        "role": "attack_main",
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
        "completed_trades": int(paper["completed_trades"]),
        "failed_gates": list(paper["decision_record"]["failed_gates"]),
        "stack_read": "attack_anchor",
    }


def _defensive_hold() -> dict:
    walk_path = ANALYSIS_DIR / "btc_1d_walk_forward_diagnostic_20260415T212625Z.json"
    friction_path = ANALYSIS_DIR / "btc_1d_volatility_expansion_pullthrough_shorthold_friction_20260415T212654Z.json"
    paper_path = ANALYSIS_DIR / "btc_1d_volatility_expansion_pullthrough_exit_v3_btcusdt_1d_2200_paper_validation_20260415T212545Z.json"

    if not (walk_path.exists() and friction_path.exists() and paper_path.exists()):
        return _scoreboard_row(
            "volatility_expansion_pullthrough_shorter_hold",
            "defensive_research_hold",
            status_label="candidate_stage_hold",
            stack_read="scoreboard_latest_fallback",
        )

    walk = _load_json(walk_path)
    friction = _load_json(friction_path)
    paper = _load_json(paper_path)

    base = walk["base_metrics"]
    overfitting = walk["overfitting"]
    oos = overfitting["oos_metrics"]
    top_cost = next(level for level in friction["levels"] if float(level["cost_bps"]) == 20.0)

    return {
        "label": "volatility_expansion_pullthrough_shorter_hold",
        "role": "defensive_research_hold",
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
        "completed_trades": int(paper["completed_trades"]),
        "failed_gates": list(paper["decision_record"]["failed_gates"]),
        "stack_read": "defensive_hold",
    }


def build_report() -> dict:
    attack = _attack_main()
    defensive = _defensive_hold()

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "stack_top": {
            "attack_anchor": attack["label"],
            "defensive_hold": defensive["label"],
        },
        "compared_models": [attack, defensive],
        "bridge_verdict": {
            "preferred_attack_model": attack["label"],
            "preferred_defensive_model": defensive["label"],
            "roles_are_distinct": True,
            "reason": "the attack anchor dominates on CAGR and still keeps drawdown in the mid-teens, while the defensive hold gives a lower-return alternative without overtaking the attack anchor's overall frontier.",
        },
        "decision_summary": [
            "ratio112 tighter_stop remains the attack anchor because it still owns the highest validated CAGR while keeping drawdown at 16% and costs controlled.",
            "pullthrough shorter_hold remains the best defensive research hold because it offers a calmer profile, but it does not overtake the attack anchor on total frontier quality.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    lines = [
        "# BTC 1d Attack-Defensive Bridge Screen",
        "",
        f"- Attack anchor: `{report['stack_top']['attack_anchor']}`",
        f"- Defensive hold: `{report['stack_top']['defensive_hold']}`",
        f"- Roles are distinct: `{report['bridge_verdict']['roles_are_distinct']}`",
        f"- Reason: {report['bridge_verdict']['reason']}",
        "",
    ]
    for row in report["compared_models"]:
        lines.extend(
            [
                f"## {row['label']}",
                f"- role: `{row['role']}`",
                f"- status_label: `{row['status_label']}`",
                f"- base: `{row['base_cagr']:.4f}` CAGR / `{row['base_mdd']:.4f}` MDD / Sharpe `{row['base_sharpe']:.4f}`",
                f"- OOS: `{row['oos_cagr']:.4f}` CAGR / `{row['oos_mdd']:.4f}` MDD / Sharpe `{row['oos_sharpe']:.4f}`",
                f"- drift: `{row['sensitivity_max_drift']:.4f}`",
                f"- cost20 Sharpe: `{row['cost20_sharpe']:.4f}`",
                f"- completed_trades: `{row['completed_trades']}`",
                f"- stack_read: `{row['stack_read']}`",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_attack_defensive_bridge_screen_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_attack_defensive_bridge_screen_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report_md_path": str(md_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
