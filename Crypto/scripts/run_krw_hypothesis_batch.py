from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.krw_hypothesis_batch import KrwHypothesisBatchConfig, KrwHypothesisBatchService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run KRW BTC-gated 4h batch screening.")
    parser.add_argument("--interval", default="4h")
    parser.add_argument("--periods", type=int, default=360)
    parser.add_argument("--max-symbols", type=int, default=2)
    parser.add_argument("--min-quote-krw-24h", type=float, default=1_000_000_000.0)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    return parser


def parse_args(argv: list[str] | None = None) -> KrwHypothesisBatchConfig:
    args = build_parser().parse_args(argv)
    return KrwHypothesisBatchConfig(
        interval=args.interval,
        periods=args.periods,
        max_symbols=args.max_symbols,
        min_quote_krw_24h=args.min_quote_krw_24h,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
    )


def main(argv: list[str] | None = None) -> int:
    result = KrwHypothesisBatchService().run_batch(parse_args(argv))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
