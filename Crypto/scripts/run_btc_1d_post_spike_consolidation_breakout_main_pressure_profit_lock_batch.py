from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_1d_post_spike_consolidation_breakout_main_pressure_profit_lock_batch import (
    Btc1dPostSpikeConsolidationBreakoutMainPressureProfitLockBatchService,
    Btc1dPostSpikeConsolidationBreakoutMainPressureProfitLockConfig,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run BTC 1d post-spike consolidation breakout main-pressure profit-lock batch."
    )
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    service = Btc1dPostSpikeConsolidationBreakoutMainPressureProfitLockBatchService(
        analysis_results_dir=args.analysis_dir
    )
    result = service.run_batch(
        Btc1dPostSpikeConsolidationBreakoutMainPressureProfitLockConfig(
            periods=args.periods,
            allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
        )
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
