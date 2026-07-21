from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_paper_validation import BtcPaperValidationConfig, BtcPaperValidationService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run BTCUSDT 1d paper validation for the volatility expansion trend faster-trigger wider-stop candidate.")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--fee-bps", type=float, default=8.0)
    parser.add_argument("--slippage-bps", type=float, default=8.0)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    return parser


def parse_args(argv: list[str] | None = None) -> BtcPaperValidationConfig:
    args = build_parser().parse_args(argv)
    return BtcPaperValidationConfig(
        symbol=args.symbol,
        interval=args.interval,
        periods=args.periods,
        strategy_name="b1dvolexptrend",
        strategy_category="volatility_breakout",
        hypothesis="BTCUSDT 1d volatility expansion trend faster-trigger wider-stop candidate targets 40% CAGR while holding drawdown in the mid-20% range without changing the unstable ATR-ratio threshold.",
        ema_fast_window=20,
        ema_slow_window=50,
        atr_window=14,
        atr_multiple=3.5,
        time_stop_bars=90,
        expected_max_drawdown=0.3,
        min_sharpe=1.0,
        max_drawdown=0.3,
        min_win_rate=0.45,
        min_cagr=0.2,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
        extra_parameters={
            "trend_ema_window": 72,
            "breakout_window": 16,
            "atr_window": 12,
            "atr_expansion_window": 6,
            "min_atr_expansion_ratio": 1.16,
            "volume_lookback": 18,
            "min_volume_ratio": 1.08,
            "stop_ema_window": 20,
            "max_hold_bars": 40,
        },
    )


def main(argv: list[str] | None = None) -> int:
    result = BtcPaperValidationService().run_validation(parse_args(argv))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
