from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_paper_validation import BtcPaperValidationConfig, BtcPaperValidationService
from scripts.post_spike_active_candidate import (
    ACTIVE_ARTIFACT_LABEL,
    ACTIVE_EXTRA_PARAMETERS,
    ACTIVE_HYPOTHESIS,
    ACTIVE_STRATEGY_NAME,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run BTCUSDT 1d paper validation for the active post-spike consolidation breakout candidate."
    )
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--periods", type=int, default=2200)
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
        strategy_name=ACTIVE_STRATEGY_NAME,
        strategy_category="trend_following",
        hypothesis=ACTIVE_HYPOTHESIS,
        ema_fast_window=20,
        ema_slow_window=50,
        atr_window=14,
        atr_multiple=3.5,
        time_stop_bars=90,
        expected_max_drawdown=0.20,
        min_sharpe=1.0,
        max_drawdown=0.20,
        min_win_rate=0.45,
        min_cagr=0.20,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
        artifact_label=ACTIVE_ARTIFACT_LABEL,
        extra_parameters=dict(ACTIVE_EXTRA_PARAMETERS),
    )


def main(argv: list[str] | None = None) -> int:
    result = BtcPaperValidationService().run_validation(parse_args(argv))
    analysis_json = Path(str(result["analysis_result_json"]))
    analysis_csv = Path(str(result["analysis_result_csv"]))
    latest_json = analysis_json.with_name(
        "btc_1d_post_spike_consolidation_breakout_candidate_paper_validation_latest.json"
    )
    latest_csv = analysis_csv.with_name(
        "btc_1d_post_spike_consolidation_breakout_candidate_paper_validation_latest.csv"
    )
    shutil.copyfile(analysis_json, latest_json)
    shutil.copyfile(analysis_csv, latest_csv)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
