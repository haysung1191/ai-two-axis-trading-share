from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_1d_walk_forward_diagnostic import (
    Btc1dWalkForwardDiagnosticConfig,
    Btc1dWalkForwardDiagnosticService,
)
from scripts.post_spike_active_candidate import (
    ACTIVE_CANDIDATE_LABEL,
    ACTIVE_EXTRA_PARAMETERS,
    ACTIVE_STRATEGY_NAME,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run BTC 1d walk-forward diagnostic for the active post-spike consolidation breakout candidate."
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
        strategy_name=ACTIVE_STRATEGY_NAME,
        walk_forward_windows=args.walk_forward_windows,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
        candidate_label=ACTIVE_CANDIDATE_LABEL,
        extra_parameters=dict(ACTIVE_EXTRA_PARAMETERS),
    )


def main(argv: list[str] | None = None) -> int:
    result = Btc1dWalkForwardDiagnosticService().run_diagnostic(parse_args(argv))
    analysis_json = Path(str(result["analysis_result_json"]))
    analysis_md = Path(str(result["analysis_result_md"]))
    latest_json = analysis_json.with_name(
        "btc_1d_post_spike_consolidation_breakout_walk_forward_latest.json"
    )
    latest_md = analysis_md.with_name(
        "btc_1d_post_spike_consolidation_breakout_walk_forward_latest.md"
    )
    shutil.copyfile(analysis_json, latest_json)
    shutil.copyfile(analysis_md, latest_md)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
