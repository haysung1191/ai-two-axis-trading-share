from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_1d_risk_scaling_stability_batch import (
    Btc1dRiskScalingStabilityBatchService,
    Btc1dRiskScalingStabilityConfig,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run BTCUSDT 1d risk-scaling stability batch.")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--lookbacks", nargs="*", type=int, default=[1400, 1800, 2200, 2600])
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    return parser


def parse_args(argv: list[str] | None = None) -> Btc1dRiskScalingStabilityConfig:
    args = build_parser().parse_args(argv)
    return Btc1dRiskScalingStabilityConfig(
        symbol=args.symbol,
        interval=args.interval,
        lookback_periods=tuple(args.lookbacks),
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
    )


def main(argv: list[str] | None = None) -> int:
    result = Btc1dRiskScalingStabilityBatchService().run_batch(parse_args(argv))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
