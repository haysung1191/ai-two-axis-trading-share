from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_paper_validation import BtcPaperValidationConfig, BtcPaperValidationService


ANALYSIS_DIR = Path("analysis_results")
REPAIR_BATCH_GLOB = "btc_1d_post_spike_consolidation_breakout_walk_forward_repair_batch_*.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _latest_json(pattern: str, analysis_dir: Path) -> Path:
    matches = sorted(analysis_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(f"No analysis artifact matched pattern: {pattern}")
    return matches[0]


def _latest_repair_winner(analysis_dir: Path) -> dict:
    payload = _load_json(_latest_json(REPAIR_BATCH_GLOB, analysis_dir))
    best = dict(payload["best_variant"])
    return {
        "variant_label": str(best["variant_label"]),
        "strategy_name": str(best["strategy_name"]),
        "parameters": dict(best["parameters"]),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run BTCUSDT 1d paper validation for the latest post-spike walk-forward repair winner."
    )
    parser.add_argument("--analysis-dir", type=Path, default=ANALYSIS_DIR)
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--fee-bps", type=float, default=8.0)
    parser.add_argument("--slippage-bps", type=float, default=8.0)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    return parser


def parse_args(argv: list[str] | None = None) -> BtcPaperValidationConfig:
    args = build_parser().parse_args(argv)
    winner = _latest_repair_winner(args.analysis_dir)
    candidate_suffix = winner["variant_label"]
    artifact_label = f"btcusdt_1d_{args.periods}_{candidate_suffix}_friction_{int(args.fee_bps)}bps"
    hypothesis = (
        "BTCUSDT 1d latest post-spike walk-forward repair winner validation checks whether the current "
        f"repair leader `{candidate_suffix}` survives paper validation under {args.fee_bps:.0f}bps friction."
    )
    return BtcPaperValidationConfig(
        symbol=args.symbol,
        interval=args.interval,
        periods=args.periods,
        strategy_name=winner["strategy_name"],
        strategy_category="trend_following",
        hypothesis=hypothesis,
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
        artifact_label=artifact_label,
        extra_parameters=winner["parameters"],
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = parse_args(argv)
    result = BtcPaperValidationService(analysis_results_dir=args.analysis_dir).run_validation(config)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
