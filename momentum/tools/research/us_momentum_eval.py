import argparse
import io
import zipfile
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import numpy as np
import pandas as pd
import requests
import statsmodels.api as sm

from tools.research.us_etf_riskbudget import run_backtest as run_etf_riskbudget
from tools.research.us_stock_mom12_1 import run_backtest as run_stock_mom
from tools.research.us_stock_mom12_1 import (
    build_membership_lookup,
    compute_rebalance_dates,
    load_price_matrix,
    load_universe,
    membership_sector,
)
from tools.research.us_residual_sector_rotation import run_backtest as run_residual

FF_MOM_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_daily_CSV.zip"


def max_drawdown(nav: pd.Series) -> float:
    peak = nav.cummax()
    dd = nav / peak - 1.0
    return float(dd.min()) if not dd.empty else 0.0


def annualized_sharpe(daily_returns: pd.Series) -> float:
    r = pd.to_numeric(daily_returns, errors="coerce").dropna()
    if len(r) < 2:
        return 0.0
    vol = float(r.std(ddof=0))
    if vol <= 0:
        return 0.0
    return float(r.mean() / vol * np.sqrt(252.0))


def summarize_nav(nav_df: pd.DataFrame) -> dict[str, float]:
    nav = pd.to_numeric(nav_df["nav"], errors="coerce").dropna()
    rets = pd.to_numeric(nav_df.iloc[:, 1], errors="coerce").fillna(0.0)
    years = max((pd.to_datetime(nav_df["date"]).iloc[-1] - pd.to_datetime(nav_df["date"]).iloc[0]).days / 365.25, 1 / 365.25)
    return {
        "CAGR": float(nav.iloc[-1] ** (1.0 / years) - 1.0),
        "MDD": max_drawdown(nav.reset_index(drop=True)),
        "Sharpe": annualized_sharpe(rets),
    }


def walkforward_rows(nav_df: pd.DataFrame, strategy: str, train_years: int, test_years: int, step_years: int) -> list[dict]:
    out = []
    df = nav_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    start = df["date"].min()
    end = df["date"].max()
    test_start = start + pd.DateOffset(years=train_years)
    while test_start + pd.DateOffset(years=test_years) <= end:
        test_end = test_start + pd.DateOffset(years=test_years)
        window = df[(df["date"] >= test_start) & (df["date"] < test_end)].copy()
        if len(window) < 200:
            test_start = test_start + pd.DateOffset(years=step_years)
            continue
        nav = (1.0 + pd.to_numeric(window["net_return"], errors="coerce").fillna(0.0)).cumprod()
        years = max((window["date"].iloc[-1] - window["date"].iloc[0]).days / 365.25, 1 / 365.25)
        out.append(
            {
                "Strategy": strategy,
                "TestStart": str(test_start.date()),
                "TestEnd": str((test_end - pd.Timedelta(days=1)).date()),
                "CAGR": float(nav.iloc[-1] ** (1.0 / years) - 1.0),
                "MDD": max_drawdown(nav),
                "Sharpe": annualized_sharpe(window["net_return"]),
            }
        )
        test_start = test_start + pd.DateOffset(years=step_years)
    return out


def min_capital_for_one_share_each(portfolio_path: Path) -> pd.DataFrame:
    p = pd.read_csv(portfolio_path)
    if p.empty:
        return pd.DataFrame()
    req = (pd.to_numeric(p["CurrentPrice"], errors="coerce") / pd.to_numeric(p["TargetWeight"], errors="coerce")).replace([np.inf, -np.inf], np.nan)
    out = p[["Symbol", "Sector", "TargetWeight", "CurrentPrice"]].copy()
    out["MinCapitalForOneShareUSD"] = req
    return out.sort_values("MinCapitalForOneShareUSD", ascending=False).reset_index(drop=True)


