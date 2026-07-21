from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_1d_trend_dip_reversal_breakout_exit_compression_batch import (
    Btc1dTrendDipReversalBreakoutExitCompressionBatchService,
    Btc1dTrendDipReversalBreakoutExitCompressionConfig,
    build_seed_aligned_variants,
)


def _load_attack_seed(analysis_dir: Path) -> dict:
    path = analysis_dir / "btc_1d_attack_common_rules_latest.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload.get("recommended_attack_rule_seed", {}))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the BTC 1d trend dip reversal breakout exit-compression batch.")
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--fee-bps", type=float, default=8.0)
    parser.add_argument("--slippage-bps", type=float, default=8.0)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    parser.add_argument("--apply-attack-seed", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = Btc1dTrendDipReversalBreakoutExitCompressionConfig(
        periods=args.periods,
        fee_bps=args.fee_bps,
        slippage_bps=args.slippage_bps,
        allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
    )
    seed = _load_attack_seed(args.analysis_dir) if args.apply_attack_seed else {}
    variants = build_seed_aligned_variants(seed) if args.apply_attack_seed else None
    result = Btc1dTrendDipReversalBreakoutExitCompressionBatchService(analysis_results_dir=args.analysis_dir).run_batch(
        config,
        variants=variants,
    )
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
