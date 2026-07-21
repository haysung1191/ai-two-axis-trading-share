from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from random import Random
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.market_data import BinanceDataProvider
from app.domains.strategy.loader import load_strategy


@dataclass(frozen=True)
class BenchmarkStatsConfig:
    interval: str = "1d"
    periods: int = 2200
    fee_bps: float = 8.0
    slippage_bps: float = 8.0
    bootstrap_samples: int = 1000
    bootstrap_block_size: int = 20
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


BENCHMARKS: list[dict[str, Any]] = [
    {
        "label": "buy_and_hold",
        "strategy_name": "btc_1d_buy_and_hold",
        "parameters": {},
    },
    {
        "label": "simple_ma_trend",
        "strategy_name": "btc_1d_simple_ma_trend",
        "parameters": {
            "fast_window": 50,
            "slow_window": 200,
        },
    },
    {
        "label": "simple_breakout",
        "strategy_name": "btc_1d_simple_breakout",
        "parameters": {
            "entry_window": 20,
            "exit_window": 10,
        },
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run paired benchmark statistics for the BTC practical leader on BTC and ETH.")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--fee-bps", type=float, default=8.0)
    parser.add_argument("--slippage-bps", type=float, default=8.0)
    parser.add_argument("--bootstrap-samples", type=int, default=1000)
    parser.add_argument("--bootstrap-block-size", type=int, default=20)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    return parser


def parse_args(argv: list[str] | None = None) -> BenchmarkStatsConfig:
    args = build_parser().parse_args(argv)
    return BenchmarkStatsConfig(
        interval=args.interval,
        periods=args.periods,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        bootstrap_samples=args.bootstrap_samples,
        bootstrap_block_size=args.bootstrap_block_size,
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


def _build_synthetic_ohlcv(symbol: str, interval: str, periods: int) -> pd.DataFrame:
    delta = _interval_delta(interval)
    start = pd.Timestamp("2020-01-01", tz="UTC")
    idx = pd.date_range(start=start, periods=periods, freq=delta)
    base = 100.0 if symbol == "BTCUSDT" else 60.0
    drift = 0.55 if symbol == "BTCUSDT" else 0.42
    close = pd.Series(
        [
            base
            + (i * drift)
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


def _load_ohlcv(symbol: str, config: BenchmarkStatsConfig) -> pd.DataFrame:
    provider = BinanceDataProvider()
    end_ts = pd.Timestamp.now(tz="UTC").floor(config.interval)
    start_ts = end_ts - (_interval_delta(config.interval) * int(config.periods))
    try:
        return provider.get_ohlcv(
            symbol=symbol,
            interval=config.interval,
            start_ts=start_ts.to_pydatetime(),
            end_ts=end_ts.to_pydatetime(),
        )
    except Exception:
        if not config.allow_synthetic_ohlcv_fallback:
            raise
        return _build_synthetic_ohlcv(symbol, config.interval, config.periods)


def _compute_periods_per_year(frame: pd.DataFrame) -> float:
    if len(frame.index) < 2 or not isinstance(frame.index, pd.DatetimeIndex):
        return 252.0
    diffs = frame.index.to_series().diff().dropna()
    if diffs.empty:
        return 252.0
    seconds = float(diffs.median().total_seconds())
    if seconds <= 0:
        return 252.0
    return float((365.25 * 24 * 3600) / seconds)


def _compute_returns(
    strategy_name: str,
    params: dict[str, Any],
    ohlcv: pd.DataFrame,
    *,
    fee_bps: float,
    slippage_bps: float,
) -> pd.Series:
    strategy = load_strategy(strategy_name, strategies_dir=Path("strategies"))
    raw_signals = strategy.generate_signals(ohlcv, params)
    signals = raw_signals.reindex(ohlcv.index).fillna(0.0).clip(lower=-1.0, upper=1.0).astype(float)
    position = signals.shift(1).fillna(0.0)
    period_returns = ohlcv["close"].astype(float).pct_change().fillna(0.0)
    turnover = signals.diff().abs().fillna(signals.abs()).astype(float)
    total_cost_rate = max(0.0, float(fee_bps) + float(slippage_bps)) / 10000.0
    return ((period_returns * position) - (turnover * total_cost_rate)).astype(float)


def _annualized_sharpe(returns: pd.Series, periods_per_year: float) -> float:
    std = float(returns.std(ddof=0))
    if std <= 0:
        return 0.0
    return float((float(returns.mean()) / std) * math.sqrt(periods_per_year))


def _max_drawdown(equity: pd.Series) -> float:
    peaks = equity.cummax()
    drawdown = equity / peaks - 1.0
    return float(abs(drawdown.min()))


def _cagr(equity: pd.Series, periods_per_year: float) -> float:
    periods = max(1, len(equity) - 1)
    years = periods / periods_per_year if periods_per_year > 0 else periods / 252.0
    final_equity = float(equity.iloc[-1])
    if years <= 0:
        return 0.0
    if final_equity <= 0:
        return -1.0
    return float((final_equity ** (1 / years)) - 1.0)


def _block_bootstrap_diff(
    differential: list[float],
    *,
    samples: int,
    block_size: int,
    seed: int = 42,
) -> list[list[float]]:
    if not differential:
        return []
    rng = Random(seed)
    n = len(differential)
    block = max(2, min(block_size, n))
    results: list[list[float]] = []
    for _ in range(samples):
        sample: list[float] = []
        while len(sample) < n:
            start = rng.randrange(0, max(1, n - block + 1))
            sample.extend(differential[start : start + block])
        results.append(sample[:n])
    return results


def _quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * q
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return float(ordered[lower])
    weight = position - lower
    return float((ordered[lower] * (1.0 - weight)) + (ordered[upper] * weight))


def _summarize_strategy(returns: pd.Series, periods_per_year: float) -> dict[str, float]:
    equity = (1.0 + returns).cumprod()
    return {
        "sharpe": round(_annualized_sharpe(returns, periods_per_year), 8),
        "cagr": round(_cagr(equity, periods_per_year), 8),
        "max_drawdown": round(_max_drawdown(equity), 8),
        "equity_end": round(float(equity.iloc[-1]), 8),
    }


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# BTC Practical Leader Paired Benchmark Stats",
        "",
        "- Candidate: `volatility_expansion_reclaim lower_atr_window_tighter_stop`",
        f"- Interval: `{report['config']['interval']}`",
        f"- Periods: `{report['config']['periods']}`",
        "",
    ]
    for symbol_result in report["symbols"]:
        lines.extend(
            [
                f"## {symbol_result['symbol']}",
                "",
                f"- leader | Sharpe `{symbol_result['leader']['sharpe']:.4f}` | CAGR `{symbol_result['leader']['cagr'] * 100:.2f}%` | MDD `{symbol_result['leader']['max_drawdown'] * 100:.2f}%`",
            ]
        )
        for benchmark in symbol_result["benchmarks"]:
            lines.extend(
                [
                    f"- {benchmark['label']} | Sharpe `{benchmark['metrics']['sharpe']:.4f}` | CAGR `{benchmark['metrics']['cagr'] * 100:.2f}%` | MDD `{benchmark['metrics']['max_drawdown'] * 100:.2f}%` | P(diff mean > 0) `{benchmark['paired_bootstrap']['p_diff_mean_gt_0']:.4f}`",
                ]
            )
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv)
    symbol_reports: list[dict[str, Any]] = []
    for symbol in ["BTCUSDT", "ETHUSDT"]:
        ohlcv = _load_ohlcv(symbol, config)
        periods_per_year = _compute_periods_per_year(ohlcv)
        leader_returns = _compute_returns(
            "btc_1d_volatility_expansion_reclaim_stab_atrs",
            PRACTICAL_PARAMS,
            ohlcv,
            fee_bps=config.fee_bps,
            slippage_bps=config.slippage_bps,
        )
        leader_metrics = _summarize_strategy(leader_returns, periods_per_year)

        benchmarks: list[dict[str, Any]] = []
        for benchmark in BENCHMARKS:
            benchmark_returns = _compute_returns(
                benchmark["strategy_name"],
                benchmark["parameters"],
                ohlcv,
                fee_bps=config.fee_bps,
                slippage_bps=config.slippage_bps,
            )
            differential = (leader_returns - benchmark_returns).astype(float)
            bootstrap_samples = _block_bootstrap_diff(
                [float(value) for value in differential.tolist()],
                samples=max(100, int(config.bootstrap_samples)),
                block_size=max(2, int(config.bootstrap_block_size)),
            )
            bootstrap_means = [statistics.fmean(sample) for sample in bootstrap_samples] if bootstrap_samples else []
            bootstrap_sharpes = [
                _annualized_sharpe(pd.Series(sample, dtype=float), periods_per_year) for sample in bootstrap_samples
            ] if bootstrap_samples else []
            paired = {
                "mean_diff": round(float(differential.mean()), 8),
                "p_diff_mean_gt_0": round(
                    sum(1 for value in bootstrap_means if value > 0.0) / max(1, len(bootstrap_means)),
                    8,
                ),
                "diff_sharpe_ci_95": [
                    round(_quantile(bootstrap_sharpes, 0.025), 8),
                    round(_quantile(bootstrap_sharpes, 0.975), 8),
                ] if bootstrap_sharpes else [0.0, 0.0],
            }
            benchmarks.append(
                {
                    "label": benchmark["label"],
                    "strategy_name": benchmark["strategy_name"],
                    "metrics": _summarize_strategy(benchmark_returns, periods_per_year),
                    "paired_bootstrap": paired,
                }
            )

        symbol_reports.append(
            {
                "symbol": symbol,
                "leader": leader_metrics,
                "benchmarks": benchmarks,
            }
        )

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "candidate": "volatility_expansion_reclaim_lower_atr_window_tighter_stop",
        "config": asdict(config),
        "parameters": PRACTICAL_PARAMS,
        "symbols": symbol_reports,
    }

    analysis_dir = ROOT / "analysis_results"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = analysis_dir / f"btc_1d_volatility_expansion_reclaim_stab_atrs_benchmark_stats_{stamp}.json"
    md_path = analysis_dir / f"btc_1d_volatility_expansion_reclaim_stab_atrs_benchmark_stats_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report_md_path": str(md_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
