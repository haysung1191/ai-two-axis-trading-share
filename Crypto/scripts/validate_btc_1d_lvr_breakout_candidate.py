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
    parser = argparse.ArgumentParser(description="Run BTCUSDT 1d paper validation for the low-vol regime breakout candidate.")
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
        strategy_name="btc_1d_lvr_breakout",
        strategy_category="volatility_breakout",
        hypothesis="BTCUSDT 1d low-vol regime breakout survives paper-validation when slower trend confirmation and cleaner breakout gating compress drawdown while preserving 30%+ CAGR.",
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
            "trend_ema_window": 96,
            "atr_window": 14,
            "contraction_window": 48,
            "breakout_window": 24,
            "volume_lookback": 28,
            "min_volume_ratio": 1.6,
            "stop_ema_window": 22,
            "max_hold_bars": 70,
        },
    )


def main(argv: list[str] | None = None) -> int:
    result = BtcPaperValidationService().run_validation(parse_args(argv))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
