import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import argparse
import math
from typing import Dict, List

import pandas as pd

import config
from kis_backtest_from_prices import StrategyConfig, build_market_matrices, run_one, strategy_runtime_kwargs, write_csv_any


def compute_nav_metrics(out: pd.DataFrame) -> Dict[str, float]:
    if out is None or out.empty:
        return {
            "FinalNAV": 1.0,
            "CAGR": 0.0,
            "MDD": 0.0,
            "Sharpe": 0.0,
        }
    nav = (1.0 + out["daily_return"].astype(float).fillna(0.0)).cumprod()
    years = max((out.index[-1] - out.index[0]).days / 365.25, 1e-9)
    cagr = float(nav.iloc[-1] ** (1 / years) - 1)
    hwm = nav.cummax()
    mdd = float((nav / hwm - 1.0).min())
    sr = float((out["daily_return"].mean() / (out["daily_return"].std(ddof=0) + 1e-12)) * math.sqrt(252))
    return {"FinalNAV": float(nav.iloc[-1]), "CAGR": cagr, "MDD": mdd, "Sharpe": sr}


def build_named_strategy(args: argparse.Namespace, name: str, fee_rate: float) -> StrategyConfig:
    base_kwargs = strategy_runtime_kwargs(args, fee_rate=fee_rate, use_regime_filter=bool(args.regime_filter))
    base_kwargs["regime_off_exposure"] = args.regime_off_exposure
    mapping = {
        "Weekly Score50 RegimeState": StrategyConfig(
            name=name,
            rebalance="W-FRI",
            use_buffer=False,
            selection_mode="score",
            entry_rank=20,
            exit_rank=25,
            use_regime_state_model=True,
            **base_kwargs,
        ),
        "Weekly ETF RiskBudget": StrategyConfig(
            name=name,
            rebalance="W-FRI",
            use_buffer=False,
            selection_mode="score",
            entry_rank=20,
            exit_rank=25,
            use_regime_state_model=True,
            use_etf_risk_budget=True,
            fixed_sleeve_weights={"stock": 0.0, "etf": 1.0},
            **{**base_kwargs, "max_weight": max(float(args.max_weight), 0.35)},
        ),
    }
    if name not in mapping:
        raise ValueError(f"Unsupported blend strategy: {name}")
    return mapping[name]


def main() -> None:
    default_base = f"gs://{config.GCS_BUCKET_NAME}/prices" if config.GCS_BUCKET_NAME else "data/prices"
    default_out = f"gs://{config.GCS_BUCKET_NAME}/backtests/kis_strategy_blend_compare.csv" if config.GCS_BUCKET_NAME else "kis_strategy_blend_compare.csv"
    p = argparse.ArgumentParser(description="Compare fixed-weight blends between named strategy return streams.")
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
    p.add_argument("--risk-budget-lookback", type=int, default=120)
    p.add_argument("--risk-budget-shrinkage", type=float, default=0.35)
    p.add_argument("--risk-budget-iv-blend", type=float, default=0.50)
    p.add_argument("--use-point-in-time-universe", type=int, default=1)
    p.add_argument("--stock-universe-min-bars", type=int, default=750)
    p.add_argument("--stock-universe-min-price", type=float, default=1000.0)
    p.add_argument("--stock-universe-min-avg-value", type=float, default=5_000_000_000.0)
    p.add_argument("--stock-universe-min-median-value", type=float, default=2_000_000_000.0)
    p.add_argument("--stock-universe-max-zero-days", type=int, default=1)
    p.add_argument("--etf-universe-min-bars", type=int, default=180)
    p.add_argument("--etf-universe-min-avg-value", type=float, default=500_000_000.0)
    p.add_argument("--etf-universe-min-median-value", type=float, default=100_000_000.0)
    p.add_argument("--etf-universe-max-zero-days", type=int, default=1)
    args = p.parse_args()

    close_s, value_s = build_market_matrices(args.base, "stock", args.max_files)
    close_e, value_e = build_market_matrices(args.base, "etf", args.max_files)
    fee_rate = float(args.fee_bps) / 10000.0

    strategies = {}
    metrics_map = {}
    for name in ["Weekly Score50 RegimeState", "Weekly ETF RiskBudget"]:
        stg = build_named_strategy(args, name, fee_rate)
        out, m = run_one(close_s, close_e, stg, min_common_dates=args.min_common_dates, traded_value_s=value_s, traded_value_e=value_e)
        strategies[name] = out[["daily_return"]].copy()
        metrics_map[name] = m

    rows: List[Dict[str, float]] = []
    for riskbudget_weight in [0.0, 0.25, 0.50, 0.75, 1.0]:
        regime_weight = 1.0 - riskbudget_weight
        label = f"Blend RS{regime_weight:.2f}_RB{riskbudget_weight:.2f}"
        a = strategies["Weekly Score50 RegimeState"]["daily_return"].astype(float)
        b = strategies["Weekly ETF RiskBudget"]["daily_return"].astype(float)
        df = pd.DataFrame(index=a.index.intersection(b.index))
        df["daily_return"] = (regime_weight * a.loc[df.index]) + (riskbudget_weight * b.loc[df.index])
        stats = compute_nav_metrics(df)
        annual_turnover = (
            regime_weight * float(metrics_map["Weekly Score50 RegimeState"].get("AnnualTurnover", 0.0))
            + riskbudget_weight * float(metrics_map["Weekly ETF RiskBudget"].get("AnnualTurnover", 0.0))
        )
        rows.append(
            {
                "Blend": label,
                "RegimeStateWeight": regime_weight,
                "RiskBudgetWeight": riskbudget_weight,
                "CAGR": stats["CAGR"],
                "MDD": stats["MDD"],
                "Sharpe": stats["Sharpe"],
                "FinalNAV": stats["FinalNAV"],
                "AnnualTurnoverApprox": annual_turnover,
            }
        )

    out = pd.DataFrame(rows).sort_values(["Sharpe", "CAGR", "Blend"], ascending=[False, False, True]).reset_index(drop=True)
    write_csv_any(out, args.save_path, index=False)
    print(f"saved {args.save_path}")
    print("\n=== Strategy Blend Compare ===")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
