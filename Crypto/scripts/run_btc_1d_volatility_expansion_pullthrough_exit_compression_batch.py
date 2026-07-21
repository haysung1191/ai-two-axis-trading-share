from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_1d_volatility_expansion_pullthrough_exit_compression_batch import (
    Btc1dVolatilityExpansionPullthroughExitCompressionBatchService,
    Btc1dVolatilityExpansionPullthroughExitCompressionConfig,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run BTC 1d volatility expansion pullthrough exit compression batch.")
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--fee-bps", type=float, default=8.0)
    parser.add_argument("--slippage-bps", type=float, default=8.0)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = Btc1dVolatilityExpansionPullthroughExitCompressionConfig(
        symbol=args.symbol,
        interval=args.interval,
        periods=args.periods,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
    )
    result = Btc1dVolatilityExpansionPullthroughExitCompressionBatchService(analysis_results_dir=args.analysis_dir).run_batch(config)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