def run_same_universe_benchmark(
    price_base: Path,
    report_path: Path,
    membership_path: Path | None,
    rebalance: str = "ME",
    one_way_cost_bps: float = 7.0,
) -> dict[str, pd.DataFrame | dict[str, float]]:
    universe = load_universe(report_path, membership_path)
    close, _ = load_price_matrix(price_base, universe)
    close = close.dropna(axis=1, how="all")
    lookup = build_membership_lookup(universe)
    rebalance_dates = compute_rebalance_dates(close.index, rebalance)
    weight_rows = []
    current = {c: 0.0 for c in close.columns}
    for dt in close.index:
        if dt in rebalance_dates:
            active = [c for c in close.columns if membership_sector(c, dt, lookup) is not None and pd.notna(close.loc[dt, c])]
            current = {c: 0.0 for c in close.columns}
            if active:
                w = 1.0 / len(active)
                for c in active:
                    current[c] = w
        weight_rows.append({"date": dt, **current})
    weights = pd.DataFrame(weight_rows).set_index("date").reindex(close.index).ffill().fillna(0.0)
    rets = close.pct_change(fill_method=None).fillna(0.0)
    shifted = weights.shift(1).fillna(0.0)
    gross = (shifted * rets).sum(axis=1)
    turnover = weights.diff().abs().sum(axis=1).fillna(0.0)
    net = gross - turnover * (one_way_cost_bps / 10000.0)
    nav = (1.0 + net).cumprod()
    years = max((nav.index[-1] - nav.index[0]).days / 365.25, 1 / 365.25)
    summary = {
        "FinalNAV": float(nav.iloc[-1]),
        "CAGR": float(nav.iloc[-1] ** (1.0 / years) - 1.0),
        "MDD": max_drawdown(nav.reset_index(drop=True)),
        "Sharpe": annualized_sharpe(net),
        "AnnualTurnover": float(turnover.mean() * 252.0),
        "AvgGrossExposure": float(weights.sum(axis=1).mean()),
        "AvgHoldings": float((weights > 0).sum(axis=1).mean()),
        "UniverseSize": int(close.shape[1]),
        "UniverseBiasNote": "SAME_UNIVERSE_EQUAL_WEIGHT_MONTHLY",
        "FirstDate": str(nav.index[0].date()),
        "LastDate": str(nav.index[-1].date()),
    }
    nav_df = pd.DataFrame({"date": nav.index, "gross_return": gross.values, "net_return": net.values, "turnover": turnover.values, "nav": nav.values})
    return {"summary": summary, "nav": nav_df, "weights": weights}


def fetch_umd_daily(cache_path: Path) -> pd.DataFrame:
    cached = pd.read_csv(cache_path, parse_dates=["date"]) if cache_path.exists() else pd.DataFrame()
    try:
        raw = requests.get(FF_MOM_URL, timeout=60)
        raw.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(raw.content)) as zf:
            text = zf.read(zf.namelist()[0]).decode("utf-8", errors="ignore")
    except Exception:
        if not cached.empty:
            return cached
        raise

    lines = text.splitlines()
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith(",Mom"):
            start_idx = i
            continue
        if start_idx is not None and i > start_idx and not line.strip():
            end_idx = i
            break
    if start_idx is None or end_idx is None:
        raise RuntimeError("Could not parse daily momentum factor.")

    mom = pd.read_csv(io.StringIO("\n".join(lines[start_idx:end_idx])))
    mom = mom.rename(columns={mom.columns[0]: "date", mom.columns[1]: "UMD"})
    mom["date"] = pd.to_datetime(mom["date"].astype(str), format="%Y%m%d", errors="coerce")
    mom["UMD"] = pd.to_numeric(mom["UMD"], errors="coerce") / 100.0
    mom = mom.dropna().reset_index(drop=True)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    mom.to_csv(cache_path, index=False)
    return mom


def load_factor_frame(ff5_path: Path, umd_path: Path) -> pd.DataFrame:
    ff5 = pd.read_csv(ff5_path, parse_dates=["date"])
    umd = fetch_umd_daily(umd_path)
    return ff5.merge(umd, on="date", how="inner").sort_values("date").reset_index(drop=True)


def factor_regression_rows(nav_df: pd.DataFrame, strategy: str, factors: pd.DataFrame) -> list[dict]:
    nav = nav_df.copy()
    nav["date"] = pd.to_datetime(nav["date"])
    nav["net_return"] = pd.to_numeric(nav["net_return"], errors="coerce")
    merged = nav.merge(factors, on="date", how="inner").dropna(subset=["net_return", "RF"])
    merged["ExcessReturn"] = merged["net_return"] - merged["RF"]

    specs = {
        "CAPM": ["Mkt-RF"],
        "CARHART4": ["Mkt-RF", "SMB", "HML", "UMD"],
        "FF5": ["Mkt-RF", "SMB", "HML", "RMW", "CMA"],
        "FF5_UMD": ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"],
    }
    rows = []
    for spec, cols in specs.items():
        df = merged[["ExcessReturn", *cols]].dropna().copy()
        if len(df) < 60:
            continue
        x = sm.add_constant(df[cols])
        model = sm.OLS(df["ExcessReturn"], x).fit(cov_type="HAC", cov_kwds={"maxlags": 5})
        row = {
            "Strategy": strategy,
            "Model": spec,
            "Obs": int(len(df)),
            "AlphaDaily": float(model.params.get("const", np.nan)),
            "AlphaAnnual": float(model.params.get("const", np.nan) * 252.0),
            "AlphaTstatNW": float(model.tvalues.get("const", np.nan)),
            "AdjR2": float(model.rsquared_adj),
        }
        for col in ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "UMD"]:
            row[f"Beta_{col}"] = float(model.params.get(col, np.nan))
            row[f"T_{col}"] = float(model.tvalues.get(col, np.nan))
        rows.append(row)
    return rows


