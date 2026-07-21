from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from split_models.backtest import (
    BacktestConfig,
    TradingVariant,
    _baseline_variant_map,
    _build_daily_caches,
    _build_monthly_close_matrix,
    _load_kr_universe,
    _load_us_universe,
    _run_trading_backtest_variant,
    _signal_dates,
    _summarize_returns,
)


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_ranked_tail_surface_review"
BASE_VARIANT_NAME = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_risk_on"
BOTTOM_SLICE_COUNTS = [3, 4]
BOTTOM_SLICE_PENALTIES = [0.60, 0.65]
BOTTOM_SLICE_FLOORS = [0.35, 0.40, 0.45]


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


def _summarize_nav(nav: pd.DataFrame) -> dict[str, float]:
    rets = pd.to_numeric(nav["NetReturn"], errors="coerce").fillna(0.0)
    summary = _summarize_returns(rets, nav["NextDate"])
    return {
        "CAGR": float(summary["CAGR"]),
        "MDD": float(summary["MDD"]),
        "Sharpe": float(summary["Sharpe"]),
        "FinalNAV": float(summary["FinalNAV"]),
        "AnnualTurnover": float(pd.to_numeric(nav["Turnover"], errors="coerce").fillna(0.0).mean() * 12.0),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    base_variant = _baseline_variant_map()[BASE_VARIANT_NAME]

    rows: list[dict[str, float | int | str]] = []
    for bottom_count in BOTTOM_SLICE_COUNTS:
        for penalty in BOTTOM_SLICE_PENALTIES:
            for floor in BOTTOM_SLICE_FLOORS:
                if floor >= penalty:
                    continue
                variant: TradingVariant = replace(
                    base_variant,
                    name=f"{BASE_VARIANT_NAME}_count{bottom_count}_pen{int(round(penalty*100))}_floor{int(round(floor*100))}",
                    breadth_bottom_slice_count=int(bottom_count),
                    breadth_bottom_slice_penalty=float(penalty),
                    breadth_bottom_slice_penalty_floor=float(floor),
                )
                nav = _run_trading_backtest_variant(
                    universe,
                    price_cache,
                    flow_cache,
                    monthly_close,
                    signal_dates,
                    cfg,
                    variant,
                )["nav"].copy()
                row = {
                    "BottomSliceCount": int(bottom_count),
                    "BottomSlicePenalty": float(penalty),
                    "BottomSlicePenaltyFloor": float(floor),
                }
                row.update(_summarize_nav(nav))
                rows.append(row)

    compare = pd.DataFrame(rows).sort_values(["CAGR", "Sharpe"], ascending=[False, False]).reset_index(drop=True)
    compare.to_csv(OUTPUT_DIR / "ranked_tail_surface_compare.csv", index=False, encoding="utf-8-sig")

    best = compare.iloc[0]
    best_cagr = float(best["CAGR"])
    near_best = compare[pd.to_numeric(compare["CAGR"], errors="coerce") >= best_cagr - 0.01].copy()

    by_count = (
        compare.groupby("BottomSliceCount", as_index=False)
        .agg(
            AvgCAGR=("CAGR", "mean"),
            BestCAGR=("CAGR", "max"),
            AvgSharpe=("Sharpe", "mean"),
            BestSharpe=("Sharpe", "max"),
        )
        .sort_values("BestCAGR", ascending=False)
    )
    by_count.to_csv(OUTPUT_DIR / "ranked_tail_surface_by_count.csv", index=False, encoding="utf-8-sig")

    by_penalty_floor = (
        compare.groupby(["BottomSlicePenalty", "BottomSlicePenaltyFloor"], as_index=False)
        .agg(
            AvgCAGR=("CAGR", "mean"),
            BestCAGR=("CAGR", "max"),
            AvgSharpe=("Sharpe", "mean"),
            BestSharpe=("Sharpe", "max"),
        )
        .sort_values(["BestCAGR", "BestSharpe"], ascending=[False, False])
    )
    by_penalty_floor.to_csv(OUTPUT_DIR / "ranked_tail_surface_by_penalty_floor.csv", index=False, encoding="utf-8-sig")

    summary = {
        "base_variant": BASE_VARIANT_NAME,
        "combos_tested": int(len(compare)),
        "best_bottom_slice_count": int(best["BottomSliceCount"]),
        "best_bottom_slice_penalty": float(best["BottomSlicePenalty"]),
        "best_bottom_slice_penalty_floor": float(best["BottomSlicePenaltyFloor"]),
        "best_cagr": float(best["CAGR"]),
        "best_sharpe": float(best["Sharpe"]),
        "near_best_combo_count": int(len(near_best)),
        "avg_cagr_across_surface": float(pd.to_numeric(compare["CAGR"], errors="coerce").mean()),
        "avg_sharpe_across_surface": float(pd.to_numeric(compare["Sharpe"], errors="coerce").mean()),
        "cagr_range": float(pd.to_numeric(compare["CAGR"], errors="coerce").max() - pd.to_numeric(compare["CAGR"], errors="coerce").min()),
        "sharpe_range": float(pd.to_numeric(compare["Sharpe"], errors="coerce").max() - pd.to_numeric(compare["Sharpe"], errors="coerce").min()),
    }
    (OUTPUT_DIR / "ranked_tail_surface_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
