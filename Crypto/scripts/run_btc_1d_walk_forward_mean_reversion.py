from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.backtesting.overfitting import OverfittingEvaluator
from app.domains.backtesting.runner import BacktestRunner, metrics_to_dict
from app.domains.market_data import BinanceDataProvider
from app.domains.strategy.loader import load_strategy


@dataclass(frozen=True)
class Btc1dMeanReversionWalkForwardConfig:
    symbol: str = "BTCUSDT"
    interval: str = "1d"
    periods: int = 2200
    fee_bps: float = 8.0
    slippage_bps: float = 8.0
    split_ratio: float = 0.7
    walk_forward_windows: int = 5
    sensitivity_limit: float = 0.35
    allow_synthetic_ohlcv_fallback: bool = False
    candidate_label: str = "btc_1d_mean_reversion_w20_z1.0"
    window: int = 20
    z_threshold: float = 1.0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run BTC 1d walk-forward diagnostic for the mean reversion strategy.")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--walk-forward-windows", type=int, default=5)
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--z-threshold", type=float, default=1.0)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    return parser


def parse_args(argv: list[str] | None = None) -> Btc1dMeanReversionWalkForwardConfig:
    args = build_parser().parse_args(argv)
    return Btc1dMeanReversionWalkForwardConfig(
        symbol=args.symbol,
        interval=args.interval,
        periods=args.periods,
        walk_forward_windows=args.walk_forward_windows,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
        candidate_label=f"btc_1d_mean_reversion_w{args.window}_z{args.z_threshold}",
        window=args.window,
        z_threshold=args.z_threshold,
    )


def interval_delta(interval: str):
    import pandas as pd

    mapping = {
        "1h": pd.Timedelta(hours=1),
        "4h": pd.Timedelta(hours=4),
        "1d": pd.Timedelta(days=1),
    }
    if interval not in mapping:
        raise ValueError(f"Unsupported interval: {interval}")
    return mapping[interval]


