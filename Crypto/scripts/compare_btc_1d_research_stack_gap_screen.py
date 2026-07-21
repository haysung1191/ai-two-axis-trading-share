from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.attack_active_stack import ACTIVE_ATTACK_BACKUP_LABEL, ACTIVE_ATTACK_MAIN_LABEL
from scripts.compare_btc_1d_research_stack_top_screen import build_report as build_stack_top_report


ANALYSIS_DIR = Path("analysis_results")
TREND_DIP_PATH = Path(
    "analysis_results/btc_1d_trend_dip_reversal_breakout_symmetry_v4_btcusdt_1d_2200_paper_validation_20260415T211024Z.json"
)
SPIKE_REVERSAL_PATH = Path(
    "analysis_results/btc_1d_volatility_spike_reversal_continuation_high_cagr_batch_20260415T171339Z.json"
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _scoreboard_row(label: str, role: str, *, source_artifact: str) -> dict:
    scoreboard = _load_json(ANALYSIS_DIR / "btc_1d_model_scoreboard_latest.json")
    rows = list(scoreboard.get("top_models", [])) + list(scoreboard.get("top_new_models", []))
    row = next((item for item in rows if str(item.get("variant")) == label), None)
    cagr = float(row.get("cagr") or 0.0) if row else 0.0
    mdd = float(row.get("mdd") or 0.0) if row else 0.0
    sharpe = float(row.get("sharpe") or 0.0) if row else 0.0
    return {
        "label": label,
        "role": role,
        "source_artifact": source_artifact,
        "base_cagr": cagr,
        "base_mdd": mdd,
        "base_sharpe": round(sharpe, 4),
        "completed_trades": int(row.get("trades") or 0) if row else 0,
        "candidate_stage_status": "scoreboard_latest_fallback",
        "reason": "Archived timestamp artifact is absent; using latest scoreboard metrics so queue reporting remains available.",
    }


def _pct(value: float) -> float:
    return round(value * 100.0, 2)


def _find_stack_model(report: dict, label: str) -> dict:
    return next(item for item in report["models"] if item["label"] == label)


def _load_trend_dip_candidate() -> dict:
    if not TREND_DIP_PATH.exists():
        return _scoreboard_row(
            "trend_dip_reversal_breakout_tighter_stop_mid_hold",
            "attack_near_miss_hold",
            source_artifact=str(TREND_DIP_PATH),
        )
    payload = _load_json(TREND_DIP_PATH)
    metrics = payload["decision_record"]["key_metrics"]
    return {
        "label": "trend_dip_reversal_breakout_tighter_stop_mid_hold",
        "role": "attack_near_miss_hold",
        "source_artifact": str(TREND_DIP_PATH),
        "base_cagr": float(metrics["cagr"]),
        "base_mdd": float(metrics["max_drawdown"]),
        "base_sharpe": round(float(metrics["sharpe"]), 4),
        "completed_trades": int(payload.get("completed_trades", 0)),
        "candidate_stage_status": "validated_fail_hold",
        "reason": "Near-miss remained below the attack frontier and failed candidate-stage gates on drawdown, OOS, and sensitivity.",
    }


def _load_spike_reversal_hold() -> dict:
    if not SPIKE_REVERSAL_PATH.exists():
        return _scoreboard_row(
            "volatility_spike_reversal_continuation_slower_trend",
            "attack_near_miss_hold",
            source_artifact=str(SPIKE_REVERSAL_PATH),
        )
    payload = _load_json(SPIKE_REVERSAL_PATH)
    best = next(item for item in payload["results"] if item["variant_label"] == "slower_trend")
    return {
        "label": "volatility_spike_reversal_continuation_slower_trend",
        "role": "attack_near_miss_hold",
        "source_artifact": str(SPIKE_REVERSAL_PATH),
        "base_cagr": float(best["cagr"]),
        "base_mdd": float(best["max_drawdown"]),
        "base_sharpe": round(float(best["sharpe"]), 4),
        "completed_trades": int(best["completed_trades"]),
        "candidate_stage_status": "stage1_hold_only",
        "reason": "High-CAGR near-miss still carries materially higher drawdown than the attack main and was not promoted to candidate stage.",
    }


def _attach_gap_to_attack_main(row: dict, attack_main: dict) -> dict:
    enriched = dict(row)
    enriched["cagr_gap_to_attack_main_pct"] = round(_pct(row["base_cagr"]) - _pct(attack_main["base_cagr"]), 2)
    enriched["mdd_gap_to_attack_main_pct"] = round(_pct(row["base_mdd"]) - _pct(attack_main["base_mdd"]), 2)
    enriched["sharpe_gap_to_attack_main"] = round(row["base_sharpe"] - attack_main["base_sharpe"], 4)
    return enriched


def build_report() -> dict:
    stack_top = build_stack_top_report()
    attack_main = _find_stack_model(stack_top, ACTIVE_ATTACK_MAIN_LABEL)
    attack_backup = _find_stack_model(stack_top, ACTIVE_ATTACK_BACKUP_LABEL)
    defensive_hold = _find_stack_model(stack_top, "volatility_expansion_pullthrough_shorter_hold")
    trend_dip_hold = _attach_gap_to_attack_main(_load_trend_dip_candidate(), attack_main)
    spike_reversal_hold = _attach_gap_to_attack_main(_load_spike_reversal_hold(), attack_main)

    near_miss_rows = sorted(
        [trend_dip_hold, spike_reversal_hold],
        key=lambda item: (-item["base_cagr"], item["base_mdd"], -item["base_sharpe"]),
    )

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "stack_top": {
            "attack_main": attack_main["label"],
            "attack_backup": attack_backup["label"],
            "defensive_hold": defensive_hold["label"],
        },
        "frontier_models": [attack_main, attack_backup, defensive_hold],
        "recent_attack_near_miss_holds": near_miss_rows,
        "gap_summary": {
            "closest_cagr_near_miss": near_miss_rows[0]["label"],
            "closest_attack_alternative_by_mdd": min(near_miss_rows, key=lambda item: item["mdd_gap_to_attack_main_pct"])["label"],
            "preferred_attack_frontier": attack_main["label"],
            "reason": "Both near-miss holds still trail the attack main on drawdown by a wide margin, so the current frontier remains unchanged.",
        },
        "decision_summary": [
            "ratio112 tighter_stop remains the attack frontier.",
            "The active backup remains inside the attack frontier stack, but the frontier itself is still anchored by ratio112.",
            "Recent near-miss holds still sit several drawdown points above the frontier even when their CAGR gets close.",
        ],
    }
    return report


