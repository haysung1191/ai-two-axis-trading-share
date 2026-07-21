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

from scripts.candidate_alpha_overlay_validation import (
    _latest_analysis_frame,
    build_4h_avoidance_overlay,
    build_overlay_signals,
    load_candidate_alpha_frame,
    load_krw_btc_4h,
)


@dataclass(frozen=True)
class CandidateAlphaOverlayAttributionArtifacts:
    report_json_path: Path
    report_md_path: Path
    report: dict[str, Any]


def compute_strategy_returns(signal: pd.Series, ohlcv: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    signal = signal.reindex(ohlcv.index).fillna(0.0).astype(float)
    period_returns = ohlcv["close"].pct_change().fillna(0.0).astype(float)
    position = signal.shift(1).fillna(0.0).astype(float)
    strategy_returns = (period_returns * position).astype(float)
    return strategy_returns, position


def _contiguous_true_segments(mask: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    mask = mask.fillna(False).astype(bool)
    segments: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    start: pd.Timestamp | None = None
    prev_ts: pd.Timestamp | None = None

    for ts, flag in mask.items():
        if flag and start is None:
            start = ts
        if not flag and start is not None and prev_ts is not None:
            segments.append((start, prev_ts))
            start = None
        prev_ts = ts

    if start is not None and prev_ts is not None:
        segments.append((start, prev_ts))
    return segments


def extract_signal_episodes(signal: pd.Series, strategy_returns: pd.Series) -> list[dict[str, Any]]:
    signal = signal.astype(float)
    episodes: list[dict[str, Any]] = []
    active = signal > 0
    for start_ts, end_ts in _contiguous_true_segments(active):
        idx = signal.index
        start_loc = idx.get_loc(start_ts)
        end_loc = idx.get_loc(end_ts)
        ret_start = start_loc + 1
        ret_end = end_loc
        if ret_start <= ret_end:
            pnl_slice = strategy_returns.iloc[ret_start : ret_end + 1]
            holding_bars = int(len(pnl_slice))
            pnl = float((1.0 + pnl_slice).prod() - 1.0)
        else:
            holding_bars = 0
            pnl = 0.0
        episodes.append(
            {
                "entry_ts": start_ts.isoformat(),
                "exit_ts": end_ts.isoformat(),
                "holding_bars": holding_bars,
                "pnl": pnl,
            }
        )
    return episodes


def _segment_pnl(returns: pd.Series, idx: pd.Index, start_ts: pd.Timestamp, end_ts: pd.Timestamp) -> float:
    start_loc = idx.get_loc(start_ts)
    end_loc = idx.get_loc(end_ts)
    ret_start = start_loc + 1
    ret_end = end_loc
    if ret_start <= ret_end:
        pnl_slice = returns.iloc[ret_start : ret_end + 1]
        return float((1.0 + pnl_slice).prod() - 1.0)
    return 0.0


def build_overlay_attribution_report(
    btc_4h: pd.DataFrame,
    baseline_signal: pd.Series,
    overlay_signal: pd.Series,
    avoidance_4h: pd.Series,
) -> dict[str, Any]:
    idx = btc_4h.index
    baseline_signal = baseline_signal.reindex(idx).fillna(0.0).astype(float)
    overlay_signal = overlay_signal.reindex(idx).fillna(0.0).astype(float)
    avoidance_4h = avoidance_4h.reindex(idx).fillna(False).astype(bool)

    baseline_returns, _ = compute_strategy_returns(baseline_signal, btc_4h)
    overlay_returns, _ = compute_strategy_returns(overlay_signal, btc_4h)

    baseline_episodes = extract_signal_episodes(baseline_signal, baseline_returns)
    overlay_episodes = extract_signal_episodes(overlay_signal, overlay_returns)

    baseline_entry = (baseline_signal > 0) & (baseline_signal.shift(1).fillna(0.0) <= 0)
    overlay_entry = (overlay_signal > 0) & (overlay_signal.shift(1).fillna(0.0) <= 0)
    overlay_exit = (overlay_signal <= 0) & (overlay_signal.shift(1).fillna(0.0) > 0)

    entries_blocked = baseline_entry & (overlay_signal <= 0)
    forced_exits = overlay_exit & (baseline_signal > 0)
    additional_reentries = overlay_entry & (baseline_signal > 0) & (baseline_signal.shift(1).fillna(0.0) > 0)

    baseline_only_mask = (baseline_signal > 0) & (overlay_signal <= 0)
    baseline_only_segments = []
    for start_ts, end_ts in _contiguous_true_segments(baseline_only_mask):
        baseline_only_segments.append(
            {
                "start_ts": start_ts.isoformat(),
                "end_ts": end_ts.isoformat(),
                "holding_bars": int(idx.get_loc(end_ts) - idx.get_loc(start_ts) + 1),
                "pnl": _segment_pnl(baseline_returns, idx, start_ts, end_ts),
            }
        )

    overlay_reentry_segments = []
    for episode in overlay_episodes:
        entry_ts = pd.Timestamp(episode["entry_ts"])
        entry_loc = idx.get_loc(entry_ts)
        prev_loc = max(0, entry_loc - 1)
        if baseline_signal.iloc[entry_loc] > 0 and baseline_signal.iloc[prev_loc] > 0:
            overlay_reentry_segments.append(episode)

    fully_avoided_baseline_trades = []
    for episode in baseline_episodes:
        start_ts = pd.Timestamp(episode["entry_ts"])
        end_ts = pd.Timestamp(episode["exit_ts"])
        overlay_slice = overlay_signal.loc[start_ts:end_ts]
        if (overlay_slice <= 0).all():
            fully_avoided_baseline_trades.append(episode)

    avg_holding_baseline = float(pd.Series([episode["holding_bars"] for episode in baseline_episodes]).mean()) if baseline_episodes else 0.0
    avg_holding_overlay = float(pd.Series([episode["holding_bars"] for episode in overlay_episodes]).mean()) if overlay_episodes else 0.0

    avoided_segment_pnls = [segment["pnl"] for segment in baseline_only_segments]
    avoided_trade_pnls = [trade["pnl"] for trade in fully_avoided_baseline_trades]
    reentry_pnls = [segment["pnl"] for segment in overlay_reentry_segments]

    avoided_mean = float(pd.Series(avoided_segment_pnls).mean()) if avoided_segment_pnls else 0.0
    reentry_mean = float(pd.Series(reentry_pnls).mean()) if reentry_pnls else 0.0
    avoided_total = float(sum(avoided_segment_pnls)) if avoided_segment_pnls else 0.0
    reentry_total = float(sum(reentry_pnls)) if reentry_pnls else 0.0

    if avoided_total < 0 and reentry_total >= 0:
        dominant_mechanism = "improvement mainly comes from cutting baseline-only losing exposure and re-entering later without losing the entire move"
    elif avoided_total < 0:
        dominant_mechanism = "improvement mainly comes from avoiding baseline-only losing exposure"
    elif reentry_total > 0:
        dominant_mechanism = "improvement mainly comes from timing changes and profitable re-entries rather than pure loss avoidance"
    else:
        dominant_mechanism = "overlay effect is mixed and not dominated by one clean event-level mechanism"

    if avoided_total < 0 and reentry_total >= 0:
        final_decision = "continue"
    elif avoided_total < 0 or reentry_total > 0:
        final_decision = "continue with caution"
    else:
        final_decision = "pause"

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "coverage": {
            "rows": int(len(idx)),
            "start": idx.min().isoformat(),
            "end": idx.max().isoformat(),
            "avoidance_ratio": float(avoidance_4h.mean()),
        },
        "event_counts": {
            "baseline_trade_count": int(len(baseline_episodes)),
            "overlay_trade_count": int(len(overlay_episodes)),
            "entries_blocked_by_overlay": int(entries_blocked.sum()),
            "forced_exits_by_overlay": int(forced_exits.sum()),
            "additional_reentries_due_to_overlay": int(additional_reentries.sum()),
        },
        "holding_periods": {
            "baseline_avg_holding_bars": avg_holding_baseline,
            "overlay_avg_holding_bars": avg_holding_overlay,
            "delta_avg_holding_bars": float(avg_holding_overlay - avg_holding_baseline),
        },
        "pnl_attribution": {
            "fully_avoided_baseline_trade_count": int(len(fully_avoided_baseline_trades)),
            "fully_avoided_baseline_trade_mean_pnl": float(pd.Series(avoided_trade_pnls).mean()) if avoided_trade_pnls else 0.0,
            "fully_avoided_baseline_trade_total_pnl": float(sum(avoided_trade_pnls)) if avoided_trade_pnls else 0.0,
            "baseline_only_segment_count": int(len(baseline_only_segments)),
            "baseline_only_segment_mean_pnl": avoided_mean,
            "baseline_only_segment_total_pnl": avoided_total,
            "overlay_reentry_segment_count": int(len(overlay_reentry_segments)),
            "overlay_reentry_segment_mean_pnl": reentry_mean,
            "overlay_reentry_segment_total_pnl": reentry_total,
        },
        "mechanism": {
            "dominant_mechanism": dominant_mechanism,
            "confidence_signal": (
                "strengthens"
                if final_decision == "continue"
                else "mixed"
                if final_decision == "continue with caution"
                else "weakens"
            ),
        },
        "final_decision": final_decision,
    }


def render_overlay_attribution_markdown(report: dict[str, Any]) -> str:
    counts = report["event_counts"]
    holding = report["holding_periods"]
    pnl = report["pnl_attribution"]
    lines = [
        "# Candidate Alpha Overlay Attribution Report",
        "",
        "## Event Counts",
        f"- baseline_trade_count: {counts['baseline_trade_count']}",
        f"- overlay_trade_count: {counts['overlay_trade_count']}",
        f"- entries_blocked_by_overlay: {counts['entries_blocked_by_overlay']}",
        f"- forced_exits_by_overlay: {counts['forced_exits_by_overlay']}",
        f"- additional_reentries_due_to_overlay: {counts['additional_reentries_due_to_overlay']}",
        "",
        "## Holding Periods",
        f"- baseline_avg_holding_bars: {holding['baseline_avg_holding_bars']}",
        f"- overlay_avg_holding_bars: {holding['overlay_avg_holding_bars']}",
        f"- delta_avg_holding_bars: {holding['delta_avg_holding_bars']}",
        "",
        "## PnL Attribution",
        f"- fully_avoided_baseline_trade_count: {pnl['fully_avoided_baseline_trade_count']}",
        f"- fully_avoided_baseline_trade_mean_pnl: {pnl['fully_avoided_baseline_trade_mean_pnl']}",
        f"- fully_avoided_baseline_trade_total_pnl: {pnl['fully_avoided_baseline_trade_total_pnl']}",
        f"- baseline_only_segment_count: {pnl['baseline_only_segment_count']}",
        f"- baseline_only_segment_mean_pnl: {pnl['baseline_only_segment_mean_pnl']}",
        f"- baseline_only_segment_total_pnl: {pnl['baseline_only_segment_total_pnl']}",
        f"- overlay_reentry_segment_count: {pnl['overlay_reentry_segment_count']}",
        f"- overlay_reentry_segment_mean_pnl: {pnl['overlay_reentry_segment_mean_pnl']}",
        f"- overlay_reentry_segment_total_pnl: {pnl['overlay_reentry_segment_total_pnl']}",
        "",
        "## Mechanism",
        f"- dominant_mechanism: {report['mechanism']['dominant_mechanism']}",
        f"- confidence_signal: {report['mechanism']['confidence_signal']}",
        "",
        "## Final Decision",
        f"- decision: {report['final_decision']}",
    ]
    return "\n".join(lines) + "\n"


def run_candidate_alpha_overlay_attribution(
    analysis_dir: Path,
    *,
    frame_path: Path | None = None,
) -> CandidateAlphaOverlayAttributionArtifacts:
    selected_frame_path = frame_path or _latest_analysis_frame(analysis_dir)
    alpha_frame_1h = load_candidate_alpha_frame(selected_frame_path)
    start = alpha_frame_1h.index.min().floor("4h")
    end = (alpha_frame_1h.index.max() + pd.Timedelta(hours=4)).ceil("4h")
    btc_4h = load_krw_btc_4h(start=start, end=end)
    avoidance_4h = build_4h_avoidance_overlay(alpha_frame_1h, btc_4h)
    baseline_signal, overlay_signal = build_overlay_signals(btc_4h, avoidance_4h)
    report = build_overlay_attribution_report(btc_4h, baseline_signal, overlay_signal, avoidance_4h)

    analysis_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    report_json_path = analysis_dir / f"candidate_alpha_overlay_attribution_{stamp}.json"
    report_md_path = analysis_dir / f"candidate_alpha_overlay_attribution_{stamp}.md"
    report_json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report_md_path.write_text(render_overlay_attribution_markdown(report), encoding="utf-8")
    return CandidateAlphaOverlayAttributionArtifacts(report_json_path=report_json_path, report_md_path=report_md_path, report=report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate event-level attribution for Candidate Alpha overlay on KRW-BTC 4h swing trend.")
    parser.add_argument("--analysis-dir", default="analysis_results")
    parser.add_argument("--frame-path", default=None)
    args = parser.parse_args()

    artifacts = run_candidate_alpha_overlay_attribution(
        Path(args.analysis_dir),
        frame_path=Path(args.frame_path) if args.frame_path else None,
    )
    print(
        json.dumps(
            {
                "report_json_path": str(artifacts.report_json_path),
                "report_md_path": str(artifacts.report_md_path),
                "event_counts": artifacts.report["event_counts"],
                "pnl_attribution": artifacts.report["pnl_attribution"],
                "final_decision": artifacts.report["final_decision"],
                "mechanism": artifacts.report["mechanism"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
