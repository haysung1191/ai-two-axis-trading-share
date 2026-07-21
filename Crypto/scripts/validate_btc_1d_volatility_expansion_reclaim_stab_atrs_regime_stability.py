from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.backtesting.runner import BacktestRunner, metrics_to_dict
from app.domains.market_data import BinanceDataProvider
from app.domains.strategy.loader import load_strategy


@dataclass(frozen=True)
class RegimeStabilityConfig:
    symbol: str = "BTCUSDT"
    interval: str = "1d"
    periods: int = 2200
    fee_bps: float = 8.0
    slippage_bps: float = 8.0
    allow_synthetic_ohlcv_fallback: bool = False


PRACTICAL_PARAMS: dict[str, Any] = {
    "trend_ema_window": 72,
    "breakout_window": 18,
    "atr_window": 11,
    "atr_expansion_window": 5,
    "min_atr_expansion_ratio": 1.12,
    "volume_lookback": 18,
    "min_volume_ratio": 1.12,
    "reclaim_buffer_ratio": 0.12,
    "stop_ema_window": 16,
    "max_hold_bars": 34,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run leave-one-year-out and regime-slice stability checks for the BTC practical leader.")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--fee-bps", type=float, default=8.0)
    parser.add_argument("--slippage-bps", type=float, default=8.0)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    return parser


def parse_args(argv: list[str] | None = None) -> RegimeStabilityConfig:
    args = build_parser().parse_args(argv)
    return RegimeStabilityConfig(
        symbol=args.symbol,
        interval=args.interval,
        periods=args.periods,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
    )


def _interval_delta(interval: str) -> pd.Timedelta:
    mapping = {
        "1h": pd.Timedelta(hours=1),
        "4h": pd.Timedelta(hours=4),
        "1d": pd.Timedelta(days=1),
    }
    if interval not in mapping:
        raise ValueError(f"Unsupported interval: {interval}")
    return mapping[interval]


