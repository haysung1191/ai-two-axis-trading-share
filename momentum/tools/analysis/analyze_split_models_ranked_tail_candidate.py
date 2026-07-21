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
    _cost_sensitivity,
    _load_kr_universe,
    _load_us_universe,
    _run_trading_backtest_variant,
    _signal_dates,
    _summarize_returns,
    _walkforward_summary,
)
from tools.analysis.analyze_split_models_variant_regime import _regime_frame, _summarize


ROOT = REPO_ROOT
OUTPUT_DIR = ROOT / "output" / "split_models_ranked_tail_candidate_review"
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
    base_variant = _baseline_variant_map()[BASELINE_VARIANT]
    candidate_variant: TradingVariant = replace(
        base_variant,
        name=CANDIDATE_NAME,
        breadth_bottom_slice_count=4,
        breadth_bottom_slice_penalty=0.60,
        breadth_bottom_slice_penalty_floor=0.35,
    )

    baseline_nav = _run_trading_backtest_variant(
        universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, base_variant
    )["nav"].copy()
    candidate_nav = _run_trading_backtest_variant(
        universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, candidate_variant
    )["nav"].copy()

    full_compare = pd.DataFrame(
        [
            {"Variant": BASELINE_VARIANT, **_summarize_nav(baseline_nav)},
            {"Variant": CANDIDATE_NAME, **_summarize_nav(candidate_nav)},
        ]
    )
    full_compare.to_csv(OUTPUT_DIR / "candidate_full_period_compare.csv", index=False, encoding="utf-8-sig")

    base_walk = _walkforward_summary(baseline_nav, window_months=24, step_months=12).rename(
        columns={"CAGR": "BaselineCAGR", "Sharpe": "BaselineSharpe", "MDD": "BaselineMDD"}
    )
    cand_walk = _walkforward_summary(candidate_nav, window_months=24, step_months=12).rename(
        columns={"CAGR": "CandidateCAGR", "Sharpe": "CandidateSharpe", "MDD": "CandidateMDD"}
    )
    walk = cand_walk.merge(base_walk, on=["WindowStart", "WindowEnd", "Months"], how="inner")
    walk["CAGRDelta"] = pd.to_numeric(walk["CandidateCAGR"], errors="coerce") - pd.to_numeric(walk["BaselineCAGR"], errors="coerce")
    walk["SharpeDelta"] = pd.to_numeric(walk["CandidateSharpe"], errors="coerce") - pd.to_numeric(walk["BaselineSharpe"], errors="coerce")
    walk["MDDDelta"] = pd.to_numeric(walk["CandidateMDD"], errors="coerce") - pd.to_numeric(walk["BaselineMDD"], errors="coerce")
    walk.to_csv(OUTPUT_DIR / "candidate_walkforward_delta.csv", index=False, encoding="utf-8-sig")

    base_cost = _cost_sensitivity(baseline_nav, [0.0, 10.0, 25.0, 50.0, 75.0]).rename(
        columns={"CAGR": "BaselineCAGR", "Sharpe": "BaselineSharpe", "MDD": "BaselineMDD"}
    )
    cand_cost = _cost_sensitivity(candidate_nav, [0.0, 10.0, 25.0, 50.0, 75.0]).rename(
        columns={"CAGR": "CandidateCAGR", "Sharpe": "CandidateSharpe", "MDD": "CandidateMDD"}
    )
    cost = cand_cost.merge(base_cost, on="OneWayCostBps", how="inner")
    cost["CAGRDelta"] = pd.to_numeric(cost["CandidateCAGR"], errors="coerce") - pd.to_numeric(cost["BaselineCAGR"], errors="coerce")
    cost["SharpeDelta"] = pd.to_numeric(cost["CandidateSharpe"], errors="coerce") - pd.to_numeric(cost["BaselineSharpe"], errors="coerce")
    cost["MDDDelta"] = pd.to_numeric(cost["CandidateMDD"], errors="coerce") - pd.to_numeric(cost["BaselineMDD"], errors="coerce")
    cost.to_csv(OUTPUT_DIR / "candidate_cost_delta.csv", index=False, encoding="utf-8-sig")

    compare = baseline_nav.merge(
        candidate_nav,
        on=["SignalDate", "NextDate"],
        suffixes=("_baseline", "_candidate"),
        how="inner",
    )
    compare["SignalDate"] = pd.to_datetime(compare["SignalDate"], errors="coerce")
    compare["NextDate"] = pd.to_datetime(compare["NextDate"], errors="coerce")
    compare["NetReturnDelta"] = compare["NetReturn_candidate"] - compare["NetReturn_baseline"]
    regimes = _regime_frame(monthly_close, signal_dates)
    compare = compare.merge(regimes, on=["SignalDate", "NextDate"], how="left")
    spy_summary = _summarize(compare, ["SPYRegime"])
    kr_summary = _summarize(compare, ["KOSPIRegime"])
    spy_summary.to_csv(OUTPUT_DIR / "candidate_regime_spy_summary.csv", index=False, encoding="utf-8-sig")
    kr_summary.to_csv(OUTPUT_DIR / "candidate_regime_kospi_summary.csv", index=False, encoding="utf-8-sig")

    summary = {
        "baseline_variant": BASELINE_VARIANT,
        "candidate_variant": CANDIDATE_NAME,
        "full_period_cagr_delta": float(full_compare.iloc[1]["CAGR"] - full_compare.iloc[0]["CAGR"]),
        "full_period_sharpe_delta": float(full_compare.iloc[1]["Sharpe"] - full_compare.iloc[0]["Sharpe"]),
        "walkforward_positive_cagr_windows": int((pd.to_numeric(walk["CAGRDelta"], errors="coerce") > 0).sum()),
        "walkforward_negative_cagr_windows": int((pd.to_numeric(walk["CAGRDelta"], errors="coerce") < 0).sum()),
        "walkforward_avg_cagr_delta": float(pd.to_numeric(walk["CAGRDelta"], errors="coerce").mean()),
        "walkforward_avg_sharpe_delta": float(pd.to_numeric(walk["SharpeDelta"], errors="coerce").mean()),
        "cost_latest_cagr_delta": float(cost.sort_values("OneWayCostBps").iloc[-1]["CAGRDelta"]),
        "cost_latest_sharpe_delta": float(cost.sort_values("OneWayCostBps").iloc[-1]["SharpeDelta"]),
        "spy_up_avg_delta": float(spy_summary.loc[spy_summary["SPYRegime"] == "UP", "AvgDelta"].iloc[0]),
        "spy_down_avg_delta": float(spy_summary.loc[spy_summary["SPYRegime"] == "DOWN", "AvgDelta"].iloc[0]),
        "kospi_up_avg_delta": float(kr_summary.loc[kr_summary["KOSPIRegime"] == "UP", "AvgDelta"].iloc[0]),
        "kospi_down_avg_delta": float(kr_summary.loc[kr_summary["KOSPIRegime"] == "DOWN", "AvgDelta"].iloc[0]),
    }
    (OUTPUT_DIR / "candidate_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
