from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.bithumb_client import BithumbPublicClient


BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"


@dataclass(frozen=True)
class CandidateAlphaArtifacts:
    report_json_path: Path
    report_md_path: Path
    aligned_frame_csv_path: Path
    report: dict[str, Any]


def _bithumb_rows_to_frame(rows: list[tuple[int, float, float, float, float, float]]) -> pd.DataFrame:
    if not rows:
        raise ValueError("No Bithumb candles returned")
    frame = pd.DataFrame(rows, columns=["open_time", "open", "high", "low", "close", "volume"])
    frame["timestamp"] = pd.to_datetime(frame["open_time"], unit="ms", utc=True)
    frame = frame.sort_values("timestamp", kind="mergesort").drop_duplicates(subset=["timestamp"], keep="first")
    frame = frame.set_index("timestamp")
    return frame[["open", "high", "low", "close", "volume"]].astype(float)


def fetch_bithumb_1h(symbol: str) -> pd.DataFrame:
    client = BithumbPublicClient()
    try:
        rows = client.fetch_1h_candles(symbol)
    finally:
        client.close()
    return _bithumb_rows_to_frame(rows)


def fetch_binance_1h(symbol: str, limit: int = 1000) -> pd.DataFrame:
    requested = max(1, int(limit))
    collected: list[pd.DataFrame] = []
    end_time: int | None = None

    with httpx.Client(timeout=20.0) as client:
        while requested > 0:
            batch_limit = min(1000, requested)
            params: dict[str, Any] = {"symbol": symbol, "interval": "1h", "limit": batch_limit}
            if end_time is not None:
                params["endTime"] = int(end_time)
            response = client.get(BINANCE_KLINES_URL, params=params)
            response.raise_for_status()
            payload = response.json()

            if not isinstance(payload, list) or not payload:
                break

            frame = pd.DataFrame(payload)
            frame = frame.iloc[:, :6]
            frame.columns = ["open_time", "open", "high", "low", "close", "volume"]
            frame["open_time"] = frame["open_time"].astype("int64")
            for column in ["open", "high", "low", "close", "volume"]:
                frame[column] = frame[column].astype("float64")
            frame["timestamp"] = pd.to_datetime(frame["open_time"], unit="ms", utc=True)
            frame = frame.sort_values("timestamp", kind="mergesort").drop_duplicates(subset=["timestamp"], keep="first")
            collected.append(frame[["timestamp", "open", "high", "low", "close", "volume"]])

            requested -= len(frame)
            oldest_open_time = int(frame["open_time"].min())
            next_end_time = oldest_open_time - 1
            if end_time is not None and next_end_time >= end_time:
                break
            end_time = next_end_time

            if len(frame) < batch_limit:
                break

    if not collected:
        raise ValueError(f"No Binance klines returned for {symbol}")

    merged = pd.concat(collected, axis=0, ignore_index=True)
    merged = merged.sort_values("timestamp", kind="mergesort").drop_duplicates(subset=["timestamp"], keep="first")
    merged = merged.tail(max(1, int(limit)))
    merged = merged.set_index("timestamp")
    return merged[["open", "high", "low", "close", "volume"]]


def align_candidate_alpha_inputs(
    bithumb_krw_btc: pd.DataFrame,
    bithumb_krw_usdt: pd.DataFrame,
    binance_btcusdt: pd.DataFrame,
    *,
    max_rows: int = 1000,
) -> pd.DataFrame:
    frames = {
        "krw_btc_close": bithumb_krw_btc["close"].rename("krw_btc_close"),
        "krw_btc_volume": bithumb_krw_btc["volume"].rename("krw_btc_volume"),
        "krw_usdt_close": bithumb_krw_usdt["close"].rename("krw_usdt_close"),
        "global_btc_close": binance_btcusdt["close"].rename("global_btc_close"),
    }
    aligned = pd.concat(frames.values(), axis=1, join="inner").sort_index(kind="mergesort")
    aligned = aligned[~aligned.index.duplicated(keep="first")]
    if max_rows > 0:
        aligned = aligned.tail(max_rows)
    if aligned.empty:
        raise ValueError("Aligned Candidate Alpha frame is empty")
    return aligned