def _build_synthetic_ohlcv(interval: str, periods: int) -> pd.DataFrame:
    delta = _interval_delta(interval)
    start = pd.Timestamp("2020-01-01", tz="UTC")
    idx = pd.date_range(start=start, periods=periods, freq=delta)
    close = pd.Series(
        [
            100.0
            + (i * 0.55)
            + ((i % 37) * 0.18)
            + (((i // 120) % 2) * 8.0)
            - (((i // 260) % 2) * 5.0)
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


def _load_ohlcv(config: RegimeStabilityConfig) -> pd.DataFrame:
    end_ts = pd.Timestamp.now(tz="UTC").floor(config.interval)
    start_ts = end_ts - (_interval_delta(config.interval) * int(config.periods))
    provider = BinanceDataProvider()
    try:
        return provider.get_ohlcv(
            symbol=config.symbol,
            interval=config.interval,
            start_ts=start_ts.to_pydatetime(),
            end_ts=end_ts.to_pydatetime(),
        )
    except Exception:
        if not config.allow_synthetic_ohlcv_fallback:
            raise
        return _build_synthetic_ohlcv(config.interval, config.periods)


def _summarize_metrics(metrics: dict[str, Any]) -> dict[str, float]:
    return {
        "sharpe": float(metrics["sharpe"]),
        "cagr": float(metrics["cagr"]),
        "max_drawdown": float(metrics["max_drawdown"]),
        "win_rate": float(metrics["win_rate"]),
        "trades": int(metrics["trades"]),
    }


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# BTC Practical Leader Regime Stability",
        "",
        "- Candidate: `volatility_expansion_reclaim lower_atr_window_tighter_stop`",
        f"- Symbol: `{report['config']['symbol']}`",
        f"- Interval: `{report['config']['interval']}`",
        f"- Periods: `{report['config']['periods']}`",
        "",
        "## Base",
        "",
        f"- Sharpe: `{report['base_metrics']['sharpe']:.4f}`",
        f"- CAGR: `{report['base_metrics']['cagr'] * 100:.2f}%`",
        f"- MDD: `{report['base_metrics']['max_drawdown'] * 100:.2f}%`",
        "",
        "## Regimes",
        "",
    ]
    for name, metrics in report["regime_metrics"]["regimes"].items():
        lines.append(
            f"- {name} | Sharpe `{metrics['sharpe']:.4f}` | MDD `{metrics['max_drawdown'] * 100:.2f}%`"
        )
    lines.extend(["", "## Leave-One-Year-Out", ""])
    for row in report["leave_one_year_out"]["runs"]:
        lines.append(
            f"- exclude {row['excluded_year']} | Sharpe `{row['sharpe']:.4f}` | CAGR `{row['cagr'] * 100:.2f}%` | MDD `{row['max_drawdown'] * 100:.2f}%` | trades `{row['trades']}`"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv)
    ohlcv = _load_ohlcv(config)
    strategy = load_strategy("btc_1d_volatility_expansion_reclaim_stab_atrs", strategies_dir=Path("strategies"))
    runner = BacktestRunner(seed=42)

    base = metrics_to_dict(
        runner.run(
            strategy,
            ohlcv,
            PRACTICAL_PARAMS,
            fee_bps=config.fee_bps,
            slippage_bps=config.slippage_bps,
        )
    )
    regime_report = runner.evaluate_regimes(
        strategy,
        ohlcv,
        PRACTICAL_PARAMS,
        fee_bps=config.fee_bps,
        slippage_bps=config.slippage_bps,
    )
    regime_metrics: dict[str, dict[str, float]] = {}
    for regime_name in sorted(regime_report["sharpe_by_regime"].keys()):
        regime_frame = runner._split_by_regime(ohlcv)[regime_name]
        regime_base = metrics_to_dict(
            runner.run(
                strategy,
                regime_frame,
                PRACTICAL_PARAMS,
                fee_bps=config.fee_bps,
                slippage_bps=config.slippage_bps,
            )
        )
        regime_metrics[regime_name] = _summarize_metrics(regime_base)

    leave_runs: list[dict[str, Any]] = []
    years = sorted({int(ts.year) for ts in ohlcv.index})
    for year in years:
        subset = ohlcv[ohlcv.index.year != year].copy()
        if len(subset) < 300:
            continue
        metrics = metrics_to_dict(
            runner.run(
                strategy,
                subset,
                PRACTICAL_PARAMS,
                fee_bps=config.fee_bps,
                slippage_bps=config.slippage_bps,
            )
        )
        leave_runs.append(
            {
                "excluded_year": int(year),
                **_summarize_metrics(metrics),
            }
        )
    leave_runs.sort(key=lambda item: int(item["excluded_year"]))

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "candidate": "volatility_expansion_reclaim_lower_atr_window_tighter_stop",
        "config": asdict(config),
        "parameters": PRACTICAL_PARAMS,
        "base_metrics": _summarize_metrics(base),
        "regime_metrics": {
            "sharpe_regime_std": float(regime_report["sharpe_regime_std"]),
            "regimes": regime_metrics,
        },
        "leave_one_year_out": {
            "runs": leave_runs,
            "worst_sharpe_year": min(leave_runs, key=lambda item: float(item["sharpe"]))["excluded_year"] if leave_runs else None,
            "worst_cagr_year": min(leave_runs, key=lambda item: float(item["cagr"]))["excluded_year"] if leave_runs else None,
            "worst_mdd_year": max(leave_runs, key=lambda item: float(item["max_drawdown"]))["excluded_year"] if leave_runs else None,
        },
    }

    analysis_dir = ROOT / "analysis_results"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = analysis_dir / f"btc_1d_volatility_expansion_reclaim_stab_atrs_regime_stability_{stamp}.json"
    md_path = analysis_dir / f"btc_1d_volatility_expansion_reclaim_stab_atrs_regime_stability_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report_md_path": str(md_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
