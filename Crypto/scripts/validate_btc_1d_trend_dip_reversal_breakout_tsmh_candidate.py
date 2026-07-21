from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domains.experiments.btc_paper_validation import BtcPaperValidationConfig, BtcPaperValidationService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run BTCUSDT 1d candidate validation for the latest trend dip reversal breakout survivors."
    )
    parser.add_argument("--analysis-dir", type=Path, default=Path("analysis_results"))
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--interval", default="1d")
    parser.add_argument("--periods", type=int, default=2200)
    parser.add_argument("--fee-bps", type=float, default=8.0)
    parser.add_argument("--slippage-bps", type=float, default=8.0)
    parser.add_argument("--allow-synthetic-ohlcv-fallback", action="store_true")
    return parser


def _latest_exit_batch_path(analysis_dir: Path) -> Path:
    candidates = sorted(
        analysis_dir.glob("btc_1d_trend_dip_reversal_breakout_exit_compression_batch_*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError("No trend dip reversal breakout exit-compression batch artifact found.")
    return candidates[0]


def load_latest_survivors(analysis_dir: Path) -> list[dict]:
    payload = json.loads(_latest_exit_batch_path(analysis_dir).read_text(encoding="utf-8"))
    survivors = [row for row in payload.get("results", []) if str(row.get("decision")) == "KEEP"]
    if not survivors:
        raise ValueError("Latest exit-compression batch has no KEEP survivors to validate.")
    return survivors


def build_validation_configs(args: argparse.Namespace) -> list[BtcPaperValidationConfig]:
    survivors = load_latest_survivors(args.analysis_dir)
    configs: list[BtcPaperValidationConfig] = []
    for row in survivors:
        label = str(row["variant_label"])
        strategy_name = str(row["strategy_name"])
        configs.append(
            BtcPaperValidationConfig(
                symbol=args.symbol,
                interval=args.interval,
                periods=args.periods,
                strategy_name=strategy_name,
                strategy_category="trend_following",
                hypothesis=(
                    f"BTCUSDT 1d trend dip reversal breakout candidate `{label}` "
                    "must hold the new attack profile after stage1 survivor promotion."
                ),
                ema_fast_window=20,
                ema_slow_window=50,
                atr_window=14,
                atr_multiple=3.5,
                time_stop_bars=90,
                expected_max_drawdown=0.22,
                min_sharpe=1.0,
                max_drawdown=0.22,
                min_win_rate=0.45,
                min_cagr=0.2,
                fee_bps=args.fee_bps,
                slippage_bps=args.slippage_bps,
                allow_synthetic_ohlcv_fallback=bool(args.allow_synthetic_ohlcv_fallback),
                artifact_label=label,
                extra_parameters=dict(row["parameters"]),
            )
        )
    return configs


def run_validations(
    configs: list[BtcPaperValidationConfig],
    *,
    analysis_dir: Path,
) -> dict:
    service = BtcPaperValidationService(analysis_results_dir=analysis_dir)
    runs: list[dict] = []
    for config in configs:
        result = service.run_validation(config)
        runs.append(
            {
                "strategy_name": config.strategy_name,
                "artifact_label": config.artifact_label,
                "decision": result["decision_record"]["decision"],
                "failed_gates": result["decision_record"]["failed_gates"],
                "analysis_result_json": result["analysis_result_json"],
                "analysis_result_csv": result["analysis_result_csv"],
            }
        )
    return {"validated_candidates": runs}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configs = build_validation_configs(args)
    summary = run_validations(configs, analysis_dir=args.analysis_dir)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
