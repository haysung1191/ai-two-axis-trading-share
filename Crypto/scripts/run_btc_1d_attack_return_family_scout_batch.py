from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_1d_attack_return_family_scout_batch import (
    Btc1dAttackReturnFamilyScoutBatchService,
    Btc1dAttackReturnFamilyScoutConfig,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run BTC 1d attack return-family scout batch.")
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    parser.add_argument("--family", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    service = Btc1dAttackReturnFamilyScoutBatchService(analysis_results_dir=args.analysis_dir)
    result = service.run_batch(
        Btc1dAttackReturnFamilyScoutConfig(
            periods=args.periods,
            allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
        ),
        families=list(args.family or []),
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
