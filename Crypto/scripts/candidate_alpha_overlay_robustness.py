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
class CandidateAlphaOverlayRobustnessArtifacts:
    memo_json_path: Path
    memo_md_path: Path
    memo: dict[str, Any]


def _delta(baseline: dict[str, Any], overlay: dict[str, Any]) -> dict[str, float]:
    return {
        "sharpe": round(float(overlay["sharpe"] - baseline["sharpe"]), 8),
        "cagr": round(float(overlay["cagr"] - baseline["cagr"]), 8),
        "trades": int(overlay["trades"] - baseline["trades"]),
        "win_rate": round(float(overlay["win_rate"] - baseline["win_rate"]), 8),
        "max_drawdown": round(float(overlay["max_drawdown"] - baseline["max_drawdown"]), 8),
    }


def _direction_flags(delta: dict[str, float]) -> dict[str, bool]:
    return {
        "sharpe_improved": delta["sharpe"] > 0.0,
        "cagr_improved": delta["cagr"] > 0.0,
        "win_rate_improved": delta["win_rate"] > 0.0,
        "drawdown_improved": delta["max_drawdown"] <= 0.0,
    }


def _chunk_labels(index: pd.Index, chunks: int) -> pd.Series:
    return pd.qcut(pd.Series(range(len(index)), index=index), q=chunks, labels=[f"chunk_{i+1}" for i in range(chunks)])


def build_overlay_robustness_memo(
    btc_4h: pd.DataFrame,
    baseline_signal: pd.Series,
    overlay_signal: pd.Series,
    *,
    chunks: int = 3,
) -> dict[str, Any]:
    runner = BacktestRunner(seed=42)

    full_baseline = metrics_to_dict(runner.run(_PrecomputedSignalStrategy(baseline_signal), btc_4h))
    full_overlay = metrics_to_dict(runner.run(_PrecomputedSignalStrategy(overlay_signal), btc_4h))
    full_delta = _delta(full_baseline, full_overlay)
    full_flags = _direction_flags(full_delta)

    labels = _chunk_labels(btc_4h.index, chunks)
    subperiods: dict[str, Any] = {}
    consistency = {
        "sharpe_improved_chunks": 0,
        "cagr_improved_chunks": 0,
        "win_rate_improved_chunks": 0,
        "drawdown_improved_chunks": 0,
    }

    for label in [f"chunk_{i+1}" for i in range(chunks)]:
        mask = labels == label
        chunk_ohlcv = btc_4h.loc[mask].copy()
        chunk_baseline_signal = baseline_signal.reindex(chunk_ohlcv.index).fillna(0.0)
        chunk_overlay_signal = overlay_signal.reindex(chunk_ohlcv.index).fillna(0.0)

        baseline_metrics = metrics_to_dict(runner.run(_PrecomputedSignalStrategy(chunk_baseline_signal), chunk_ohlcv))
        overlay_metrics = metrics_to_dict(runner.run(_PrecomputedSignalStrategy(chunk_overlay_signal), chunk_ohlcv))
        delta = _delta(baseline_metrics, overlay_metrics)
        flags = _direction_flags(delta)
        for key in consistency:
            flag_key = key.replace("_chunks", "")
            if flags[flag_key]:
                consistency[key] += 1
        subperiods[label] = {
            "baseline": baseline_metrics,
            "overlay": overlay_metrics,
            "delta_overlay_minus_baseline": delta,
            "direction_flags": flags,
        }

    continue_direction = (
        full_flags["sharpe_improved"]
        and full_flags["drawdown_improved"]
        and consistency["sharpe_improved_chunks"] >= 2
        and consistency["drawdown_improved_chunks"] >= 2
    )
    pause_direction = (
        full_flags["sharpe_improved"] or full_flags["drawdown_improved"]
    ) and not continue_direction

    if continue_direction:
        final_decision = "continue"
        reason = "full sample improves sharpe and drawdown, and that direction holds in most subperiods."
    elif pause_direction:
        final_decision = "pause"
        reason = "full-sample improvement exists, but subperiod consistency is too mixed to treat as stable yet."
    else:
        final_decision = "stop"
        reason = "overlay improvement does not hold directionally once the sample is split."

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "coverage": {
            "rows": int(len(btc_4h)),
            "start": btc_4h.index.min().isoformat(),
            "end": btc_4h.index.max().isoformat(),
            "chunks": chunks,
        },
        "full_sample": {
            "baseline": full_baseline,
            "overlay": full_overlay,
            "delta_overlay_minus_baseline": full_delta,
            "direction_flags": full_flags,
        },
        "subperiods": subperiods,
        "consistency": consistency,
        "final_decision": final_decision,
        "decision_reason": reason,
    }