def break_even_one_way_cost_bps(
    stock_nav: pd.DataFrame,
    benchmark_nav: pd.DataFrame,
) -> pd.DataFrame:
    s = stock_nav.copy()
    b = benchmark_nav.copy()
    s["date"] = pd.to_datetime(s["date"])
    b["date"] = pd.to_datetime(b["date"])
    merged = s.merge(
        b[["date", "net_return"]].rename(columns={"net_return": "benchmark_net_return"}),
        on="date",
        how="inner",
    ).dropna(subset=["gross_return", "turnover", "benchmark_net_return"])
    merged["gross_excess"] = pd.to_numeric(merged["gross_return"], errors="coerce") - pd.to_numeric(merged["benchmark_net_return"], errors="coerce")
    merged["turnover"] = pd.to_numeric(merged["turnover"], errors="coerce").fillna(0.0)
    mean_turnover = float(merged["turnover"].mean())
    mean_gross_excess = float(merged["gross_excess"].mean())
    be_mean_bps = float(mean_gross_excess / mean_turnover * 10000.0) if mean_turnover > 0 else np.nan

    def cagr_diff(bps: float) -> float:
        net_excess = merged["gross_excess"] - merged["turnover"] * (bps / 10000.0)
        nav = (1.0 + net_excess).cumprod()
        years = max((merged["date"].iloc[-1] - merged["date"].iloc[0]).days / 365.25, 1 / 365.25)
        return float(nav.iloc[-1] ** (1.0 / years) - 1.0)

    lo = 0.0
    hi = 500.0
    diff_lo = cagr_diff(lo)
    diff_hi = cagr_diff(hi)
    be_cagr_bps = np.nan
    if diff_lo >= 0 and diff_hi <= 0:
        for _ in range(50):
            mid = (lo + hi) / 2.0
            diff_mid = cagr_diff(mid)
            if diff_mid > 0:
                lo = mid
            else:
                hi = mid
        be_cagr_bps = (lo + hi) / 2.0

    rows = [
        {
            "Strategy": "US Stock Mom12_1",
            "Benchmark": "US Same-Universe EW Benchmark",
            "MeanGrossExcessDaily": mean_gross_excess,
            "MeanTurnoverDaily": mean_turnover,
            "BreakEvenOneWayBps_MeanExcessZero": be_mean_bps,
            "BreakEvenOneWayBps_CAGRMatchBenchmark": be_cagr_bps,
        }
    ]
    return pd.DataFrame(rows)


