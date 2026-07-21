from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.domains.backtesting.runner import BacktestMetrics, BacktestRunner, metrics_to_dict
from app.domains.strategy.btc_derivatives_positioning_stress import compute_overlay_signals
from app.domains.strategy.strategy_protocol import Strategy


BINANCE_SPOT_KLINES_URL = "https://api.binance.com/api/v3/klines"
BINANCE_FUNDING_URL = "https://fapi.binance.com/fapi/v1/fundingRate"
BINANCE_OI_HIST_URL = "https://fapi.binance.com/futures/data/openInterestHist"


@dataclass(frozen=True)
class PositioningStressArtifacts:
    run_id: str
    report_json_path: Path
    report_md_path: Path
    frame_csv_path: Path
    report: dict[str, Any]


class _PrecomputedSignalStrategy(Strategy):
    name = "precomputed_signal"
    default_params: dict[str, float] = {}

    def __init__(self, signal: pd.Series) -> None:
        self._signal = signal.astype(float)

    def generate_signals(self, ohlcv: pd.DataFrame, params=None) -> pd.Series:
        _ = params
        return self._signal.reindex(ohlcv.index).fillna(0.0).astype(float)


def fetch_binance_spot_klines(symbol: str, interval: str, limit: int = 1500) -> pd.DataFrame:
    requested = max(1, int(limit))
    batches: list[pd.DataFrame] = []
    end_time: int | None = None

    with httpx.Client(timeout=20.0) as client:
        while requested > 0:
            batch_limit = min(1000, requested)
            params: dict[str, Any] = {"symbol": symbol, "interval": interval, "limit": batch_limit}
            if end_time is not None:
                params["endTime"] = int(end_time)
            response = client.get(BINANCE_SPOT_KLINES_URL, params=params)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list) or not payload:
                break

            frame = pd.DataFrame(payload).iloc[:, :6]
            frame.columns = ["open_time", "open", "high", "low", "close", "volume"]
            frame["open_time"] = frame["open_time"].astype("int64")
            for column in ["open", "high", "low", "close", "volume"]:
                frame[column] = frame[column].astype("float64")
            frame["timestamp"] = pd.to_datetime(frame["open_time"], unit="ms", utc=True)
            batches.append(frame[["timestamp", "open", "high", "low", "close", "volume"]])

            requested -= len(frame)
            oldest_open_time = int(frame["open_time"].min())
            next_end_time = oldest_open_time - 1
            if end_time is not None and next_end_time >= end_time:
                break
            end_time = next_end_time
            if len(frame) < batch_limit:
                break

    if not batches:
        raise ValueError(f"No Binance spot klines returned for {symbol}")

    merged = pd.concat(batches, axis=0, ignore_index=True)
    merged = merged.sort_values("timestamp", kind="mergesort").drop_duplicates(subset=["timestamp"], keep="first")
    merged = merged.tail(max(1, int(limit))).set_index("timestamp")
    return merged[["open", "high", "low", "close", "volume"]]


def fetch_binance_funding_rates(symbol: str, limit: int = 1200) -> pd.DataFrame:
    requested = max(1, int(limit))
    batches: list[pd.DataFrame] = []
    start_time: int | None = None

    with httpx.Client(timeout=20.0) as client:
        while requested > 0:
            batch_limit = min(1000, requested)
            params: dict[str, Any] = {"symbol": symbol, "limit": batch_limit}
            if start_time is not None:
                params["startTime"] = int(start_time)
            response = client.get(BINANCE_FUNDING_URL, params=params)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list) or not payload:
                break

            frame = pd.DataFrame(payload)
            frame = frame[["fundingTime", "fundingRate"]].copy()
            frame["fundingTime"] = frame["fundingTime"].astype("int64")
            frame["fundingRate"] = frame["fundingRate"].astype("float64")
            frame["timestamp"] = pd.to_datetime(frame["fundingTime"], unit="ms", utc=True)
            batches.append(frame[["timestamp", "fundingRate"]])

            requested -= len(frame)
            last_time = int(frame["fundingTime"].max())
            next_start = last_time + 1
            if start_time is not None and next_start <= start_time:
                break
            start_time = next_start
            if len(frame) < batch_limit:
                break

    if not batches:
        raise ValueError(f"No Binance funding rates returned for {symbol}")

    merged = pd.concat(batches, axis=0, ignore_index=True)
    merged = merged.sort_values("timestamp", kind="mergesort").drop_duplicates(subset=["timestamp"], keep="last")
    merged = merged.tail(max(1, int(limit))).set_index("timestamp")
    return merged.rename(columns={"fundingRate": "funding_rate"})[["funding_rate"]]


