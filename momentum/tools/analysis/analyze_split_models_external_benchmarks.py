from __future__ import annotations

import json
import math
from pathlib import Path
import sys
from typing import Callable

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


from split_models.backtest import (
    BacktestConfig,
    _asset_key,
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
OUTPUT_DIR = ROOT / "output" / "split_models_external_benchmark_review"
MODEL_VARIANTS = [
    "rule_breadth_it_us5_cap",
        "rule_sector_cap2_breadth_it_us5_top2_convex_ranked_tail_count6_pen35_floor20_bonus18_pow05_risk_on",
]
SPY_KEY = _asset_key("US", "ETF", "SPY")
KOSPI_KEY = _asset_key("KR", "ETF", "069500")


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


def _run_model_variant(
    cfg: BacktestConfig,
    variant_name: str,
    universe: pd.DataFrame,
    price_cache: dict[str, pd.DataFrame],
    flow_cache: dict[str, pd.DataFrame],
    monthly_close: pd.DataFrame,
    signal_dates: list[pd.Timestamp],
) -> pd.DataFrame:
    variant = _baseline_variant_map()[variant_name]
    return _run_trading_backtest_variant(universe, price_cache, flow_cache, monthly_close, signal_dates, cfg, variant)["nav"].copy()


def _simulate_strategy(
    signal_dates: list[pd.Timestamp],
    monthly_close: pd.DataFrame,
    target_fn,
    one_way_cost_bps: float,
) -> pd.DataFrame:
    cost_rate = one_way_cost_bps / 10000.0
    prev_end_weights: dict[str, float] = {}
    rows: list[dict[str, float | str | pd.Timestamp]] = []

    for idx, signal_date in enumerate(signal_dates[:-1]):
        next_date = signal_dates[idx + 1]
        target_weights = {k: float(v) for k, v in target_fn(signal_date, monthly_close).items() if float(v) > 0}
        turnover = float(
            sum(
                abs(target_weights.get(k, 0.0) - prev_end_weights.get(k, 0.0))
                for k in set(target_weights) | set(prev_end_weights)
            )
        )
        gross_return = 0.0
        end_weights: dict[str, float] = {}
        if target_weights:
            period_returns = {}
            for asset_key, weight in target_weights.items():
                if asset_key not in monthly_close.columns:
                    period_returns[asset_key] = 0.0
                    continue
                period_returns[asset_key] = float(monthly_close.loc[next_date, asset_key] / monthly_close.loc[signal_date, asset_key] - 1.0)
            gross_return = float(sum(target_weights[k] * period_returns[k] for k in target_weights))
            denom = 1.0 + gross_return
            if denom > 0:
                end_weights = {
                    k: float((target_weights[k] * (1.0 + period_returns[k])) / denom)
                    for k in target_weights
                    if target_weights[k] > 0
                }
        net_return = gross_return - turnover * cost_rate
        rows.append(
            {
                "SignalDate": signal_date,
                "NextDate": next_date,
                "GrossReturn": gross_return,
                "NetReturn": net_return,
                "Turnover": turnover,
                "Holdings": len(target_weights),
            }
        )
        prev_end_weights = end_weights

    out = pd.DataFrame(rows)
    out["NAV"] = (1.0 + pd.to_numeric(out["NetReturn"], errors="coerce").fillna(0.0)).cumprod()
    return out


def _spy_buy_hold(signal_date: pd.Timestamp, monthly_close: pd.DataFrame) -> dict[str, float]:
    return {SPY_KEY: 1.0}


def _kospi_buy_hold(signal_date: pd.Timestamp, monthly_close: pd.DataFrame) -> dict[str, float]:
    return {KOSPI_KEY: 1.0}


def _eq_50_50(signal_date: pd.Timestamp, monthly_close: pd.DataFrame) -> dict[str, float]:
    return {SPY_KEY: 0.5, KOSPI_KEY: 0.5}


def _spy_sma10(signal_date: pd.Timestamp, monthly_close: pd.DataFrame) -> dict[str, float]:
    spy_series = monthly_close[SPY_KEY].dropna()
    hist = spy_series.loc[:signal_date]
    if len(hist) < 10:
        return {}
    sma10 = float(hist.tail(10).mean())
    close = float(hist.iloc[-1])
    return {SPY_KEY: 1.0} if close > sma10 else {}


def _build_xs_momentum_target_fn(
    universe: pd.DataFrame,
    monthly_close: pd.DataFrame,
    *,
    top_n: int,
    lookback_months: int = 12,
    skip_recent_months: int = 1,
    market: str | None = None,
    asset_type: str | None = None,
) -> Callable[[pd.Timestamp, pd.DataFrame], dict[str, float]]:
    allowed = universe.copy()
    if market is not None:
        allowed = allowed[allowed["Market"].astype(str).eq(market)].copy()
    if asset_type is not None:
        allowed = allowed[allowed["AssetType"].astype(str).eq(asset_type)].copy()
    allowed_keys = [k for k in allowed["AssetKey"].astype(str).tolist() if k in monthly_close.columns]

    def _target(signal_date: pd.Timestamp, monthly_close: pd.DataFrame) -> dict[str, float]:
        if signal_date not in monthly_close.index or not allowed_keys:
            return {}
        idx = monthly_close.index.get_loc(signal_date)
        if idx < lookback_months + skip_recent_months or idx - skip_recent_months < 0:
            return {}
        end_idx = idx - skip_recent_months
        start_idx = end_idx - lookback_months
        if start_idx < 0:
            return {}
        start_row = monthly_close.iloc[start_idx]
        end_row = monthly_close.iloc[end_idx]
        scores: list[tuple[str, float]] = []
        for asset_key in allowed_keys:
            start_price = pd.to_numeric(start_row.get(asset_key), errors="coerce")
            end_price = pd.to_numeric(end_row.get(asset_key), errors="coerce")
            current_price = pd.to_numeric(monthly_close.loc[signal_date, asset_key], errors="coerce")
            if pd.isna(start_price) or pd.isna(end_price) or pd.isna(current_price) or float(start_price) <= 0:
                continue
            score = float(end_price / start_price - 1.0)
            scores.append((asset_key, score))
        if not scores:
            return {}
        winners = [asset_key for asset_key, _ in sorted(scores, key=lambda x: (x[1], x[0]), reverse=True)[:top_n]]
        if not winners:
            return {}
        weight = 1.0 / float(len(winners))
        return {asset_key: weight for asset_key in winners}

    return _target


def _summarize_nav(nav: pd.DataFrame) -> dict[str, float | int | None]:
    rets = pd.to_numeric(nav["NetReturn"], errors="coerce").fillna(0.0)
    summary = _summarize_returns(rets, nav["NextDate"])
    downside = rets[rets < 0]
    sortino = None
    if len(downside) > 0:
        downside_dev = downside.std(ddof=0) * math.sqrt(12.0)
        if downside_dev > 0:
            sortino = float((rets.mean() * 12.0) / downside_dev)
    calmar = None if summary["MDD"] == 0 else float(summary["CAGR"] / abs(summary["MDD"]))
    profit_factor = None
    losses = float(-rets[rets < 0].sum())
    if losses > 0:
        profit_factor = float(rets[rets > 0].sum() / losses)
    return {
        "CAGR": float(summary["CAGR"]),
        "MDD": float(summary["MDD"]),
        "Sharpe": float(summary["Sharpe"]),
        "Sortino": sortino,
        "Calmar": calmar,
        "FinalNAV": float(summary["FinalNAV"]),
        "ProfitFactor": profit_factor,
        "ExpectancyPerPeriod": float(rets.mean()),
        "WinRate": float((rets > 0).mean()),
        "TradeCountProxy": int(len(nav)),
        "AnnualTurnover": float(pd.to_numeric(nav["Turnover"], errors="coerce").fillna(0.0).mean() * 12.0),
        "AvgExposure": float(pd.to_numeric(nav["Holdings"], errors="coerce").gt(0).mean()),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cfg = BacktestConfig()
    universe, price_cache, flow_cache, monthly_close, signal_dates = _build_context(cfg)

    strategies: dict[str, pd.DataFrame] = {}
    for variant_name in MODEL_VARIANTS:
        strategies[variant_name] = _run_model_variant(cfg, variant_name, universe, price_cache, flow_cache, monthly_close, signal_dates)

    benchmark_fns = {
        "benchmark_spy_buy_hold": _spy_buy_hold,
        "benchmark_kospi200_buy_hold": _kospi_buy_hold,
        "benchmark_spy_kospi_equal_weight": _eq_50_50,
        "benchmark_spy_sma10": _spy_sma10,
        "benchmark_xs_mom_12_1_top5_eq": _build_xs_momentum_target_fn(
            universe,
            monthly_close,
            top_n=5,
            lookback_months=12,
            skip_recent_months=1,
        ),
        "benchmark_xs_mom_12_1_us_stock_top5_eq": _build_xs_momentum_target_fn(
            universe,
            monthly_close,
            top_n=5,
            lookback_months=12,
            skip_recent_months=1,
            market="US",
            asset_type="STOCK",
        ),
    }
    for name, fn in benchmark_fns.items():
        strategies[name] = _simulate_strategy(signal_dates, monthly_close, fn, cfg.one_way_cost_bps)

    summary_rows = []
    for name, nav in strategies.items():
        row = {"Variant": name}
        row.update(_summarize_nav(nav))
        summary_rows.append(row)
        nav.to_csv(OUTPUT_DIR / f"{name}_nav.csv", index=False, encoding="utf-8-sig")

    summary_df = pd.DataFrame(summary_rows).sort_values("CAGR", ascending=False).reset_index(drop=True)
    summary_df.to_csv(OUTPUT_DIR / "external_benchmark_compare.csv", index=False, encoding="utf-8-sig")

    relative_rows = []
    for model_name in MODEL_VARIANTS:
        model_nav = strategies[model_name].copy()
        model_nav["SignalDate"] = pd.to_datetime(model_nav["SignalDate"])
        model_nav["NextDate"] = pd.to_datetime(model_nav["NextDate"])
        for benchmark_name in benchmark_fns:
            bench_nav = strategies[benchmark_name].copy()
            bench_nav["SignalDate"] = pd.to_datetime(bench_nav["SignalDate"])
            bench_nav["NextDate"] = pd.to_datetime(bench_nav["NextDate"])
            compare = model_nav.merge(
                bench_nav,
                on=["SignalDate", "NextDate"],
                suffixes=("_model", "_benchmark"),
                how="inner",
            )
            compare["NetReturnDelta"] = compare["NetReturn_model"] - compare["NetReturn_benchmark"]
            relative_rows.append(
                {
                    "Model": model_name,
                    "Benchmark": benchmark_name,
                    "MonthsCompared": int(len(compare)),
                    "AvgMonthlyDelta": float(pd.to_numeric(compare["NetReturnDelta"], errors="coerce").mean()),
                    "PositiveMonths": int((pd.to_numeric(compare["NetReturnDelta"], errors="coerce") > 0).sum()),
                    "NegativeMonths": int((pd.to_numeric(compare["NetReturnDelta"], errors="coerce") < 0).sum()),
                    "ModelCAGR": float(summary_df.loc[summary_df["Variant"] == model_name, "CAGR"].iloc[0]),
                    "BenchmarkCAGR": float(summary_df.loc[summary_df["Variant"] == benchmark_name, "CAGR"].iloc[0]),
                    "ModelSharpe": float(summary_df.loc[summary_df["Variant"] == model_name, "Sharpe"].iloc[0]),
                    "BenchmarkSharpe": float(summary_df.loc[summary_df["Variant"] == benchmark_name, "Sharpe"].iloc[0]),
                }
            )

    relative_df = pd.DataFrame(relative_rows).sort_values(["Model", "AvgMonthlyDelta"], ascending=[True, False]).reset_index(drop=True)
    relative_df.to_csv(OUTPUT_DIR / "external_benchmark_relative_compare.csv", index=False, encoding="utf-8-sig")

    summary = {
        "period_start": str(signal_dates[0].date()) if signal_dates else None,
        "period_end": str(signal_dates[-1].date()) if signal_dates else None,
        "months": max(len(signal_dates) - 1, 0),
        "best_strategy_by_cagr": None if summary_df.empty else str(summary_df.iloc[0]["Variant"]),
        "best_strategy_by_sharpe": None if summary_df.empty else str(summary_df.sort_values("Sharpe", ascending=False).iloc[0]["Variant"]),
    }
    (OUTPUT_DIR / "external_benchmark_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()


