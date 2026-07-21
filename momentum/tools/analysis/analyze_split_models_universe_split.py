from __future__ import annotations

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
    _load_kr_universe,
    _load_us_universe,
    _run_trading_backtest_variant,
    _signal_dates,
    _summarize_returns,
)



ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_universe_split_review"
MODEL_VARIANTS = [
    "rule_breadth_it_us5_cap",
    "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on",
]


def _full_context(
    cfg: BacktestConfig,
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame], dict[str, pd.DataFrame], pd.DataFrame]:
    us_stocks, us_etfs = _load_us_universe()
    kr_universe = _load_kr_universe()
    universe = pd.concat([us_stocks, us_etfs, kr_universe], ignore_index=True)
    price_cache, flow_cache = _build_daily_caches(universe)
    monthly_close = _build_monthly_close_matrix(universe, price_cache)
    return universe, price_cache, flow_cache, monthly_close


def _split_universe(full_universe: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {
        "full_universe": full_universe.copy(),
        "us_only": full_universe[full_universe["Market"].eq("US")].copy(),
        "kr_only": full_universe[full_universe["Market"].eq("KR")].copy(),
        "etf_only": full_universe[full_universe["AssetType"].eq("ETF")].copy(),
        "stock_only": full_universe[full_universe["AssetType"].eq("STOCK")].copy(),
    }


def _summarize_nav(nav: pd.DataFrame) -> dict[str, float | int]:
    rets = pd.to_numeric(nav["NetReturn"], errors="coerce").fillna(0.0)
    summary = _summarize_returns(rets, nav["NextDate"])
    return {
        "CAGR": float(summary["CAGR"]),
        "MDD": float(summary["MDD"]),
        "Sharpe": float(summary["Sharpe"]),
        "FinalNAV": float(summary["FinalNAV"]),
        "AnnualTurnover": float(pd.to_numeric(nav["Turnover"], errors="coerce").fillna(0.0).mean() * 12.0),
        "AvgHoldings": float(pd.to_numeric(nav["Holdings"], errors="coerce").fillna(0.0).mean()),
        "Months": int(len(nav)),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cfg = BacktestConfig()
    full_universe, full_price_cache, full_flow_cache, full_monthly_close = _full_context(cfg)
    variant_lookup = _baseline_variant_map()

    rows = []
    for split_name, split_universe in _split_universe(full_universe).items():
        if split_universe.empty:
            continue
        asset_keys = split_universe["AssetKey"].astype(str).tolist()
        price_cache = {k: v for k, v in full_price_cache.items() if k in asset_keys}
        flow_cache = {k: v for k, v in full_flow_cache.items() if k in asset_keys}
        monthly_close = full_monthly_close[[c for c in full_monthly_close.columns if c in asset_keys]].copy()
        signal_dates = _signal_dates(monthly_close, cfg.signal_start)
        if len(signal_dates) < 2:
            continue

        for variant_name in MODEL_VARIANTS:
            result = _run_trading_backtest_variant(
                split_universe,
                price_cache,
                flow_cache,
                monthly_close,
                signal_dates,
                cfg,
                variant_lookup[variant_name],
            )
            nav = result["nav"].copy()
            if nav.empty:
                continue
            row = {
                "Split": split_name,
                "Variant": variant_name,
                "UniverseCount": int(len(split_universe)),
                "USCount": int(split_universe["Market"].eq("US").sum()),
                "KRCount": int(split_universe["Market"].eq("KR").sum()),
                "ETFCount": int(split_universe["AssetType"].eq("ETF").sum()),
                "StockCount": int(split_universe["AssetType"].eq("STOCK").sum()),
            }
            row.update(_summarize_nav(nav))
            rows.append(row)

    summary_df = pd.DataFrame(rows).sort_values(["Split", "Variant"]).reset_index(drop=True)
    summary_df.to_csv(OUTPUT_DIR / "universe_split_compare.csv", index=False, encoding="utf-8-sig")

    relative_rows = []
    for split_name, group in summary_df.groupby("Split"):
        if len(group) < 2:
            continue
        base = group[group["Variant"] == "rule_breadth_it_us5_cap"]
        aggr = group[group["Variant"] == "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on"]
        if base.empty or aggr.empty:
            continue
        base_row = base.iloc[0]
        aggr_row = aggr.iloc[0]
        relative_rows.append(
            {
                "Split": split_name,
                "AggressiveMinusBaselineCAGR": float(aggr_row["CAGR"] - base_row["CAGR"]),
                "AggressiveMinusBaselineSharpe": float(aggr_row["Sharpe"] - base_row["Sharpe"]),
                "AggressiveMinusBaselineMDD": float(aggr_row["MDD"] - base_row["MDD"]),
                "AggressiveMinusBaselineTurnover": float(aggr_row["AnnualTurnover"] - base_row["AnnualTurnover"]),
            }
        )
    relative_df = pd.DataFrame(relative_rows).sort_values("AggressiveMinusBaselineCAGR", ascending=False).reset_index(drop=True)
    relative_df.to_csv(OUTPUT_DIR / "universe_split_relative.csv", index=False, encoding="utf-8-sig")

    summary = {
        "splits_tested": summary_df["Split"].nunique(),
        "best_split_for_aggressive_cagr": None,
        "worst_split_for_aggressive_cagr": None,
        "aggressive_positive_cagr_splits": 0,
    }
    aggr = summary_df[summary_df["Variant"] == "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on"].copy()
    if not aggr.empty:
        aggr_sorted = aggr.sort_values("CAGR", ascending=False)
        summary["best_split_for_aggressive_cagr"] = str(aggr_sorted.iloc[0]["Split"])
        summary["worst_split_for_aggressive_cagr"] = str(aggr_sorted.iloc[-1]["Split"])
        summary["aggressive_positive_cagr_splits"] = int((pd.to_numeric(aggr["CAGR"], errors="coerce") > 0).sum())
    (OUTPUT_DIR / "universe_split_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()


