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

from app.domains.market_data import BinanceDataProvider
from app.domains.strategy.loader import load_strategy


@dataclass(frozen=True)
class ConcentrationCompareConfig:
    symbol: str = "BTCUSDT"
    interval: str = "1d"
    periods: int = 2200
    fee_bps: float = 8.0
    slippage_bps: float = 8.0
    allow_synthetic_ohlcv_fallback: bool = False


CANDIDATES: list[dict[str, Any]] = [
    {
        "label": "ratio112_tighter_stop_main",
        "strategy_name": "btc_1d_volatility_expansion_reclaim_sr112_tightstop",
        "parameters": {
            "trend_ema_window": 72,
            "breakout_window": 18,
            "atr_window": 12,
            "atr_expansion_window": 5,
            "min_atr_expansion_ratio": 1.12,
            "volume_lookback": 18,
            "min_volume_ratio": 1.12,
            "reclaim_buffer_ratio": 0.12,
            "stop_ema_window": 16,
            "max_hold_bars": 34,
        },
    },
    {
        "label": "ratio111_tighter_stop_backup",
        "strategy_name": "btc_1d_volatility_expansion_reclaim_sr112_tightstop_r111",
        "parameters": {
            "trend_ema_window": 72,
            "breakout_window": 18,
            "atr_window": 12,
            "atr_expansion_window": 5,
            "min_atr_expansion_ratio": 1.11,
            "volume_lookback": 18,
            "min_volume_ratio": 1.12,
            "reclaim_buffer_ratio": 0.12,
            "stop_ema_window": 16,
            "max_hold_bars": 34,
        },
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare concentration between BTC sr112 tighter-stop main and backup candidates.")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--fee-bps", type=float, default=8.0)
    parser.add_argument("--slippage-bps", type=float, default=8.0)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    return parser


def parse_args(argv: list[str] | None = None) -> ConcentrationCompareConfig:
    args = build_parser().parse_args(argv)
    return ConcentrationCompareConfig(
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


def _load_ohlcv(config: ConcentrationCompareConfig) -> pd.DataFrame:
    provider = BinanceDataProvider()
    end_ts = pd.Timestamp.now(tz="UTC").floor(config.interval)
    start_ts = end_ts - (_interval_delta(config.interval) * int(config.periods))
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


def _compute_returns_and_trades(
    ohlcv: pd.DataFrame,
    *,
    strategy_name: str,
    parameters: dict[str, Any],
    fee_bps: float,
    slippage_bps: float,
) -> tuple[pd.Series, list[dict[str, Any]]]:
    strategy = load_strategy(strategy_name, strategies_dir=Path("strategies"))
    raw_signals = strategy.generate_signals(ohlcv, parameters)
    signals = raw_signals.reindex(ohlcv.index).fillna(0.0).clip(lower=-1.0, upper=1.0).astype(float)
    position = signals.shift(1).fillna(0.0)
    period_returns = ohlcv["close"].astype(float).pct_change().fillna(0.0)
    turnover = signals.diff().abs().fillna(signals.abs()).astype(float)
    total_cost_rate = max(0.0, float(fee_bps) + float(slippage_bps)) / 10000.0
    strategy_returns = ((period_returns * position) - (turnover * total_cost_rate)).astype(float)

    trades: list[dict[str, Any]] = []
    active_direction = 0.0
    entry_idx: int | None = None
    for idx in range(len(ohlcv.index)):
        direction = float(position.iloc[idx])
        if active_direction == 0.0 and direction != 0.0:
            active_direction = direction
            entry_idx = idx
            continue
        if active_direction != 0.0 and direction == active_direction:
            continue
        if active_direction != 0.0 and entry_idx is not None:
            exit_idx = idx - 1
            if exit_idx >= entry_idx:
                trade_slice = strategy_returns.iloc[entry_idx : exit_idx + 1]
                pnl = float((1.0 + trade_slice).prod() - 1.0)
                trades.append(
                    {
                        "entry_timestamp": ohlcv.index[entry_idx].isoformat(),
                        "exit_timestamp": ohlcv.index[exit_idx].isoformat(),
                        "bars_held": int(exit_idx - entry_idx + 1),
                        "pnl": pnl,
                    }
                )
        active_direction = direction
        entry_idx = idx if direction != 0.0 else None
    if active_direction != 0.0 and entry_idx is not None:
        exit_idx = len(ohlcv.index) - 1
        trade_slice = strategy_returns.iloc[entry_idx : exit_idx + 1]
        pnl = float((1.0 + trade_slice).prod() - 1.0)
        trades.append(
            {
                "entry_timestamp": ohlcv.index[entry_idx].isoformat(),
                "exit_timestamp": ohlcv.index[exit_idx].isoformat(),
                "bars_held": int(exit_idx - entry_idx + 1),
                "pnl": pnl,
            }
        )
    return strategy_returns, trades


def _trade_concentration(trades: list[dict[str, Any]]) -> dict[str, Any]:
    positive = [trade for trade in trades if float(trade["pnl"]) > 0.0]
    ordered = sorted(positive, key=lambda item: float(item["pnl"]), reverse=True)
    total_positive = sum(float(item["pnl"]) for item in positive)

    def share(top_n: int) -> float:
        if total_positive <= 0:
            return 0.0
        return float(sum(float(item["pnl"]) for item in ordered[:top_n]) / total_positive)

    return {
        "completed_trades": len(trades),
        "positive_trades": len(positive),
        "top_1_trade_share": round(share(1), 8),
        "top_3_trade_share": round(share(3), 8),
        "top_5_trade_share": round(share(5), 8),
    }


def _monthly_concentration(strategy_returns: pd.Series) -> dict[str, Any]:
    monthly = ((1.0 + strategy_returns).resample("MS").prod() - 1.0).dropna()
    positive = monthly[monthly > 0.0].sort_values(ascending=False)
    total_positive = float(positive.sum())

    def share(top_n: int) -> float:
        if total_positive <= 0:
            return 0.0
        return float(positive.head(top_n).sum() / total_positive)

    return {
        "monthly_observations": int(monthly.shape[0]),
        "positive_months": int(positive.shape[0]),
        "top_1_month_share": round(share(1), 8),
        "top_3_month_share": round(share(3), 8),
        "top_5_month_share": round(share(5), 8),
    }


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# BTC sr112 Tighter Stop Concentration Compare",
        "",
        f"- Symbol: `{report['config']['symbol']}`",
        "",
    ]
    for candidate in report["candidates"]:
        lines.extend(
            [
                f"## {candidate['label']}",
                f"- strategy: `{candidate['strategy_name']}`",
                f"- top 1 trade share: `{candidate['trade_concentration']['top_1_trade_share']:.4f}`",
                f"- top 3 trade share: `{candidate['trade_concentration']['top_3_trade_share']:.4f}`",
                f"- top 5 trade share: `{candidate['trade_concentration']['top_5_trade_share']:.4f}`",
                f"- top 1 month share: `{candidate['monthly_concentration']['top_1_month_share']:.4f}`",
                f"- top 3 month share: `{candidate['monthly_concentration']['top_3_month_share']:.4f}`",
                f"- top 5 month share: `{candidate['monthly_concentration']['top_5_month_share']:.4f}`",
                "",
            ]
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    config = parse_args(argv)
    ohlcv = _load_ohlcv(config)
    candidate_reports: list[dict[str, Any]] = []
    for candidate in CANDIDATES:
        returns, trades = _compute_returns_and_trades(
            ohlcv,
            strategy_name=candidate["strategy_name"],
            parameters=candidate["parameters"],
            fee_bps=config.fee_bps,
            slippage_bps=config.slippage_bps,
        )
        candidate_reports.append(
            {
                "label": candidate["label"],
                "strategy_name": candidate["strategy_name"],
                "parameters": candidate["parameters"],
                "trade_concentration": _trade_concentration(trades),
                "monthly_concentration": _monthly_concentration(returns),
            }
        )

    report = {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "config": asdict(config),
        "candidates": candidate_reports,
    }

    analysis_dir = Path("analysis_results")
    analysis_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = analysis_dir / f"btc_1d_volatility_expansion_reclaim_sr112_tightstop_concentration_compare_{stamp}.json"
    md_path = analysis_dir / f"btc_1d_volatility_expansion_reclaim_sr112_tightstop_concentration_compare_{stamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    print(json.dumps({"report_json_path": str(json_path), "report_md_path": str(md_path), "report": report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
