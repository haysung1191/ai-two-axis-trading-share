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
)


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_ranked_tail_candidate_concentration_review"
BASELINE_VARIANT = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_risk_on"
CANDIDATE_NAME = "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count4_floor35"


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


def _share_of_positive(series: pd.Series, top_n: int) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    positive = values[values > 0]
    total = float(positive.sum())
    if total <= 0 or positive.empty:
        return 0.0
    return float(positive.nlargest(min(top_n, len(positive))).sum() / total)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)
    base_variant = _baseline_variant_map()[BASELINE_VARIANT]
    candidate_variant: TradingVariant = replace(
        base_variant,
        name=CANDIDATE_NAME,
        breadth_bottom_slice_count=4,
        breadth_bottom_slice_penalty=0.60,
        breadth_bottom_slice_penalty_floor=0.35,
    )

    baseline = _run_trading_backtest_variant(universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, base_variant)
    candidate = _run_trading_backtest_variant(universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, candidate_variant)

    base_nav = baseline["nav"].copy()
    cand_nav = candidate["nav"].copy()
    for df in (base_nav, cand_nav):
        df["SignalDate"] = pd.to_datetime(df["SignalDate"])
        df["NextDate"] = pd.to_datetime(df["NextDate"])

    month_compare = base_nav.merge(
        cand_nav,
        on=["SignalDate", "NextDate"],
        suffixes=("_baseline", "_candidate"),
        how="inner",
    )
    month_compare["NetReturnDelta"] = month_compare["NetReturn_candidate"] - month_compare["NetReturn_baseline"]
    month_compare.to_csv(OUTPUT_DIR / "candidate_concentration_month_compare.csv", index=False, encoding="utf-8-sig")

    base_symbol = baseline["symbol_contrib"].copy()
    cand_symbol = candidate["symbol_contrib"].copy()
    for df in (base_symbol, cand_symbol):
        df["SignalDate"] = pd.to_datetime(df["SignalDate"])
        df["NextDate"] = pd.to_datetime(df["NextDate"])

    symbol_compare = base_symbol.merge(
        cand_symbol,
        on=["SignalDate", "NextDate", "Market", "Sector", "Symbol"],
        suffixes=("_baseline", "_candidate"),
        how="outer",
    ).fillna({"Contribution_baseline": 0.0, "Contribution_candidate": 0.0})
    symbol_compare["ContributionDelta"] = (
        pd.to_numeric(symbol_compare["Contribution_candidate"], errors="coerce").fillna(0.0)
        - pd.to_numeric(symbol_compare["Contribution_baseline"], errors="coerce").fillna(0.0)
    )
    symbol_compare.to_csv(OUTPUT_DIR / "candidate_concentration_symbol_compare.csv", index=False, encoding="utf-8-sig")

    month_summary = (
        month_compare.groupby("SignalDate", as_index=False)
        .agg(NetReturnDelta=("NetReturnDelta", "sum"))
        .sort_values("NetReturnDelta", ascending=False)
    )
    symbol_summary = (
        symbol_compare.groupby(["Market", "Sector", "Symbol"], as_index=False)
        .agg(ContributionDelta=("ContributionDelta", "sum"))
        .sort_values("ContributionDelta", ascending=False)
    )
    month_summary.to_csv(OUTPUT_DIR / "candidate_concentration_month_summary.csv", index=False, encoding="utf-8-sig")
    symbol_summary.to_csv(OUTPUT_DIR / "candidate_concentration_symbol_summary.csv", index=False, encoding="utf-8-sig")

    summary = {
        "baseline_variant": BASELINE_VARIANT,
        "candidate_variant": CANDIDATE_NAME,
        "months_compared": int(len(month_compare)),
        "positive_months": int((pd.to_numeric(month_compare["NetReturnDelta"], errors="coerce") > 0).sum()),
        "negative_months": int((pd.to_numeric(month_compare["NetReturnDelta"], errors="coerce") < 0).sum()),
        "avg_monthly_delta": float(pd.to_numeric(month_compare["NetReturnDelta"], errors="coerce").mean()),
        "top_1_positive_month_share": _share_of_positive(month_summary["NetReturnDelta"], 1),
        "top_3_positive_month_share": _share_of_positive(month_summary["NetReturnDelta"], 3),
        "top_1_positive_symbol_share": _share_of_positive(symbol_summary["ContributionDelta"], 1),
        "top_3_positive_symbol_share": _share_of_positive(symbol_summary["ContributionDelta"], 3),
        "top_symbol": None if symbol_summary.empty else str(symbol_summary.iloc[0]["Symbol"]),
    }
    (OUTPUT_DIR / "candidate_concentration_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
