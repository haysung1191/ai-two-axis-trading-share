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

from app.domains.backtesting.runner import BacktestMetrics, BacktestRunner, metrics_to_dict
from app.domains.market_data.binance_client import fetch_ohlcv
from app.domains.strategy.krw_btc_swing_trend import compute_swing_trend_signals
from app.domains.strategy.strategy_protocol import Strategy


@dataclass(frozen=True)
class CandidateAlphaOverlayArtifacts:
    report_json_path: Path
    report_md_path: Path
    report: dict[str, Any]


class _PrecomputedSignalStrategy(Strategy):
    name = "precomputed_signal"
    default_params: dict[str, float] = {}

    def __init__(self, signal: pd.Series) -> None:
        self._signal = signal.astype(float)

    def generate_signals(self, ohlcv: pd.DataFrame, params=None) -> pd.Series:
        _ = params
        return self._signal.reindex(ohlcv.index).fillna(0.0).astype(float)


def _latest_analysis_frame(analysis_dir: Path) -> Path:
    candidates = sorted(
        analysis_dir.glob("candidate_alpha_regime_frame_*.csv"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError("No Candidate Alpha frame artifact found")
    return candidates[0]


def load_candidate_alpha_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, parse_dates=["timestamp"]).set_index("timestamp")
    frame.index = pd.DatetimeIndex(frame.index)
    frame["avoidance_regime"] = frame["avoidance_regime"].astype(bool)
    return frame.sort_index(kind="mergesort")


def load_krw_btc_4h(start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return fetch_ohlcv(
        symbol="KRW-BTC",
        interval="4h",
        start_ts=start.to_pydatetime(),
        end_ts=end.to_pydatetime(),
    )


def build_4h_avoidance_overlay(alpha_frame_1h: pd.DataFrame, btc_4h: pd.DataFrame) -> pd.Series:
    # Candidate Alpha is defined on 1h bars. To align with a finalized 4h candle
    # starting at t, use the last completed 1h bar within that 4h window: t + 3h.
    anchor_index = pd.DatetimeIndex(btc_4h.index) + pd.Timedelta(hours=3)
    avoidance = (
        alpha_frame_1h["avoidance_regime"]
        .reindex(anchor_index, method="pad")
        .fillna(False)
        .astype(bool)
    )
    avoidance.index = btc_4h.index
    return avoidance


def build_overlay_signals(btc_4h: pd.DataFrame, avoidance_4h: pd.Series) -> tuple[pd.Series, pd.Series]:
    baseline = compute_swing_trend_signals(btc_4h)
    overlay = baseline.mask(avoidance_4h.reindex(baseline.index).fillna(False), 0.0).astype(float)
    return baseline.astype(float), overlay


def _metrics_delta(baseline: BacktestMetrics, overlay: BacktestMetrics) -> dict[str, float]:
    return {
        "sharpe": round(float(overlay.sharpe - baseline.sharpe), 8),
        "cagr": round(float(overlay.cagr - baseline.cagr), 8),
        "trades": int(overlay.trades - baseline.trades),
        "win_rate": round(float(overlay.win_rate - baseline.win_rate), 8),
        "max_drawdown": round(float(overlay.max_drawdown - baseline.max_drawdown), 8),
    }


def build_overlay_report(
    alpha_frame_1h: pd.DataFrame,
    btc_4h: pd.DataFrame,
    baseline_metrics: BacktestMetrics,
    overlay_metrics: BacktestMetrics,
    avoidance_4h: pd.Series,
) -> dict[str, Any]:
    delta = _metrics_delta(baseline_metrics, overlay_metrics)
    improves_directionally = (
        overlay_metrics.sharpe > baseline_metrics.sharpe
        and overlay_metrics.max_drawdown <= baseline_metrics.max_drawdown
    )
    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "series": {
            "candidate_alpha_asset_pair": "KRW-BTC / BTCUSDT",
            "baseline_strategy": "krw_btc_swing_trend",
            "baseline_interval": "4h",
            "overlay_semantics": "avoidance-regime detector",
        },
        "coverage": {
            "candidate_alpha_start": alpha_frame_1h.index.min().isoformat(),
            "candidate_alpha_end": alpha_frame_1h.index.max().isoformat(),
            "btc_4h_start": btc_4h.index.min().isoformat(),
            "btc_4h_end": btc_4h.index.max().isoformat(),
            "btc_4h_rows": int(len(btc_4h)),
            "avoidance_4h_count": int(avoidance_4h.sum()),
            "avoidance_4h_ratio": float(avoidance_4h.mean()),
        },
        "comparison": {
            "baseline": metrics_to_dict(baseline_metrics),
            "baseline_plus_candidate_alpha_avoidance_filter": metrics_to_dict(overlay_metrics),
            "delta_overlay_minus_baseline": delta,
        },
        "interpretation": {
            "improves_directionally": bool(improves_directionally),
            "primary_signal": (
                "overlay improves sharpe and does not worsen drawdown"
                if improves_directionally
                else "overlay does not improve the baseline in a clear direction"
            ),
        },
    }


def render_overlay_markdown(report: dict[str, Any]) -> str:
    baseline = report["comparison"]["baseline"]
    overlay = report["comparison"]["baseline_plus_candidate_alpha_avoidance_filter"]
    delta = report["comparison"]["delta_overlay_minus_baseline"]
    coverage = report["coverage"]
    lines = [
        "# Candidate Alpha Overlay Validation",
        "",
        "## Coverage",
        f"- baseline_interval: {report['series']['baseline_interval']}",
        f"- candidate_alpha_start: {coverage['candidate_alpha_start']}",
        f"- candidate_alpha_end: {coverage['candidate_alpha_end']}",
        f"- btc_4h_rows: {coverage['btc_4h_rows']}",
        f"- avoidance_4h_count: {coverage['avoidance_4h_count']}",
        f"- avoidance_4h_ratio: {coverage['avoidance_4h_ratio']}",
        "",
        "## Baseline",
        f"- sharpe: {baseline['sharpe']}",
        f"- cagr: {baseline['cagr']}",
        f"- trades: {baseline['trades']}",
        f"- win_rate: {baseline['win_rate']}",
        f"- max_drawdown: {baseline['max_drawdown']}",
        "",
        "## Baseline + Candidate Alpha Avoidance Filter",
        f"- sharpe: {overlay['sharpe']}",
        f"- cagr: {overlay['cagr']}",
        f"- trades: {overlay['trades']}",
        f"- win_rate: {overlay['win_rate']}",
        f"- max_drawdown: {overlay['max_drawdown']}",
        "",
        "## Delta (overlay - baseline)",
        f"- sharpe: {delta['sharpe']}",
        f"- cagr: {delta['cagr']}",
        f"- trades: {delta['trades']}",
        f"- win_rate: {delta['win_rate']}",
        f"- max_drawdown: {delta['max_drawdown']}",
        "",
        "## Conclusion",
        f"- improves_directionally: {report['interpretation']['improves_directionally']}",
        f"- primary_signal: {report['interpretation']['primary_signal']}",
    ]
    return "\n".join(lines) + "\n"


def run_candidate_alpha_overlay_validation(
    analysis_dir: Path,
    *,
    frame_path: Path | None = None,
) -> CandidateAlphaOverlayArtifacts:
    selected_frame_path = frame_path or _latest_analysis_frame(analysis_dir)
    alpha_frame_1h = load_candidate_alpha_frame(selected_frame_path)

    start = alpha_frame_1h.index.min().floor("4h")
    end = (alpha_frame_1h.index.max() + pd.Timedelta(hours=4)).ceil("4h")
    btc_4h = load_krw_btc_4h(start=start, end=end)

    avoidance_4h = build_4h_avoidance_overlay(alpha_frame_1h, btc_4h)
    baseline_signal, overlay_signal = build_overlay_signals(btc_4h, avoidance_4h)

    runner = BacktestRunner(seed=42)
    baseline_metrics = runner.run(_PrecomputedSignalStrategy(baseline_signal), btc_4h)
    overlay_metrics = runner.run(_PrecomputedSignalStrategy(overlay_signal), btc_4h)

    report = build_overlay_report(
        alpha_frame_1h=alpha_frame_1h,
        btc_4h=btc_4h,
        baseline_metrics=baseline_metrics,
        overlay_metrics=overlay_metrics,
        avoidance_4h=avoidance_4h,
    )

    analysis_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    report_json_path = analysis_dir / f"candidate_alpha_overlay_validation_{stamp}.json"
    report_md_path = analysis_dir / f"candidate_alpha_overlay_validation_{stamp}.md"
    report_json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report_md_path.write_text(render_overlay_markdown(report), encoding="utf-8")

    return CandidateAlphaOverlayArtifacts(
        report_json_path=report_json_path,
        report_md_path=report_md_path,
        report=report,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Candidate Alpha as an avoidance-regime overlay on KRW-BTC 4h swing trend.")
    parser.add_argument("--analysis-dir", default="analysis_results")
    parser.add_argument("--frame-path", default=None)
    args = parser.parse_args()

    artifacts = run_candidate_alpha_overlay_validation(
        Path(args.analysis_dir),
        frame_path=Path(args.frame_path) if args.frame_path else None,
    )
    print(
        json.dumps(
            {
                "report_json_path": str(artifacts.report_json_path),
                "report_md_path": str(artifacts.report_md_path),
                "comparison": artifacts.report["comparison"],
                "interpretation": artifacts.report["interpretation"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