def capacity_diagnostics(
    stock_result: dict[str, pd.DataFrame | dict[str, float]],
    aum_levels: list[float] | None = None,
    participation_thresholds: list[float] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if aum_levels is None:
        aum_levels = [1_000_000.0, 5_000_000.0, 10_000_000.0, 25_000_000.0, 50_000_000.0, 100_000_000.0]
    if participation_thresholds is None:
        participation_thresholds = [0.001, 0.005, 0.01, 0.02, 0.05]

    weights = stock_result["weights"].copy()
    traded_value = stock_result["traded_value"].copy()
    adv60 = traded_value.rolling(60, min_periods=60).median()
    deltas = weights.diff().abs().fillna(0.0)

    rows = []
    cap_rows = []
    for dt in deltas.index:
        delta_row = deltas.loc[dt]
        adv_row = adv60.loc[dt] if dt in adv60.index else pd.Series(dtype=float)
        for symbol, dw in delta_row.items():
            if not pd.notna(dw) or float(dw) <= 0:
                continue
            adv = float(pd.to_numeric(adv_row.get(symbol), errors="coerce"))
            if not np.isfinite(adv) or adv <= 0:
                continue
            for aum in aum_levels:
                participation = float(aum * float(dw) / adv)
                rows.append(
                    {
                        "Date": str(pd.Timestamp(dt).date()),
                        "Symbol": symbol,
                        "WeightChange": float(dw),
                        "ADV60USD": adv,
                        "AUMUSD": aum,
                        "ParticipationRate": participation,
                    }
                )
            for threshold in participation_thresholds:
                max_aum = float(threshold * adv / float(dw))
                cap_rows.append(
                    {
                        "Date": str(pd.Timestamp(dt).date()),
                        "Symbol": symbol,
                        "WeightChange": float(dw),
                        "ADV60USD": adv,
                        "ParticipationThreshold": threshold,
                        "MaxAUMUSD": max_aum,
                    }
                )

    participation_df = pd.DataFrame(rows)
    capacity_limits = pd.DataFrame(cap_rows)
    if capacity_limits.empty:
        return participation_df, capacity_limits

    summary_rows = []
    for threshold, grp in capacity_limits.groupby("ParticipationThreshold"):
        worst = grp.sort_values("MaxAUMUSD").iloc[0]
        summary_rows.append(
            {
                "ParticipationThreshold": float(threshold),
                "CapacityAUMUSD": float(worst["MaxAUMUSD"]),
                "BottleneckDate": worst["Date"],
                "BottleneckSymbol": worst["Symbol"],
                "BottleneckWeightChange": float(worst["WeightChange"]),
                "BottleneckADV60USD": float(worst["ADV60USD"]),
            }
        )
    return participation_df, pd.DataFrame(summary_rows)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate US stock momentum vs ETF baselines.")
    p.add_argument("--price-base-stock", type=str, default="data/prices_us_stock_sp100")
    p.add_argument("--report-path-stock", type=str, default="backtests/us_stock_sp100_universe.csv")
    p.add_argument("--membership-path-stock", type=str, default="")
    p.add_argument("--price-base-etf", type=str, default="data/prices_us_etf_core")
    p.add_argument("--report-path-etf", type=str, default="backtests/us_etf_core_universe.csv")
    p.add_argument("--factor-cache", type=str, default="data/us_ff5_daily.csv")
    p.add_argument("--factor-cache-umd", type=str, default="data/us_umd_daily.csv")
    p.add_argument("--output-dir", type=str, default="backtests/us_momentum_eval_20260329")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    stock = run_stock_mom(
        price_base=Path(args.price_base_stock),
        report_path=Path(args.report_path_stock),
        membership_path=Path(args.membership_path_stock) if args.membership_path_stock else None,
        top_n=20,
        max_per_sector=3,
        min_median_value=100_000_000.0,
        min_price=10.0,
        rebalance="ME",
        one_way_cost_bps=7.0,
    )
    residual = run_residual(
        price_base=Path(args.price_base_etf),
        factor_cache=Path(args.factor_cache),
        regression_window=756,
        top_k=3,
        rebalance="ME",
        one_way_cost_bps=7.0,
    )
    same_universe = run_same_universe_benchmark(
        price_base=Path(args.price_base_stock),
        report_path=Path(args.report_path_stock),
        membership_path=Path(args.membership_path_stock) if args.membership_path_stock else None,
        rebalance="ME",
        one_way_cost_bps=7.0,
    )
    etf = run_etf_riskbudget(
        price_base=Path(args.price_base_etf),
        report_path=Path(args.report_path_etf),
        lookback=120,
        rebalance="W-FRI",
        max_weight=0.35,
        min_median_value=5_000_000.0,
        one_way_cost_bps=7.0,
    )

    compare = pd.DataFrame(
        [
            {"Strategy": "US ETF RiskBudget", "ValidationStatus": "BASELINE", "Notes": "adjusted_close_weekly_riskbudget", **summarize_nav(etf["nav"][["date", "net_return", "nav"]])},
            {"Strategy": "US Same-Universe EW Benchmark", "ValidationStatus": "REFERENCE", "Notes": "monthly_equal_weight_active_members", **summarize_nav(same_universe["nav"][["date", "net_return", "nav"]])},
            {"Strategy": "US Residual Sector Rotation", "ValidationStatus": "RESEARCH_ONLY", "Notes": f"factor_last_date={residual['summary'].get('FactorLastDate','')}", **summarize_nav(residual["nav"][["date", "net_return", "nav"]])},
            {"Strategy": "US Stock Mom12_1", "ValidationStatus": "RESEARCH_ONLY", "Notes": str(stock["summary"].get("UniverseBiasNote", "")), **summarize_nav(stock["nav"][["date", "net_return", "nav"]])},
        ]
    )
    compare.to_csv(out_dir / "us_compare.csv", index=False)

    cost_rows = []
    for bps in [5.0, 7.0, 10.0, 15.0, 25.0]:
        r = run_stock_mom(
            price_base=Path(args.price_base_stock),
            report_path=Path(args.report_path_stock),
            membership_path=Path(args.membership_path_stock) if args.membership_path_stock else None,
            top_n=20,
            max_per_sector=3,
            min_median_value=100_000_000.0,
            min_price=10.0,
            rebalance="ME",
            one_way_cost_bps=bps,
        )
        s = summarize_nav(r["nav"][["date", "net_return", "nav"]])
        cost_rows.append({"Strategy": "US Stock Mom12_1", "OneWayCostBps": bps, **s})
    pd.DataFrame(cost_rows).to_csv(out_dir / "us_stock_mom12_1_cost.csv", index=False)

    wf_rows = []
    wf_rows += walkforward_rows(etf["nav"][["date", "net_return", "nav"]], "US ETF RiskBudget", train_years=5, test_years=2, step_years=1)
    wf_rows += walkforward_rows(same_universe["nav"][["date", "net_return", "nav"]], "US Same-Universe EW Benchmark", train_years=5, test_years=2, step_years=1)
    wf_rows += walkforward_rows(residual["nav"][["date", "net_return", "nav"]], "US Residual Sector Rotation", train_years=5, test_years=2, step_years=1)
    wf_rows += walkforward_rows(stock["nav"][["date", "net_return", "nav"]], "US Stock Mom12_1", train_years=5, test_years=2, step_years=1)
    wf = pd.DataFrame(wf_rows)
    wf.to_csv(out_dir / "us_walkforward_results.csv", index=False)
    wf_summary = wf.groupby("Strategy", as_index=False).agg(
        WindowCount=("CAGR", "count"),
        MedianCAGR=("CAGR", "median"),
        WorstCAGR=("CAGR", "min"),
        WorstMDD=("MDD", "min"),
        MedianSharpe=("Sharpe", "median"),
    )
    wf_summary.to_csv(out_dir / "us_walkforward_summary.csv", index=False)

    stock_portfolio = stock["portfolio"]
    stock["nav"].to_csv(out_dir / "us_stock_mom12_1_nav.csv", index=False)
    stock_portfolio.to_csv(out_dir / "us_stock_mom12_1_portfolio.csv", index=False)
    pd.DataFrame([etf["summary"]]).to_csv(out_dir / "us_etf_riskbudget_summary.csv", index=False)
    etf["nav"].to_csv(out_dir / "us_etf_riskbudget_nav.csv", index=False)
    pd.DataFrame([same_universe["summary"]]).to_csv(out_dir / "us_same_universe_ew_summary.csv", index=False)
    same_universe["nav"].to_csv(out_dir / "us_same_universe_ew_nav.csv", index=False)
    mincap = min_capital_for_one_share_each(out_dir / "us_stock_mom12_1_portfolio.csv")
    mincap.to_csv(out_dir / "us_stock_mom12_1_min_capital.csv", index=False)
    if not mincap.empty:
        min_summary = pd.DataFrame(
            [
                {
                    "Strategy": "US Stock Mom12_1",
                    "AsOfDate": str(stock_portfolio["AsOfDate"].iloc[0]),
                    "RequiredCapitalForAllOneShareUSD": float(mincap["MinCapitalForOneShareUSD"].max()),
                }
            ]
        )
        min_summary.to_csv(out_dir / "us_stock_mom12_1_min_capital_summary.csv", index=False)

    factors = load_factor_frame(Path(args.factor_cache), Path(args.factor_cache_umd))
    reg_rows = []
    reg_rows += factor_regression_rows(etf["nav"][["date", "net_return", "nav"]], "US ETF RiskBudget", factors)
    reg_rows += factor_regression_rows(same_universe["nav"][["date", "net_return", "nav"]], "US Same-Universe EW Benchmark", factors)
    reg_rows += factor_regression_rows(residual["nav"][["date", "net_return", "nav"]], "US Residual Sector Rotation", factors)
    reg_rows += factor_regression_rows(stock["nav"][["date", "net_return", "nav"]], "US Stock Mom12_1", factors)
    pd.DataFrame(reg_rows).to_csv(out_dir / "us_factor_regressions.csv", index=False)

    break_even_df = break_even_one_way_cost_bps(stock["nav"][["date", "gross_return", "turnover", "nav"]], same_universe["nav"][["date", "net_return", "nav"]])
    break_even_df.to_csv(out_dir / "us_stock_mom12_1_break_even_cost.csv", index=False)

    participation_df, capacity_df = capacity_diagnostics(stock)
    participation_df.to_csv(out_dir / "us_stock_mom12_1_capacity_participation.csv", index=False)
    capacity_df.to_csv(out_dir / "us_stock_mom12_1_capacity_summary.csv", index=False)

    print(compare.to_string(index=False))
    print()
    print(wf_summary.to_string(index=False))


if __name__ == "__main__":
    main()