def fetch_binance_open_interest_hist(symbol: str, period: str = "1h", limit: int = 1200) -> pd.DataFrame:
    requested = max(1, int(limit))
    batches: list[pd.DataFrame] = []
    end_time: int | None = None

    with httpx.Client(timeout=20.0) as client:
        while requested > 0:
            batch_limit = min(500, requested)
            params: dict[str, Any] = {"symbol": symbol, "period": period, "limit": batch_limit}
            if end_time is not None:
                params["endTime"] = int(end_time)
            response = client.get(BINANCE_OI_HIST_URL, params=params)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, list) or not payload:
                break

            frame = pd.DataFrame(payload)
            frame = frame[["timestamp", "sumOpenInterest"]].copy()
            frame["timestamp"] = frame["timestamp"].astype("int64")
            frame["sumOpenInterest"] = frame["sumOpenInterest"].astype("float64")
            frame["dt"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
            batches.append(frame[["dt", "sumOpenInterest"]].rename(columns={"dt": "timestamp"}))

            requested -= len(frame)
            oldest_time = int(frame["timestamp"].min())
            next_end = oldest_time - 1
            if end_time is not None and next_end >= end_time:
                break
            end_time = next_end
            if len(frame) < batch_limit:
                break

    if not batches:
        raise ValueError(f"No Binance open interest history returned for {symbol}")

    merged = pd.concat(batches, axis=0, ignore_index=True)
    merged = merged.sort_values("timestamp", kind="mergesort").drop_duplicates(subset=["timestamp"], keep="last")
    merged = merged.tail(max(1, int(limit))).set_index("timestamp")
    return merged.rename(columns={"sumOpenInterest": "open_interest"})[["open_interest"]]


def build_aligned_frame(symbol: str, interval: str, *, limit: int = 1200) -> pd.DataFrame:
    spot = fetch_binance_spot_klines(symbol=symbol, interval=interval, limit=limit)
    funding_raw = fetch_binance_funding_rates(symbol=symbol, limit=max(limit, 1000))
    oi = fetch_binance_open_interest_hist(symbol=symbol, period=interval, limit=limit)

    funding = funding_raw.reindex(spot.index, method="ffill")
    aligned = spot.join(funding, how="inner").join(oi, how="inner")
    aligned = aligned.sort_index(kind="mergesort").dropna()
    if aligned.empty:
        raise ValueError("Aligned spot/funding/open-interest frame is empty")
    return aligned


def _metrics_delta(baseline: BacktestMetrics, overlay: BacktestMetrics) -> dict[str, float]:
    return {
        "sharpe": round(float(overlay.sharpe - baseline.sharpe), 8),
        "cagr": round(float(overlay.cagr - baseline.cagr), 8),
        "trades": int(overlay.trades - baseline.trades),
        "win_rate": round(float(overlay.win_rate - baseline.win_rate), 8),
        "max_drawdown": round(float(overlay.max_drawdown - baseline.max_drawdown), 8),
    }


def build_report(
    *,
    run_id: str,
    symbol: str,
    interval: str,
    frame: pd.DataFrame,
    baseline_metrics: BacktestMetrics,
    overlay_metrics: BacktestMetrics,
    stress: pd.Series,
) -> dict[str, Any]:
    overlay_beats_baseline = overlay_metrics.sharpe > baseline_metrics.sharpe
    overlay_positive = overlay_metrics.sharpe > 0
    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "run_id": run_id,
        "series": {
            "symbol": symbol,
            "interval": interval,
            "baseline_strategy": "btc_spot_swing_trend",
            "overlay_strategy": "btc_derivatives_positioning_stress_overlay",
        },
        "coverage": {
            "aligned_rows": int(len(frame)),
            "start": frame.index.min().isoformat(),
            "end": frame.index.max().isoformat(),
            "stress_count": int(stress.sum()),
            "stress_ratio": round(float(stress.mean()), 8),
        },
        "comparison": {
            "baseline": metrics_to_dict(baseline_metrics),
            "overlay": metrics_to_dict(overlay_metrics),
            "delta_overlay_minus_baseline": _metrics_delta(baseline_metrics, overlay_metrics),
        },
        "decision": {
            "pass": bool(overlay_beats_baseline and overlay_positive),
            "overlay_beats_baseline": bool(overlay_beats_baseline),
            "overlay_positive_sharpe": bool(overlay_positive),
            "kill_rule": "discard if overlay Sharpe <= baseline Sharpe; treat overlay Sharpe <= 0 as stronger failure",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    baseline = report["comparison"]["baseline"]
    overlay = report["comparison"]["overlay"]
    delta = report["comparison"]["delta_overlay_minus_baseline"]
    decision = report["decision"]
    coverage = report["coverage"]
    lines = [
        "# BTC Derivatives Positioning Stress Validation",
        "",
        "## Coverage",
        f"- run_id: {report['run_id']}",
        f"- symbol: {report['series']['symbol']}",
        f"- interval: {report['series']['interval']}",
        f"- aligned_rows: {coverage['aligned_rows']}",
        f"- start: {coverage['start']}",
        f"- end: {coverage['end']}",
        f"- stress_count: {coverage['stress_count']}",
        f"- stress_ratio: {coverage['stress_ratio']}",
        "",
        "## Baseline",
        f"- sharpe: {baseline['sharpe']}",
        f"- cagr: {baseline['cagr']}",
        f"- trades: {baseline['trades']}",
        f"- win_rate: {baseline['win_rate']}",
        f"- max_drawdown: {baseline['max_drawdown']}",
        "",
        "## Overlay",
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
        "## Decision",
        f"- pass: {decision['pass']}",
        f"- overlay_beats_baseline: {decision['overlay_beats_baseline']}",
        f"- overlay_positive_sharpe: {decision['overlay_positive_sharpe']}",
        f"- kill_rule: {decision['kill_rule']}",
    ]
    return "\n".join(lines) + "\n"


def run_validation(
    *,
    analysis_dir: Path,
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    limit: int = 1200,
    rolling_window: int = 720,
    quantile_level: float = 0.9,
    fee_bps: float = 8.0,
    slippage_bps: float = 8.0,
) -> PositioningStressArtifacts:
    run_id = str(uuid.uuid4())
    frame = build_aligned_frame(symbol=symbol, interval=interval, limit=limit)
    baseline_signal, overlay_signal, stress = compute_overlay_signals(
        frame,
        rolling_window=rolling_window,
        quantile_level=quantile_level,
    )

    runner = BacktestRunner(seed=42)
    base_frame = frame[["open", "high", "low", "close", "volume"]]
    baseline_metrics = runner.run(
        _PrecomputedSignalStrategy(baseline_signal),
        base_frame,
        fee_bps=fee_bps,
        slippage_bps=slippage_bps,
    )
    overlay_metrics = runner.run(
        _PrecomputedSignalStrategy(overlay_signal),
        base_frame,
        fee_bps=fee_bps,
        slippage_bps=slippage_bps,
    )

    report = build_report(
        run_id=run_id,
        symbol=symbol,
        interval=interval,
        frame=frame,
        baseline_metrics=baseline_metrics,
        overlay_metrics=overlay_metrics,
        stress=stress,
    )

    analysis_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = analysis_dir / f"btc_derivatives_positioning_stress_{stamp}.json"
    md_path = analysis_dir / f"btc_derivatives_positioning_stress_{stamp}.md"
    csv_path = analysis_dir / f"btc_derivatives_positioning_stress_frame_{stamp}.csv"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    frame.assign(
        baseline_signal=baseline_signal,
        overlay_signal=overlay_signal,
        positioning_stress=stress.astype(bool),
    ).to_csv(csv_path, index_label="timestamp")

    return PositioningStressArtifacts(
        run_id=run_id,
        report_json_path=json_path,
        report_md_path=md_path,
        frame_csv_path=csv_path,
        report=report,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate BTC derivatives positioning stress as a cash-default overlay.")
    parser.add_argument("--analysis-dir", default="analysis_results")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--limit", type=int, default=1200)
    parser.add_argument("--rolling-window", type=int, default=720)
    parser.add_argument("--quantile-level", type=float, default=0.9)
    parser.add_argument("--fee-bps", type=float, default=8.0)
    parser.add_argument("--slippage-bps", type=float, default=8.0)
    args = parser.parse_args()

    artifacts = run_validation(
        analysis_dir=Path(args.analysis_dir),
        symbol=args.symbol,
        interval=args.interval,
        limit=args.limit,
        rolling_window=args.rolling_window,
        quantile_level=args.quantile_level,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
    )
    print(
        json.dumps(
            {
                "run_id": artifacts.run_id,
                "report_json_path": str(artifacts.report_json_path),
                "report_md_path": str(artifacts.report_md_path),
                "frame_csv_path": str(artifacts.frame_csv_path),
                "comparison": artifacts.report["comparison"],
                "decision": artifacts.report["decision"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
