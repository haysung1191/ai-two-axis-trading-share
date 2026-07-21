from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_1d_walk_forward_diagnostic import (
    Btc1dWalkForwardDiagnosticConfig,
    Btc1dWalkForwardDiagnosticService,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run BTC 1d walk-forward diagnostic for the volatility expansion pullthrough softer-setup hold-31 candidate."
    )
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--walk-forward-windows", type=int, default=5)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    return parser


def parse_args(argv: list[str] | None = None) -> Btc1dWalkForwardDiagnosticConfig:
    args = build_parser().parse_args(argv)
    return Btc1dWalkForwardDiagnosticConfig(
        symbol=args.symbol,
        interval=args.interval,
        periods=args.periods,
        strategy_name="btc_1d_volatility_expansion_pullthrough_v3",
        walk_forward_windows=args.walk_forward_windows,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
        candidate_label="volatility_expansion_pullthrough_softer_setup_hold31",
        extra_parameters={
            "trend_ema_window": 72,
            "breakout_window": 18,
            "atr_window": 14,
            "atr_expansion_window": 10,
            "min_atr_expansion_ratio": 1.10,
            "setup_close_strength_threshold": 0.70,
            "pullthrough_buffer_pct": 0.001,
            "volume_lookback": 18,
            "min_volume_ratio": 1.05,
            "stop_ema_window": 18,
            "max_hold_bars": 31,
        },
    )


def main(argv: list[str] | None = None) -> int:
    result = Btc1dWalkForwardDiagnosticService().run_diagnostic(parse_args(argv))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