def render_overlay_robustness_markdown(memo: dict[str, Any]) -> str:
    full = memo["full_sample"]
    lines = [
        "# Candidate Alpha Overlay Robustness Memo",
        "",
        "## Full Sample Recap",
        f"- baseline sharpe: {full['baseline']['sharpe']}",
        f"- overlay sharpe: {full['overlay']['sharpe']}",
        f"- delta sharpe: {full['delta_overlay_minus_baseline']['sharpe']}",
        f"- baseline cagr: {full['baseline']['cagr']}",
        f"- overlay cagr: {full['overlay']['cagr']}",
        f"- delta cagr: {full['delta_overlay_minus_baseline']['cagr']}",
        f"- baseline trades: {full['baseline']['trades']}",
        f"- overlay trades: {full['overlay']['trades']}",
        f"- baseline win_rate: {full['baseline']['win_rate']}",
        f"- overlay win_rate: {full['overlay']['win_rate']}",
        f"- baseline max_drawdown: {full['baseline']['max_drawdown']}",
        f"- overlay max_drawdown: {full['overlay']['max_drawdown']}",
        "",
        "## Subperiod Comparison",
    ]
    for label, block in memo["subperiods"].items():
        delta = block["delta_overlay_minus_baseline"]
        flags = block["direction_flags"]
        lines.extend(
            [
                f"### {label}",
                f"- delta sharpe: {delta['sharpe']}",
                f"- delta cagr: {delta['cagr']}",
                f"- delta trades: {delta['trades']}",
                f"- delta win_rate: {delta['win_rate']}",
                f"- delta max_drawdown: {delta['max_drawdown']}",
                f"- sharpe_improved: {flags['sharpe_improved']}",
                f"- cagr_improved: {flags['cagr_improved']}",
                f"- win_rate_improved: {flags['win_rate_improved']}",
                f"- drawdown_improved: {flags['drawdown_improved']}",
                "",
            ]
        )
    consistency = memo["consistency"]
    lines.extend(
        [
            "## Consistency Summary",
            f"- sharpe improved chunks: {consistency['sharpe_improved_chunks']}",
            f"- cagr improved chunks: {consistency['cagr_improved_chunks']}",
            f"- win_rate improved chunks: {consistency['win_rate_improved_chunks']}",
            f"- drawdown improved chunks: {consistency['drawdown_improved_chunks']}",
            "",
            "## Final Decision",
            f"- decision: {memo['final_decision']}",
            f"- reason: {memo['decision_reason']}",
        ]
    )
    return "\n".join(lines) + "\n"


def run_candidate_alpha_overlay_robustness(
    analysis_dir: Path,
    *,
    frame_path: Path | None = None,
    chunks: int = 3,
) -> CandidateAlphaOverlayRobustnessArtifacts:
    selected_frame_path = frame_path or _latest_analysis_frame(analysis_dir)
    alpha_frame_1h = load_candidate_alpha_frame(selected_frame_path)
    start = alpha_frame_1h.index.min().floor("4h")
    end = (alpha_frame_1h.index.max() + pd.Timedelta(hours=4)).ceil("4h")
    btc_4h = load_krw_btc_4h(start=start, end=end)
    avoidance_4h = build_4h_avoidance_overlay(alpha_frame_1h, btc_4h)
    baseline_signal, overlay_signal = build_overlay_signals(btc_4h, avoidance_4h)
    memo = build_overlay_robustness_memo(btc_4h, baseline_signal, overlay_signal, chunks=chunks)

    analysis_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    memo_json_path = analysis_dir / f"candidate_alpha_overlay_robustness_{stamp}.json"
    memo_md_path = analysis_dir / f"candidate_alpha_overlay_robustness_{stamp}.md"
    memo_json_path.write_text(json.dumps(memo, indent=2), encoding="utf-8")
    memo_md_path.write_text(render_overlay_robustness_markdown(memo), encoding="utf-8")
    return CandidateAlphaOverlayRobustnessArtifacts(memo_json_path=memo_json_path, memo_md_path=memo_md_path, memo=memo)


def main() -> None:
    parser = argparse.ArgumentParser(description="Robustness-check Candidate Alpha avoidance overlay on KRW-BTC 4h swing trend.")
    parser.add_argument("--analysis-dir", default="analysis_results")
    parser.add_argument("--frame-path", default=None)
    parser.add_argument("--chunks", type=int, default=3)
    args = parser.parse_args()

    artifacts = run_candidate_alpha_overlay_robustness(
        Path(args.analysis_dir),
        frame_path=Path(args.frame_path) if args.frame_path else None,
        chunks=max(2, int(args.chunks)),
    )
    print(
        json.dumps(
            {
                "memo_json_path": str(artifacts.memo_json_path),
                "memo_md_path": str(artifacts.memo_md_path),
                "final_decision": artifacts.memo["final_decision"],
                "consistency": artifacts.memo["consistency"],
                "decision_reason": artifacts.memo["decision_reason"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
