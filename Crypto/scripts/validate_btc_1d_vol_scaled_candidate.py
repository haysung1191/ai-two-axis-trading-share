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
    parser = argparse.ArgumentParser(description="Run BTCUSDT 1d paper validation for the promoted low-volatility capped candidate.")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--ema-fast-window", type=int, default=20)
    parser.add_argument("--ema-slow-window", type=int, default=50)
    parser.add_argument("--atr-window", type=int, default=14)
    parser.add_argument("--atr-multiple", type=float, default=3.5)
    parser.add_argument("--time-stop-bars", type=int, default=90)
    parser.add_argument("--regime-exit-confirmation-bars", type=int, default=2)
    parser.add_argument("--volatility-window", type=int, default=20)
    parser.add_argument("--volatility-target", type=float, default=0.2)
    parser.add_argument("--min-position-size", type=float, default=0.35)
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
        strategy_name="btc_1d_ema_trend_atr_exit",
        strategy_category="trend_following",
        hypothesis="BTCUSDT 1d trend following survives paper-validation when low-volatility exposure is capped and keeps drawdown below the hard gate.",
        ema_fast_window=args.ema_fast_window,
        ema_slow_window=args.ema_slow_window,
        atr_window=args.atr_window,
        atr_multiple=args.atr_multiple,
        time_stop_bars=args.time_stop_bars,
        expected_max_drawdown=0.18,
        min_sharpe=1.0,
        max_drawdown=0.2,
        min_win_rate=0.45,
        min_cagr=0.05,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
        extra_parameters={
            "regime_exit_confirmation_bars": args.regime_exit_confirmation_bars,
            "volatility_window": args.volatility_window,
            "volatility_target": args.volatility_target,
            "min_position_size": args.min_position_size,
            "risk_off_drawdown_threshold": 0.0,
            "risk_off_lookback": 120,
            "recovery_confirmation_bars": 3,
            "cooldown_bars": 0,
            "low_volatility_cap_threshold": 0.45,
            "low_volatility_position_cap": 0.35,
        },
    )


def main(argv: list[str] | None = None) -> int:
    result = BtcPaperValidationService().run_validation(parse_args(argv))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
