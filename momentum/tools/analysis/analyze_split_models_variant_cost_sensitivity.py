from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from split_models.backtest import (
    BacktestConfig,
    _baseline_variant_map,
    _build_daily_caches,
    _build_monthly_close_matrix,
    _cost_sensitivity,
    _load_kr_universe,
    _load_us_universe,
    _run_trading_backtest_variant,
    _signal_dates,
)



ROOT = REPO_ROOT


def _build_context(
    cfg: BacktestConfig,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame], dict[str, pd.DataFrame], pd.DataFrame, list[pd.Timestamp]]:
    us_stocks, us_etfs = _load_us_universe()
    kr_universe = _load_kr_universe()
    universe = pd.concat([us_stocks, us_etfs, kr_universe], ignore_index=True)
    price_cache, flow_cache = _build_daily_caches(universe)
    monthly_close = _build_monthly_close_matrix(universe, price_cache)
    signal_dates = _signal_dates(monthly_close, cfg.signal_start)
    return universe, price_cache, flow_cache, monthly_close, signal_dates


def _run_variant(
    cfg: BacktestConfig,
    variant_name: str,
    universe: pd.DataFrame,
    price_cache: dict[str, pd.DataFrame],
    flow_cache: dict[str, pd.DataFrame],
    monthly_close: pd.DataFrame,
    signal_dates: list[pd.Timestamp],
) -> dict[str, pd.DataFrame]:
    variant = _baseline_variant_map()[variant_name]
    return _run_trading_backtest_variant(universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, variant)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variants", nargs="+", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--cost-bps", nargs="+", type=float, default=[10.0, 20.0, 30.0, 50.0, 75.0])
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)

    rows: list[pd.DataFrame] = []
    summary: dict[str, dict[str, float | str]] = {}
    for variant_name in args.variants:
        result = _run_variant(cfg, variant_name, universe, price_cache, flow_cache, monthly_close, signal_dates)
        nav = result["nav"].copy()
        sensitivity = _cost_sensitivity(nav, list(args.cost_bps))
        sensitivity.insert(0, "Variant", variant_name)
        rows.append(sensitivity)

        sensitivity = sensitivity.sort_values("OneWayCostBps").reset_index(drop=True)
        start_cagr = float(sensitivity.iloc[0]["CAGR"])
        end_cagr = float(sensitivity.iloc[-1]["CAGR"])
        summary[variant_name] = {
            "start_cost_bps": float(sensitivity.iloc[0]["OneWayCostBps"]),
            "end_cost_bps": float(sensitivity.iloc[-1]["OneWayCostBps"]),
            "start_cagr": start_cagr,
            "end_cagr": end_cagr,
            "cagr_decay": start_cagr - end_cagr,
            "end_sharpe": float(sensitivity.iloc[-1]["Sharpe"]),
        }

    compare = pd.concat(rows, ignore_index=True)
    compare.to_csv(output_dir / "variant_cost_sensitivity_compare.csv", index=False, encoding="utf-8-sig")
    (output_dir / "variant_cost_sensitivity_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    latest_cost = max(args.cost_bps)
    latest = compare[compare["OneWayCostBps"] == latest_cost].sort_values("CAGR", ascending=False)
    latest.to_csv(output_dir / "variant_cost_sensitivity_latest_cost.csv", index=False, encoding="utf-8-sig")

    print(f"variants={len(args.variants)}")
    print(f"latest_cost_bps={latest_cost}")
    if not latest.empty:
        best = latest.iloc[0]
        print(f"best_variant_at_latest_cost={best['Variant']}")
        print(f"best_cagr_at_latest_cost={float(best['CAGR']):.6f}")


if __name__ == "__main__":
    main()


