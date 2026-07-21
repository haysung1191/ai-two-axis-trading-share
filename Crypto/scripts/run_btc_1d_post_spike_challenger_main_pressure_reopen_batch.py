from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_1d_post_spike_challenger_main_pressure_reopen_batch import (
    DEFAULT_VARIANTS,
    Btc1dPostSpikeChallengerMainPressureReopenBatchService,
    Btc1dPostSpikeChallengerMainPressureReopenConfig,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run BTC 1d post-spike challenger main-pressure reopen batch."
    )
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    parser.add_argument(
        "--variant-label",
        action="append",
        default=[],
        help="Optional variant label to keep. Repeat to run a focused shortlist only.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.variant_label:
        selected = [row for row in DEFAULT_VARIANTS if str(row["label"]) in set(args.variant_label)]
        if not selected:
            raise SystemExit(f"No variants matched: {args.variant_label}")
        import app.domains.experiments.btc_1d_post_spike_challenger_main_pressure_reopen_batch as mod

        mod.DEFAULT_VARIANTS = selected

    service = Btc1dPostSpikeChallengerMainPressureReopenBatchService(
        analysis_results_dir=args.analysis_dir
    )
    result = service.run_batch(
        Btc1dPostSpikeChallengerMainPressureReopenConfig(
            periods=args.periods,
            allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
        )
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