def compute_candidate_alpha_frame(aligned: pd.DataFrame) -> pd.DataFrame:
    frame = aligned.copy()
    frame["dislocation"] = ((frame["krw_btc_close"] / frame["krw_usdt_close"]) - frame["global_btc_close"]) / frame["global_btc_close"]
    frame["delta_dislocation_1h"] = frame["dislocation"].diff()
    frame["dislocation_std_72"] = frame["dislocation"].rolling(window=72, min_periods=72).std()
    frame["delta_dislocation_std_72"] = frame["delta_dislocation_1h"].rolling(window=72, min_periods=72).std()
    frame["krw_usdt_return_1h"] = frame["krw_usdt_close"].pct_change()
    frame["krw_usdt_abs_return_mean_72"] = frame["krw_usdt_return_1h"].abs().rolling(window=72, min_periods=72).mean()

    tradable_mask = (
        frame["dislocation"].abs() <= frame["dislocation_std_72"] * 1.5
    ) & (
        frame["delta_dislocation_1h"].abs() <= frame["delta_dislocation_std_72"] * 2.0
    ) & (
        frame["krw_usdt_return_1h"].abs() <= frame["krw_usdt_abs_return_mean_72"] * 2.0
    )
    frame["tradable_regime"] = tradable_mask.fillna(False)
    frame["avoidance_regime"] = ~frame["tradable_regime"]

    close = frame["krw_btc_close"].astype(float)
    frame["forward_return_1h"] = close.shift(-1) / close - 1.0
    frame["forward_return_4h"] = close.shift(-4) / close - 1.0

    log_return = np.log(close).diff()
    frame["forward_vol_1h"] = log_return.shift(-1).abs()
    future_sq = pd.concat([(log_return.shift(-step) ** 2).rename(f"sq_{step}") for step in range(1, 5)], axis=1)
    frame["forward_vol_4h"] = np.sqrt(future_sq.mean(axis=1))

    return frame


def _regime_stats(frame: pd.DataFrame, mask: pd.Series) -> dict[str, Any]:
    subset = frame.loc[mask].copy()
    subset = subset.dropna(
        subset=[
            "forward_return_1h",
            "forward_return_4h",
            "forward_vol_1h",
            "forward_vol_4h",
        ]
    )
    if subset.empty:
        return {
            "count": 0,
            "mean_forward_return_1h": None,
            "median_forward_return_1h": None,
            "mean_forward_return_4h": None,
            "median_forward_return_4h": None,
            "mean_forward_vol_1h": None,
            "mean_forward_vol_4h": None,
        }
    return {
        "count": int(len(subset)),
        "mean_forward_return_1h": float(subset["forward_return_1h"].mean()),
        "median_forward_return_1h": float(subset["forward_return_1h"].median()),
        "mean_forward_return_4h": float(subset["forward_return_4h"].mean()),
        "median_forward_return_4h": float(subset["forward_return_4h"].median()),
        "mean_forward_vol_1h": float(subset["forward_vol_1h"].mean()),
        "mean_forward_vol_4h": float(subset["forward_vol_4h"].mean()),
    }


def build_candidate_alpha_report(frame: pd.DataFrame) -> dict[str, Any]:
    valid = frame.dropna(
        subset=[
            "dislocation_std_72",
            "delta_dislocation_std_72",
            "krw_usdt_abs_return_mean_72",
            "forward_return_1h",
            "forward_return_4h",
            "forward_vol_1h",
            "forward_vol_4h",
        ]
    )
    tradable_mask = valid["tradable_regime"].astype(bool)
    avoidance_mask = valid["avoidance_regime"].astype(bool)
    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "series": {
            "domestic_market": "Bithumb KRW spot",
            "global_reference_market": "Binance USDT spot",
            "asset_pair": "KRW-BTC / BTCUSDT",
            "interval": "1h",
        },
        "coverage": {
            "aligned_rows": int(len(frame)),
            "valid_rows": int(len(valid)),
            "start": valid.index.min().isoformat() if not valid.empty else None,
            "end": valid.index.max().isoformat() if not valid.empty else None,
        },
        "dislocation_summary": {
            "mean": float(valid["dislocation"].mean()) if not valid.empty else None,
            "median": float(valid["dislocation"].median()) if not valid.empty else None,
            "std": float(valid["dislocation"].std()) if not valid.empty else None,
            "abs_mean": float(valid["dislocation"].abs().mean()) if not valid.empty else None,
        },
        "regime_comparison": {
            "tradable": _regime_stats(valid, tradable_mask),
            "avoidance": _regime_stats(valid, avoidance_mask),
        },
    }


