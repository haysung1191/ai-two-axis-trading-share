from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.domains.backtesting.runner import BacktestRunner, metrics_to_dict
from scripts.candidate_alpha_overlay_validation import (
    _PrecomputedSignalStrategy,
    _latest_analysis_frame,
    build_4h_avoidance_overlay,
    build_overlay_signals,
    load_candidate_alpha_frame,
    load_krw_btc_4h,
)


@dataclass(frozen=True)
class CandidateAlphaOverlayFrictionArtifacts:
    report_json_path: Path
    report_md_path: Path
    report: dict[str, Any]


def _delta(baseline: dict[str, Any], overlay: dict[str, Any]) -> dict[str, float]:
    return {
        "sharpe": round(float(overlay["sharpe"] - baseline["sharpe"]), 8),
        "cagr": round(float(overlay["cagr"] - baseline["cagr"]), 8),
        "trades": int(overlay["trades"] - baseline["trades"]),
        "win_rate": round(float(overlay["win_rate"] - baseline["win_rate"]), 8),
        "max_drawdown": round(float(overlay["max_drawdown"] - baseline["max_drawdown"]), 8),
    }


def _overlay_advantage(delta: dict[str, float]) -> bool:
    return delta["sharpe"] > 0.0 and delta["cagr"] > 0.0 and delta["max_drawdown"] <= 0.0


def build_overlay_friction_report(
    btc_4h,
    baseline_signal,
    overlay_signal,
    *,
    cost_levels_bps: list[float],
) -> dict[str, Any]:
    runner = BacktestRunner(seed=42)
    levels: dict[str, Any] = {}
    surviving_levels: list[float] = []

    for cost_bps in cost_levels_bps:
        baseline = metrics_to_dict(
            runner.run(
                _PrecomputedSignalStrategy(baseline_signal),
                btc_4h,
                fee_bps=float(cost_bps),
            )
        )
        overlay = metrics_to_dict(
            runner.run(
                _PrecomputedSignalStrategy(overlay_signal),
                btc_4h,
                fee_bps=float(cost_bps),
            )
        )
        delta = _delta(baseline, overlay)
        keeps_advantage = _overlay_advantage(delta)
        if keeps_advantage:
            surviving_levels.append(float(cost_bps))
        levels[f"{int(cost_bps)}bps"] = {
            "assumption": {
                "per_signal_change_cost_bps": float(cost_bps),
                "model": "fee_bps applied on each position change via turnover",
            },
            "baseline": baseline,
            "overlay": overlay,
            "delta_overlay_minus_baseline": delta,
            "overlay_advantage_survives": keeps_advantage,
        }

    if surviving_levels:
        max_surviving = max(surviving_levels)
        if max_surviving >= 20.0:
            final_decision = "continue"
            reason = "overlay advantage survives even under the heavier simple friction assumption tested."
        else:
            final_decision = "continue with caution"
            reason = "overlay advantage survives only under lighter friction assumptions."
    else:
        final_decision = "pause"
        reason = "overlay advantage disappears once simple execution friction is applied."

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "coverage": {
            "rows": int(len(btc_4h)),
            "start": btc_4h.index.min().isoformat(),
            "end": btc_4h.index.max().isoformat(),
        },
        "cost_levels_bps": [float(v) for v in cost_levels_bps],
        "levels": levels,
        "final_decision": final_decision,
        "decision_reason": reason,
    }


def render_overlay_friction_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Candidate Alpha Overlay Friction Sanity Check",
        "",
        "## Coverage",
        f"- rows: {report['coverage']['rows']}",
        f"- start: {report['coverage']['start']}",
        f"- end: {report['coverage']['end']}",
        "",
    ]
    for level_name, block in report["levels"].items():
        baseline = block["baseline"]
        overlay = block["overlay"]
        delta = block["delta_overlay_minus_baseline"]
        lines.extend(
            [
                f"## {level_name}",
                f"- baseline sharpe: {baseline['sharpe']}",
                f"- overlay sharpe: {overlay['sharpe']}",
                f"- delta sharpe: {delta['sharpe']}",
                f"- baseline cagr: {baseline['cagr']}",
                f"- overlay cagr: {overlay['cagr']}",
                f"- delta cagr: {delta['cagr']}",
                f"- baseline trades: {baseline['trades']}",
                f"- overlay trades: {overlay['trades']}",
                f"- baseline win_rate: {baseline['win_rate']}",
                f"- overlay win_rate: {overlay['win_rate']}",
                f"- baseline max_drawdown: {baseline['max_drawdown']}",
                f"- overlay max_drawdown: {overlay['max_drawdown']}",
                f"- overlay_advantage_survives: {block['overlay_advantage_survives']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Final Decision",
            f"- decision: {report['final_decision']}",
            f"- reason: {report['decision_reason']}",
        ]
    )
    return "\n".join(lines) + "\n"


def run_candidate_alpha_overlay_friction_report(
    analysis_dir: Path,
    *,
    frame_path: Path | None = None,
    cost_levels_bps: list[float] | None = None,
) -> CandidateAlphaOverlayFrictionArtifacts:
    selected_frame_path = frame_path or _latest_analysis_frame(analysis_dir)
    alpha_frame_1h = load_candidate_alpha_frame(selected_frame_path)
    start = alpha_frame_1h.index.min().floor("4h")
    end = (alpha_frame_1h.index.max() + pd.Timedelta(hours=4)).ceil("4h")
    btc_4h = load_krw_btc_4h(start=start, end=end)
    avoidance_4h = build_4h_avoidance_overlay(alpha_frame_1h, btc_4h)
    baseline_signal, overlay_signal = build_overlay_signals(btc_4h, avoidance_4h)

    levels = cost_levels_bps or [0.0, 5.0, 10.0, 20.0]
    report = build_overlay_friction_report(
        btc_4h,
        baseline_signal,
        overlay_signal,
        cost_levels_bps=levels,
    )

    analysis_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    report_json_path = analysis_dir / f"candidate_alpha_overlay_friction_{stamp}.json"
    report_md_path = analysis_dir / f"candidate_alpha_overlay_friction_{stamp}.md"
    report_json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report_md_path.write_text(render_overlay_friction_markdown(report), encoding="utf-8")
    return CandidateAlphaOverlayFrictionArtifacts(report_json_path=report_json_path, report_md_path=report_md_path, report=report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run simple friction sensitivity for Candidate Alpha overlay.")
    parser.add_argument("--analysis-dir", default="analysis_results")
    parser.add_argument("--frame-path", default=None)
    args = parser.parse_args()

    artifacts = run_candidate_alpha_overlay_friction_report(
        Path(args.analysis_dir),
        frame_path=Path(args.frame_path) if args.frame_path else None,
    )
    print(
        json.dumps(
            {
                "report_json_path": str(artifacts.report_json_path),
                "report_md_path": str(artifacts.report_md_path),
                "final_decision": artifacts.report["final_decision"],
                "decision_reason": artifacts.report["decision_reason"],
                "levels": {
                    key: {
                        "delta": value["delta_overlay_minus_baseline"],
                        "overlay_advantage_survives": value["overlay_advantage_survives"],
                    }
                    for key, value in artifacts.report["levels"].items()
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
