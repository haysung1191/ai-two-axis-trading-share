from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.major_core_strategy_batch import MajorCoreBatchConfig, MajorCoreStrategyBatchService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run major-asset core strategy batch screening.")
    parser.add_argument("--interval", default="4h")
    parser.add_argument("--periods", type=int, default=2000)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    return parser


def parse_args(argv: list[str] | None = None) -> MajorCoreBatchConfig:
    args = build_parser().parse_args(argv)
    return MajorCoreBatchConfig(
        interval=args.interval,
        periods=args.periods,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
    )


def main(argv: list[str] | None = None) -> int:
    result = MajorCoreStrategyBatchService().run_batch(parse_args(argv))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