def render_candidate_alpha_markdown(report: dict[str, Any]) -> str:
    tradable = report["regime_comparison"]["tradable"]
    avoidance = report["regime_comparison"]["avoidance"]
    coverage = report["coverage"]
    dislocation = report["dislocation_summary"]
    lines = [
        "# Candidate Alpha Regime Validation",
        "",
        "## Coverage",
        f"- interval: {report['series']['interval']}",
        f"- aligned_rows: {coverage['aligned_rows']}",
        f"- valid_rows: {coverage['valid_rows']}",
        f"- start: {coverage['start']}",
        f"- end: {coverage['end']}",
        "",
        "## Dislocation Summary",
        f"- mean: {dislocation['mean']}",
        f"- median: {dislocation['median']}",
        f"- std: {dislocation['std']}",
        f"- abs_mean: {dislocation['abs_mean']}",
        "",
        "## Regime Comparison",
        "### Tradable",
        f"- count: {tradable['count']}",
        f"- mean_forward_return_1h: {tradable['mean_forward_return_1h']}",
        f"- median_forward_return_1h: {tradable['median_forward_return_1h']}",
        f"- mean_forward_return_4h: {tradable['mean_forward_return_4h']}",
        f"- median_forward_return_4h: {tradable['median_forward_return_4h']}",
        f"- mean_forward_vol_1h: {tradable['mean_forward_vol_1h']}",
        f"- mean_forward_vol_4h: {tradable['mean_forward_vol_4h']}",
        "",
        "### Avoidance",
        f"- count: {avoidance['count']}",
        f"- mean_forward_return_1h: {avoidance['mean_forward_return_1h']}",
        f"- median_forward_return_1h: {avoidance['median_forward_return_1h']}",
        f"- mean_forward_return_4h: {avoidance['mean_forward_return_4h']}",
        f"- median_forward_return_4h: {avoidance['median_forward_return_4h']}",
        f"- mean_forward_vol_1h: {avoidance['mean_forward_vol_1h']}",
        f"- mean_forward_vol_4h: {avoidance['mean_forward_vol_4h']}",
    ]
    return "\n".join(lines) + "\n"


def run_candidate_alpha_regime_report(output_dir: Path, *, max_rows: int = 1000) -> CandidateAlphaArtifacts:
    krw_btc = fetch_bithumb_1h("BTC")
    krw_usdt = fetch_bithumb_1h("USDT")
    global_btc = fetch_binance_1h("BTCUSDT", limit=max(1000, max_rows))

    aligned = align_candidate_alpha_inputs(
        bithumb_krw_btc=krw_btc,
        bithumb_krw_usdt=krw_usdt,
        binance_btcusdt=global_btc,
        max_rows=max_rows,
    )
    analysis_frame = compute_candidate_alpha_frame(aligned)
    report = build_candidate_alpha_report(analysis_frame)

    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    report_json_path = output_dir / f"candidate_alpha_regime_report_{stamp}.json"
    report_md_path = output_dir / f"candidate_alpha_regime_report_{stamp}.md"
    aligned_frame_csv_path = output_dir / f"candidate_alpha_regime_frame_{stamp}.csv"

    report_json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    report_md_path.write_text(render_candidate_alpha_markdown(report), encoding="utf-8")
    analysis_frame.to_csv(aligned_frame_csv_path, encoding="utf-8")

    return CandidateAlphaArtifacts(
        report_json_path=report_json_path,
        report_md_path=report_md_path,
        aligned_frame_csv_path=aligned_frame_csv_path,
        report=report,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the first Candidate Alpha dislocation-regime validation report.")
    parser.add_argument("--output-dir", default="analysis_results")
    parser.add_argument("--max-rows", type=int, default=1000)
    args = parser.parse_args()

    artifacts = run_candidate_alpha_regime_report(Path(args.output_dir), max_rows=max(200, int(args.max_rows)))
    print(
        json.dumps(
            {
                "report_json_path": str(artifacts.report_json_path),
                "report_md_path": str(artifacts.report_md_path),
                "aligned_frame_csv_path": str(artifacts.aligned_frame_csv_path),
                "coverage": artifacts.report["coverage"],
                "regime_comparison": artifacts.report["regime_comparison"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