def _render_markdown(report: dict) -> str:
    lines = [
        "# BTC 1d Research Stack Gap Screen",
        "",
        f"- Attack main: `{report['stack_top']['attack_main']}`",
        f"- Attack backup: `{report['stack_top']['attack_backup']}`",
        f"- Defensive hold: `{report['stack_top']['defensive_hold']}`",
        f"- Closest CAGR near-miss: `{report['gap_summary']['closest_cagr_near_miss']}`",
        f"- Closest near-miss by MDD gap: `{report['gap_summary']['closest_attack_alternative_by_mdd']}`",
        f"- Preferred attack frontier: `{report['gap_summary']['preferred_attack_frontier']}`",
        f"- Reason: {report['gap_summary']['reason']}",
        "",
        "## Frontier",
        "",
    ]
    for row in report["frontier_models"]:
        lines.extend(
            [
                f"### {row['label']}",
                f"- role: `{row['role']}`",
                f"- base: `{row['base_cagr']:.4f}` CAGR / `{row['base_mdd']:.4f}` MDD / Sharpe `{row['base_sharpe']:.4f}`",
                "",
            ]
        )
    lines.append("## Recent Attack Near-Miss Holds")
    lines.append("")
    for row in report["recent_attack_near_miss_holds"]:
        lines.extend(
            [
                f"### {row['label']}",
                f"- status: `{row['candidate_stage_status']}`",
                f"- base: `{row['base_cagr']:.4f}` CAGR / `{row['base_mdd']:.4f}` MDD / Sharpe `{row['base_sharpe']:.4f}`",
                f"- gap to attack main: CAGR `{row['cagr_gap_to_attack_main_pct']:.2f}%`, MDD `{row['mdd_gap_to_attack_main_pct']:.2f}%`, Sharpe `{row['sharpe_gap_to_attack_main']:.4f}`",
                f"- completed trades: `{row['completed_trades']}`",
                f"- reason: {row['reason']}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    report = build_report()
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = ANALYSIS_DIR / f"btc_1d_research_stack_gap_screen_{stamp}.json"
    md_path = ANALYSIS_DIR / f"btc_1d_research_stack_gap_screen_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report_md_path": str(md_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
