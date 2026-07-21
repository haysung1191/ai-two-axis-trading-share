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
    parser = argparse.ArgumentParser(description="Run BTCUSDT 1d paper validation for the defensive cash filter strategy.")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--floor-ema-window", type=int, default=96)
    parser.add_argument("--rebound-window", type=int, default=3)
    parser.add_argument("--rebound-threshold", type=float, default=0.01)
    parser.add_argument("--dip-window", type=int, default=8)
    parser.add_argument("--dip-threshold", type=float, default=-0.035)
    parser.add_argument("--volatility-window", type=int, default=12)
    parser.add_argument("--max-volatility", type=float, default=0.03)
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
        strategy_name="major_4h_defensive_cash_filter",
        strategy_category="mean_reversion",
        hypothesis="BTCUSDT 1d may preserve capital better when long exposure is limited to rebound-after-dip conditions under a volatility ceiling.",
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        expected_max_drawdown=0.2,
        min_sharpe=0.0,
        max_drawdown=0.35,
        min_win_rate=0.35,
        min_cagr=0.0,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
        extra_parameters={
            "floor_ema_window": args.floor_ema_window,
            "rebound_window": args.rebound_window,
            "rebound_threshold": args.rebound_threshold,
            "dip_window": args.dip_window,
            "dip_threshold": args.dip_threshold,
            "volatility_window": args.volatility_window,
            "max_volatility": args.max_volatility,
        },
    )


def main(argv: list[str] | None = None) -> int:
    result = BtcPaperValidationService().run_validation(parse_args(argv))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