def build_synthetic_ohlcv(interval: str, periods: int):
    import pandas as pd

    delta = interval_delta(interval)
    start = pd.Timestamp("2020-01-01", tz="UTC")
    idx = pd.date_range(start=start, periods=periods, freq=delta)
    close = pd.Series(
        [
            100.0
            + (i * 0.2)
            + ((i % 17) * 0.4)
            - ((i % 9) * 0.35)
            + (((i // 120) % 2) * 3.0)
            - (((i // 240) % 2) * 2.0)
            for i in range(periods)
        ],
        index=idx,
        dtype=float,
    )
    frame = pd.DataFrame(index=idx)
    frame["close"] = close
    frame["open"] = frame["close"].shift(1).fillna(frame["close"])
    frame["high"] = frame[["open", "close"]].max(axis=1) + 1.5
    frame["low"] = frame[["open", "close"]].min(axis=1) - 1.5
    frame["volume"] = 1000.0
    return frame[["open", "high", "low", "close", "volume"]]


def load_ohlcv(config: Btc1dMeanReversionWalkForwardConfig):
    import pandas as pd

    end_ts = pd.Timestamp.now(tz="UTC").floor(config.interval)
    start_ts = end_ts - (interval_delta(config.interval) * int(config.periods))
    try:
        return BinanceDataProvider().get_ohlcv(
            symbol=config.symbol,
            interval=config.interval,
            start_ts=start_ts.to_pydatetime(),
            end_ts=end_ts.to_pydatetime(),
        )
    except Exception:
        if not config.allow_synthetic_ohlcv_fallback:
            raise
        return build_synthetic_ohlcv(config.interval, config.periods)


def parameter_drift_details(
    *,
    strategy: Any,
    runner: BacktestRunner,
    ohlcv,
    params: dict[str, Any],
    fee_bps: float,
    slippage_bps: float,
) -> list[dict[str, Any]]:
    base_metrics = metrics_to_dict(runner.run(strategy, ohlcv, params, fee_bps=fee_bps, slippage_bps=slippage_bps))
    rows: list[dict[str, Any]] = []
    for name, value in params.items():
        if not isinstance(value, (int, float)):
            continue
        if abs(float(value)) <= 1e-12:
            continue
        delta = max(1e-9, abs(float(value)) * 0.1)
        variants: list[dict[str, Any]] = []
        max_drift = 0.0
        for direction, candidate in (("down", float(value) - delta), ("up", float(value) + delta)):
            test_params = dict(params)
            test_params[name] = candidate
            metrics = metrics_to_dict(runner.run(strategy, ohlcv, test_params, fee_bps=fee_bps, slippage_bps=slippage_bps))
            sharpe_drift = abs(float(metrics["sharpe"]) - float(base_metrics["sharpe"])) / max(
                1e-6, abs(float(base_metrics["sharpe"])) + 1e-6
            )
            cagr_drift = abs(float(metrics["cagr"]) - float(base_metrics["cagr"])) / max(
                1e-6, abs(float(base_metrics["cagr"])) + 1e-6
            )
            win_rate_drift = abs(float(metrics["win_rate"]) - float(base_metrics["win_rate"]))
            drift = max(sharpe_drift, cagr_drift, win_rate_drift)
            max_drift = max(max_drift, drift)
            variants.append(
                {
                    "direction": direction,
                    "candidate_value": round(float(candidate), 8),
                    "drift": round(float(drift), 8),
                    "sharpe": float(metrics["sharpe"]),
                    "cagr": float(metrics["cagr"]),
                    "max_drawdown": float(metrics["max_drawdown"]),
                }
            )
        rows.append(
            {
                "parameter": name,
                "base_value": round(float(value), 8),
                "max_drift": round(float(max_drift), 8),
                "variants": variants,
            }
        )
    rows.sort(key=lambda item: (-float(item["max_drift"]), str(item["parameter"])))
    return rows


def build_summary(payload: dict[str, Any]) -> str:
    overfitting = payload["overfitting"]
    top_drift = payload["parameter_drifts"][:5]
    lines = [
        "# BTC 1d Mean Reversion Walk-Forward Diagnostic",
        "",
        f"- Symbol: `{payload['config']['symbol']}`",
        f"- Interval: `{payload['config']['interval']}`",
        f"- Candidate: `{payload['config']['candidate_label']}`",
        f"- Base Sharpe: `{payload['base_metrics']['sharpe']:.4f}`",
        f"- Base CAGR: `{payload['base_metrics']['cagr']:.4f}`",
        f"- Base MDD: `{payload['base_metrics']['max_drawdown']:.4f}`",
        f"- IS Sharpe: `{overfitting['is_metrics'].get('sharpe', 0.0):.4f}`",
        f"- OOS Sharpe: `{overfitting['oos_metrics'].get('sharpe', 0.0):.4f}`",
        f"- Sensitivity Drift: `{overfitting['sensitivity_max_drift']:.4f}`",
        f"- Unstable Parameters: `{', '.join(overfitting['unstable_parameters']) or 'none'}`",
        "",
        "## Walk-Forward",
    ]
    for row in overfitting["walk_forward"]:
        metrics = row.get("metrics", {})
        lines.append(
            f"- Window {row.get('window')}: Sharpe `{float(metrics.get('sharpe', 0.0)):.4f}`, "
            f"CAGR `{float(metrics.get('cagr', 0.0)):.4f}`, MDD `{float(metrics.get('max_drawdown', 0.0)):.4f}`"
        )
    lines.extend(["", "## Top Drift Parameters"])
    for row in top_drift:
        lines.append(f"- `{row['parameter']}`: max drift `{row['max_drift']:.4f}` from base `{row['base_value']}`")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv)
    runner = BacktestRunner(seed=42)
    strategy = load_strategy("mean_reversion", strategies_dir=Path("strategies"))
    ohlcv = load_ohlcv(config)
    parameters = {"window": config.window, "z_threshold": config.z_threshold}
    base_metrics = metrics_to_dict(runner.run(strategy, ohlcv, parameters, fee_bps=config.fee_bps, slippage_bps=config.slippage_bps))
    overfitting = OverfittingEvaluator(
        runner=runner,
        split_ratio=config.split_ratio,
        enable_walk_forward=True,
        walk_forward_windows=config.walk_forward_windows,
        sensitivity_limit=config.sensitivity_limit,
    ).evaluate(
        strategy,
        ohlcv,
        parameters,
        fee_bps=config.fee_bps,
        slippage_bps=config.slippage_bps,
    )
    parameter_drifts = parameter_drift_details(
        strategy=strategy,
        runner=runner,
        ohlcv=ohlcv,
        params=parameters,
        fee_bps=config.fee_bps,
        slippage_bps=config.slippage_bps,
    )
    payload = {
        "run_id": f"btc-1d-mean-reversion-walkdiag-{datetime.now(tz=UTC).strftime('%Y%m%dT%H%M%SZ')}",
        "config": asdict(config),
        "parameters": parameters,
        "base_metrics": base_metrics,
        "overfitting": {
            "passed": overfitting.passed,
            "summary": overfitting.summary,
            "is_metrics": overfitting.is_metrics,
            "oos_metrics": overfitting.oos_metrics,
            "walk_forward": overfitting.walk_forward,
            "sensitivity_max_drift": overfitting.sensitivity_max_drift,
            "unstable_parameters": overfitting.unstable_parameters,
        },
        "parameter_drifts": parameter_drifts,
    }
    summary = build_summary(payload)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    analysis_json = Path("analysis_results") / f"btc_1d_mean_reversion_walk_forward_diagnostic_{stamp}.json"
    analysis_md = Path("analysis_results") / f"btc_1d_mean_reversion_walk_forward_diagnostic_{stamp}.md"
    analysis_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    analysis_md.write_text(summary, encoding="utf-8")
    print(json.dumps({"analysis_result_json": str(analysis_json), "analysis_result_md": str(analysis_md)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
