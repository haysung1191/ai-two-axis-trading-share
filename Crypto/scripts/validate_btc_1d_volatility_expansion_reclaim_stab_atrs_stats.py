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
class StatsValidationConfig:
    symbol: str = "BTCUSDT"
    interval: str = "1d"
    periods: int = 2200
    fee_bps: float = 8.0
    slippage_bps: float = 8.0
    benchmark_sharpe: float = 0.0
    selection_trials: int = 20
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run PSR/DSR/bootstrap validation for the BTC practical leader.")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--fee-bps", type=float, default=8.0)
    parser.add_argument("--slippage-bps", type=float, default=8.0)
    parser.add_argument("--benchmark-sharpe", type=float, default=0.0)
    parser.add_argument("--selection-trials", type=int, default=20)
    parser.add_argument("--bootstrap-samples", type=int, default=1000)
    parser.add_argument("--bootstrap-block-size", type=int, default=20)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    return parser


def parse_args(argv: list[str] | None = None) -> StatsValidationConfig:
    args = build_parser().parse_args(argv)
    return StatsValidationConfig(
        symbol=args.symbol,
        interval=args.interval,
        periods=args.periods,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        benchmark_sharpe=args.benchmark_sharpe,
        selection_trials=args.selection_trials,
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


def _load_ohlcv(config: StatsValidationConfig) -> pd.DataFrame:
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


def _compute_strategy_returns(
    ohlcv: pd.DataFrame,
    *,
    fee_bps: float,
    slippage_bps: float,
) -> tuple[pd.Series, pd.Series]:
    strategy = load_strategy("btc_1d_volatility_expansion_reclaim_stab_atrs", strategies_dir=Path("strategies"))
    raw_signals = strategy.generate_signals(ohlcv, PRACTICAL_PARAMS)
    signals = raw_signals.reindex(ohlcv.index).fillna(0.0).clip(lower=-1.0, upper=1.0).astype(float)
    position = signals.shift(1).fillna(0.0)
    period_returns = ohlcv["close"].astype(float).pct_change().fillna(0.0)
    turnover = signals.diff().abs().fillna(signals.abs()).astype(float)
    total_cost_rate = max(0.0, float(fee_bps) + float(slippage_bps)) / 10000.0
    strategy_returns = ((period_returns * position) - (turnover * total_cost_rate)).astype(float)
    return strategy_returns, position


def _annualized_sharpe(returns: pd.Series, periods_per_year: float) -> float:
    ret_std = float(returns.std(ddof=0))
    if ret_std <= 0:
        return 0.0
    ret_mean = float(returns.mean())
    return float((ret_mean / ret_std) * math.sqrt(periods_per_year))


def _max_drawdown(equity_curve: pd.Series) -> float:
    peaks = equity_curve.cummax()
    drawdown = equity_curve / peaks - 1.0
    return float(abs(drawdown.min()))


def _cagr(equity_curve: pd.Series, periods_per_year: float) -> float:
    periods = max(1, len(equity_curve) - 1)
    years = periods / periods_per_year if periods_per_year > 0 else periods / 252.0
    final_equity = float(equity_curve.iloc[-1])
    if years <= 0:
        return 0.0
    if final_equity <= 0:
        return -1.0
    return float((final_equity ** (1 / years)) - 1.0)


def _skewness(values: list[float]) -> float:
    n = len(values)
    if n < 3:
        return 0.0
    mean = statistics.fmean(values)
    centered = [value - mean for value in values]
    m2 = sum(value * value for value in centered) / n
    if m2 <= 0:
        return 0.0
    m3 = sum(value**3 for value in centered) / n
    return float(m3 / (m2 ** 1.5))


def _kurtosis(values: list[float]) -> float:
    n = len(values)
    if n < 4:
        return 3.0
    mean = statistics.fmean(values)
    centered = [value - mean for value in values]
    m2 = sum(value * value for value in centered) / n
    if m2 <= 0:
        return 3.0
    m4 = sum(value**4 for value in centered) / n
    return float(m4 / (m2**2))


def _normal_cdf(value: float) -> float:
    return statistics.NormalDist().cdf(value)


def _probabilistic_sharpe_ratio(observed_sr: float, benchmark_sr: float, n: int, skew: float, kurtosis: float) -> float:
    if n <= 1:
        return 0.0
    denominator = math.sqrt(max(1e-12, 1.0 - (skew * observed_sr) + (((kurtosis - 1.0) / 4.0) * (observed_sr**2))))
    z_score = ((observed_sr - benchmark_sr) * math.sqrt(n - 1)) / denominator
    return float(_normal_cdf(z_score))


def _expected_max_sharpe_variance(num_trials: int) -> float:
    if num_trials <= 1:
        return 0.0
    norm = statistics.NormalDist()
    euler_gamma = 0.5772156649
    term1 = norm.inv_cdf(1.0 - (1.0 / num_trials))
    term2 = norm.inv_cdf(1.0 - (1.0 / (num_trials * math.e)))
    return float((1.0 - euler_gamma) * term1 + euler_gamma * term2)


def _deflated_sharpe_ratio(observed_sr: float, n: int, skew: float, kurtosis: float, num_trials: int) -> tuple[float, float]:
    sr_star = _expected_max_sharpe_variance(num_trials)
    dsr = _probabilistic_sharpe_ratio(observed_sr, sr_star, n, skew, kurtosis)
    return float(dsr), float(sr_star)


def _trade_count(position: pd.Series) -> int:
    signal = position.shift(-1).fillna(0.0)
    turnover = signal.diff().abs().fillna(signal.abs())
    return int((turnover > 0).sum())


def _block_bootstrap_returns(
    returns: list[float],
    *,
    samples: int,
    block_size: int,
    seed: int = 42,
) -> list[list[float]]:
    if not returns:
        return []
    rng = Random(seed)
    n = len(returns)
    block = max(2, min(block_size, n))
    bootstraps: list[list[float]] = []
    for _ in range(samples):
        sample: list[float] = []
        while len(sample) < n:
            start = rng.randrange(0, max(1, n - block + 1))
            sample.extend(returns[start : start + block])
        bootstraps.append(sample[:n])
    return bootstraps


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return float(ordered[0])
    position = (len(ordered) - 1) * q
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return float(ordered[lower])
    weight = position - lower
    return float((ordered[lower] * (1.0 - weight)) + (ordered[upper] * weight))


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# BTC 1d Practical Leader Statistical Defense",
        "",
        "- Candidate: `volatility_expansion_reclaim lower_atr_window_tighter_stop`",
        f"- Symbol: `{report['config']['symbol']}`",
        f"- Interval: `{report['config']['interval']}`",
        f"- Periods: `{report['config']['periods']}`",
        "",
        "## Core",
        "",
        f"- Sharpe: `{report['metrics']['sharpe']:.4f}`",
        f"- CAGR: `{report['metrics']['cagr'] * 100:.2f}%`",
        f"- MDD: `{report['metrics']['max_drawdown'] * 100:.2f}%`",
        f"- trades: `{report['metrics']['trades']}`",
        "",
        "## Statistical Defense",
        "",
        f"- PSR vs Sharpe {report['config']['benchmark_sharpe']:.2f}: `{report['statistics']['psr']:.4f}`",
        f"- DSR: `{report['statistics']['dsr']:.4f}`",
        f"- DSR hurdle Sharpe: `{report['statistics']['dsr_hurdle_sharpe']:.4f}`",
        f"- selection trials assumption: `{report['config']['selection_trials']}`",
        "",
        "## Bootstrap",
        "",
        f"- Sharpe 95% CI: `[{report['bootstrap']['sharpe_ci_95'][0]:.4f}, {report['bootstrap']['sharpe_ci_95'][1]:.4f}]`",
        f"- CAGR 95% CI: `[{report['bootstrap']['cagr_ci_95'][0] * 100:.2f}%, {report['bootstrap']['cagr_ci_95'][1] * 100:.2f}%]`",
        f"- MDD 95% CI: `[{report['bootstrap']['mdd_ci_95'][0] * 100:.2f}%, {report['bootstrap']['mdd_ci_95'][1] * 100:.2f}%]`",
        f"- P(Sharpe > 0): `{report['bootstrap']['p_sharpe_gt_0']:.4f}`",
        f"- P(CAGR > 25%): `{report['bootstrap']['p_cagr_gt_25pct']:.4f}`",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv)
    ohlcv = _load_ohlcv(config)
    returns, position = _compute_strategy_returns(ohlcv, fee_bps=config.fee_bps, slippage_bps=config.slippage_bps)
    periods_per_year = _compute_periods_per_year(ohlcv)
    equity_curve = (1.0 + returns).cumprod()
    returns_list = [float(value) for value in returns.tolist()]
    n = len(returns_list)
    sharpe = _annualized_sharpe(returns, periods_per_year)
    cagr = _cagr(equity_curve, periods_per_year)
    max_drawdown = _max_drawdown(equity_curve)
    skew = _skewness(returns_list)
    kurtosis = _kurtosis(returns_list)
    psr = _probabilistic_sharpe_ratio(sharpe, float(config.benchmark_sharpe), n, skew, kurtosis)
    dsr, hurdle = _deflated_sharpe_ratio(sharpe, n, skew, kurtosis, max(1, int(config.selection_trials)))

    bootstraps = _block_bootstrap_returns(
        returns_list,
        samples=max(100, int(config.bootstrap_samples)),
        block_size=max(2, int(config.bootstrap_block_size)),
    )
    bootstrap_sharpes: list[float] = []
    bootstrap_cagrs: list[float] = []
    bootstrap_mdds: list[float] = []
    for sample in bootstraps:
        sample_series = pd.Series(sample, dtype=float)
        sample_equity = (1.0 + sample_series).cumprod()
        bootstrap_sharpes.append(_annualized_sharpe(sample_series, periods_per_year))
        bootstrap_cagrs.append(_cagr(sample_equity, periods_per_year))
        bootstrap_mdds.append(_max_drawdown(sample_equity))

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "candidate": "volatility_expansion_reclaim_lower_atr_window_tighter_stop",
        "config": asdict(config),
        "parameters": PRACTICAL_PARAMS,
        "metrics": {
            "sharpe": round(float(sharpe), 8),
            "cagr": round(float(cagr), 8),
            "max_drawdown": round(float(max_drawdown), 8),
            "trades": _trade_count(position),
            "return_observations": n,
            "periods_per_year": round(float(periods_per_year), 8),
            "skew": round(float(skew), 8),
            "kurtosis": round(float(kurtosis), 8),
        },
        "statistics": {
            "psr": round(float(psr), 8),
            "dsr": round(float(dsr), 8),
            "dsr_hurdle_sharpe": round(float(hurdle), 8),
        },
        "bootstrap": {
            "samples": len(bootstraps),
            "block_size": max(2, int(config.bootstrap_block_size)),
            "sharpe_ci_95": [
                round(_quantile(bootstrap_sharpes, 0.025), 8),
                round(_quantile(bootstrap_sharpes, 0.975), 8),
            ],
            "cagr_ci_95": [
                round(_quantile(bootstrap_cagrs, 0.025), 8),
                round(_quantile(bootstrap_cagrs, 0.975), 8),
            ],
            "mdd_ci_95": [
                round(_quantile(bootstrap_mdds, 0.025), 8),
                round(_quantile(bootstrap_mdds, 0.975), 8),
            ],
            "p_sharpe_gt_0": round(sum(1 for value in bootstrap_sharpes if value > 0.0) / max(1, len(bootstrap_sharpes)), 8),
            "p_cagr_gt_25pct": round(sum(1 for value in bootstrap_cagrs if value > 0.25) / max(1, len(bootstrap_cagrs)), 8),
        },
    }

    analysis_dir = ROOT / "analysis_results"
    analysis_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = analysis_dir / f"btc_1d_volatility_expansion_reclaim_stab_atrs_stats_{stamp}.json"
    md_path = analysis_dir / f"btc_1d_volatility_expansion_reclaim_stab_atrs_stats_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report_md_path": str(md_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
