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
    parser = argparse.ArgumentParser(
        description="Run BTCUSDT 1d paper validation for the shallow liquidity void refill continuation candidate."
    )
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
        strategy_name="btc_1d_shallow_liquidity_void_refill_continuation_exit_v1",
        strategy_category="trend_following",
        hypothesis="BTCUSDT 1d shallow liquidity void refill continuation candidate aims to test whether the practical-adjacent defensive hold survives candidate-stage validation.",
        ema_fast_window=20,
        ema_slow_window=50,
        atr_window=3,
        atr_multiple=4.0,
        time_stop_bars=80,
        expected_max_drawdown=0.2,
        min_sharpe=1.0,
        max_drawdown=0.2,
        min_win_rate=0.4,
        min_cagr=0.2,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
        artifact_label="btcusdt_1d_2200",
        extra_parameters={
            "trend_ema_window": 64,
            "breakout_window": 18,
            "atr_window": 12,
            "atr_expansion_window": 8,
            "min_atr_expansion_ratio": 1.06,
            "impulse_close_strength_threshold": 0.66,
            "refill_window": 2,
            "max_refill_pct": 0.5,
            "continuation_buffer_pct": 0.0005,
            "volume_lookback": 16,
            "min_volume_ratio": 1.02,
            "stop_ema_window": 16,
            "max_hold_bars": 24,
        },
    )


def main(argv: list[str] | None = None) -> int:
    result = BtcPaperValidationService().run_validation(parse_args(argv))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
