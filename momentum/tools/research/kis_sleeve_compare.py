import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import argparse
from io import BytesIO
from typing import Dict, List

import pandas as pd

import config
from kis_backtest_from_prices import StrategyConfig, build_market_matrices, run_one, strategy_runtime_kwargs, write_csv_any


def read_csv_any(path: str) -> pd.DataFrame:
    try:
        if path.startswith("gs://"):
            from google.cloud import storage

            no_scheme = path.replace("gs://", "", 1)
            bucket_name, blob_name = no_scheme.split("/", 1) if "/" in no_scheme else (no_scheme, "")
            raw = storage.Client().bucket(bucket_name).blob(blob_name).download_as_bytes()
            return pd.read_csv(BytesIO(raw))
        return pd.read_csv(path)
    except Exception as e:
        print(f"[WARN] could not read {path}: {e}")
        return pd.DataFrame()


def make_rotation_variants(args: argparse.Namespace, fee_rate: float) -> List[StrategyConfig]:
    base_kwargs = strategy_runtime_kwargs(args, fee_rate=fee_rate, use_regime_filter=bool(args.regime_filter))
    base_kwargs["regime_off_exposure"] = args.regime_off_exposure
    base_kwargs.pop("top_n_stock", None)
    base_kwargs.pop("top_n_etf", None)
    common = dict(
        rebalance="W-FRI",
        use_buffer=False,
        selection_mode="score",
        entry_rank=20,
        exit_rank=25,
        use_regime_state_model=True,
        use_rotation_overlay=True,
        **base_kwargs,
    )
    return [
        StrategyConfig(name="Weekly Score50 Rotation", top_n_stock=args.top_n, top_n_etf=args.top_n, **common),
        StrategyConfig(
            name="Weekly Score50 Rotation ETFOnly",
            top_n_stock=0,
            top_n_etf=args.top_n,
            fixed_sleeve_weights={"stock": 0.0, "etf": 1.0},
            **common,
        ),
        StrategyConfig(
            name="Weekly Score50 Rotation StockOnly",
            top_n_stock=args.top_n,
            top_n_etf=0,
            fixed_sleeve_weights={"stock": 1.0, "etf": 0.0},
            **common,
        ),
    ]


def main() -> None:
    default_base = f"gs://{config.GCS_BUCKET_NAME}/prices" if config.GCS_BUCKET_NAME else "data/prices"
    default_out = f"gs://{config.GCS_BUCKET_NAME}/backtests/kis_sleeve_compare_report.csv" if config.GCS_BUCKET_NAME else "kis_sleeve_compare_report.csv"
    p = argparse.ArgumentParser(description="Compare current rotation against ETF-only and stock-only sleeve variants.")
    p.add_argument("--base", type=str, default=default_base)
    p.add_argument("--save-path", type=str, default=default_out)
    p.add_argument("--max-files", type=int, default=0)
    p.add_argument("--min-common-dates", type=int, default=180)
    p.add_argument("--top-n", type=int, default=20)
    p.add_argument("--fee-bps", type=int, default=8)
    p.add_argument("--regime-filter", type=int, default=1)
    p.add_argument("--stop-loss-pct", type=float, default=0.12)
    p.add_argument("--trend-exit-ma", type=int, default=60)
    p.add_argument("--regime-ma-window", type=int, default=200)
    p.add_argument("--regime-slope-window", type=int, default=20)
    p.add_argument("--regime-breadth-threshold", type=float, default=0.55)
    p.add_argument("--vol-lookback", type=int, default=20)
    p.add_argument("--target-vol-annual", type=float, default=0.20)
    p.add_argument("--max-weight", type=float, default=0.20)
    p.add_argument("--min-gross-exposure", type=float, default=0.50)
    p.add_argument("--score-top-k", type=int, default=50)
    p.add_argument("--score-power", type=float, default=1.5)
    p.add_argument("--regime-off-exposure", type=float, default=0.40)
    p.add_argument("--allow-intraperiod-reentry", type=int, default=1)
    p.add_argument("--reentry-cooldown-days", type=int, default=0)
    p.add_argument("--osc-lookback", type=int, default=20)
    p.add_argument("--osc-z-entry", type=float, default=-1.5)
    p.add_argument("--osc-z-exit", type=float, default=-0.25)
    p.add_argument("--osc-z-stop", type=float, default=-2.5)
    p.add_argument("--osc-band-sigma", type=float, default=1.5)
    p.add_argument("--osc-band-break-sigma", type=float, default=2.0)
    p.add_argument("--osc-reentry-cooldown-days", type=int, default=5)
    p.add_argument("--rotation-top-k", type=int, default=5)
    p.add_argument("--rotation-tilt-strength", type=float, default=0.20)
    p.add_argument("--rotation-min-sleeve-weight", type=float, default=0.25)
    p.add_argument("--range-slope-threshold", type=float, default=0.015)
    p.add_argument("--range-dist-threshold", type=float, default=0.03)
    p.add_argument("--range-breakout-persistence-threshold", type=float, default=0.35)
    p.add_argument("--range-breadth-tolerance", type=float, default=0.15)
    args = p.parse_args()

    close_s, value_s = build_market_matrices(args.base, "stock", args.max_files)
    close_e, value_e = build_market_matrices(args.base, "etf", args.max_files)
    fee_rate = float(args.fee_bps) / 10000.0
    rows: List[Dict[str, float]] = []
    for stg in make_rotation_variants(args, fee_rate=fee_rate):
        _, m = run_one(close_s, close_e, stg, min_common_dates=args.min_common_dates, traded_value_s=value_s, traded_value_e=value_e)
        rows.append(
            {
                "Strategy": stg.name,
                "CAGR": float(m.get("CAGR", 0.0)),
                "MDD": float(m.get("MDD", 0.0)),
                "Sharpe": float(m.get("Sharpe", 0.0)),
                "AnnualTurnover": float(m.get("AnnualTurnover", 0.0)),
                "AvgStockSleeve": float(m.get("AvgStockSleeve", 0.0)),
                "AvgEtfSleeve": float(m.get("AvgEtfSleeve", 0.0)),
                "RotationSignalAvg": float(m.get("RotationSignalAvg", 0.0)),
                "FinalNAV": float(m.get("FinalNAV", 0.0)),
                "RunId": "",
                "RunStartedAt": "",
            }
        )
    out = pd.DataFrame(rows).sort_values(["CAGR", "Sharpe", "Strategy"], ascending=[False, False, True]).reset_index(drop=True)
    write_csv_any(out, args.save_path, index=False)
    print(f"saved {args.save_path}")
    print("\n=== Sleeve Compare ===")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
