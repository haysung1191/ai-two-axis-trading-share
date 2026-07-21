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


FACTOR_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_daily_CSV.zip"
SECTOR_ETFS = ["XLE", "XLF", "XLI", "XLK", "XLP", "XLV", "XLY"]
SAFE_ETF = "SHY"


def load_price_series(base: Path, ticker: str) -> pd.Series:
    path = base / "etf" / f"{ticker}.csv.gz"
    df = pd.read_csv(path, compression="gzip", parse_dates=["date"])
    s = pd.to_numeric(df["close"], errors="coerce")
    s.index = pd.to_datetime(df["date"])
    s = s.dropna()
    s.name = ticker
    return s


def load_prices(base: Path, tickers: list[str]) -> pd.DataFrame:
    frames = [load_price_series(base, ticker) for ticker in tickers]
    return pd.concat(frames, axis=1).sort_index()


def fetch_ff5_daily(cache_path: Path) -> pd.DataFrame:
    cached = pd.read_csv(cache_path, parse_dates=["date"]) if cache_path.exists() else pd.DataFrame()
    try:
        raw = requests.get(FACTOR_URL, timeout=60)
        raw.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(raw.content)) as zf:
            first_name = zf.namelist()[0]
            text = zf.read(first_name).decode("utf-8", errors="ignore")
    except Exception:
        if not cached.empty:
            return cached
        raise

    lines = text.splitlines()
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith(",Mkt-RF,SMB,HML,RMW,CMA,RF"):
            start_idx = i
            continue
        if start_idx is not None and i > start_idx and not line.strip():
            end_idx = i
            break
    if start_idx is None or end_idx is None:
        raise RuntimeError("Could not parse FF5 daily data.")

    data_lines = lines[start_idx:end_idx]
    csv_text = "\n".join(data_lines)
    ff = pd.read_csv(io.StringIO(csv_text))
    ff = ff.rename(columns={ff.columns[0]: "date"})
    ff["date"] = pd.to_datetime(ff["date"].astype(str), format="%Y%m%d", errors="coerce")
    ff = ff.dropna(subset=["date"]).copy()
    for col in ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"]:
        ff[col] = pd.to_numeric(ff[col], errors="coerce") / 100.0
    ff = ff.dropna().reset_index(drop=True)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    ff.to_csv(cache_path, index=False)
    return ff


def compute_rebalance_dates(index: pd.DatetimeIndex, rebalance: str) -> set[pd.Timestamp]:
    if str(rebalance).upper() == "ME":
        month_ends = pd.Series(index=index, data=index)
        return set(month_ends.groupby(index.to_period("M")).tail(1).tolist())
    return set(index.intersection(index.to_series().resample(rebalance).last().dropna().index))


def annualized_sharpe(daily_returns: pd.Series) -> float:
    r = pd.to_numeric(daily_returns, errors="coerce").dropna()
    if len(r) < 2:
        return 0.0
    vol = float(r.std(ddof=0))
    if vol <= 0:
        return 0.0
    return float(r.mean() / vol * np.sqrt(252.0))


def max_drawdown(nav: pd.Series) -> float:
    peak = nav.cummax()
    dd = nav / peak - 1.0
    return float(dd.min()) if not dd.empty else 0.0


def annualized_turnover(weights: pd.DataFrame) -> float:
    if weights.empty:
        return 0.0
    turnover = weights.fillna(0.0).diff().abs().sum(axis=1).fillna(0.0)
    return float(turnover.mean() * 252.0)


def fit_alpha(window_excess: pd.Series, window_factors: pd.DataFrame) -> float:
    df = pd.concat([window_excess.rename("y"), window_factors], axis=1).dropna()
    if len(df) < 252:
        return np.nan
    x = sm.add_constant(df[["Mkt-RF", "SMB", "HML", "RMW", "CMA"]])
    model = sm.OLS(df["y"], x).fit()
    return float(model.params.get("const", np.nan) * 252.0)


def compute_weights(
    prices: pd.DataFrame,
    ff: pd.DataFrame,
    regression_window: int,
    top_k: int,
    rebalance: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    returns = prices.pct_change(fill_method=None)
    ff = ff.set_index("date").reindex(prices.index)
    excess = returns.sub(ff["RF"], axis=0)
    rebalance_dates = compute_rebalance_dates(prices.index, rebalance)

    weight_rows = []
    alpha_rows = []
    current = {ticker: 0.0 for ticker in prices.columns}
    for dt in prices.index:
        if dt in rebalance_dates:
            alpha_map: dict[str, float] = {}
            start_loc = prices.index.get_loc(dt)
            if start_loc >= regression_window:
                window_idx = prices.index[start_loc - regression_window:start_loc]
                factor_window = ff.loc[window_idx, ["Mkt-RF", "SMB", "HML", "RMW", "CMA"]]
                for ticker in SECTOR_ETFS:
                    alpha_map[ticker] = fit_alpha(excess.loc[window_idx, ticker], factor_window)
                ranked = sorted(
                    [(ticker, alpha) for ticker, alpha in alpha_map.items() if pd.notna(alpha) and alpha > 0],
                    key=lambda x: x[1],
                    reverse=True,
                )[:top_k]
                current = {ticker: 0.0 for ticker in prices.columns}
                if ranked:
                    per_weight = 1.0 / top_k
                    for ticker, _ in ranked:
                        current[ticker] = per_weight
                    current[SAFE_ETF] = max(0.0, 1.0 - per_weight * len(ranked))
                else:
                    current[SAFE_ETF] = 1.0
            alpha_rows.append({"date": dt, **{ticker: alpha_map.get(ticker, np.nan) for ticker in SECTOR_ETFS}})
        weight_rows.append({"date": dt, **current})

    weights = pd.DataFrame(weight_rows).set_index("date").reindex(prices.index).ffill().fillna(0.0)
    alphas = pd.DataFrame(alpha_rows).set_index("date") if alpha_rows else pd.DataFrame()
    return weights, alphas


def run_backtest(
    price_base: Path,
    factor_cache: Path,
    regression_window: int,
    top_k: int,
    rebalance: str,
    one_way_cost_bps: float,
) -> dict[str, pd.DataFrame | dict[str, float]]:
    tickers = sorted(set(SECTOR_ETFS + [SAFE_ETF]))
    prices = load_prices(price_base, tickers).dropna()
    ff = fetch_ff5_daily(factor_cache)
    ff_last = pd.to_datetime(ff["date"]).max()
    prices = prices.loc[prices.index <= ff_last].copy()
    weights, alphas = compute_weights(prices, ff, regression_window, top_k, rebalance)
    returns = prices.pct_change(fill_method=None).fillna(0.0)
    shifted_weights = weights.shift(1).fillna(0.0)
    gross = (shifted_weights * returns).sum(axis=1)
    daily_turnover = weights.fillna(0.0).diff().abs().sum(axis=1).fillna(0.0)
    cost = daily_turnover * (one_way_cost_bps / 10000.0)
    net = gross - cost
    nav = (1.0 + net).cumprod()

    years = max((nav.index[-1] - nav.index[0]).days / 365.25, 1 / 365.25)
    summary = {
        "FinalNAV": float(nav.iloc[-1]),
        "CAGR": float(nav.iloc[-1] ** (1.0 / years) - 1.0),
        "MDD": max_drawdown(nav),
        "Sharpe": annualized_sharpe(net),
        "AnnualTurnover": annualized_turnover(weights),
        "AvgGrossExposure": float(weights.sum(axis=1).mean()),
        "AvgHoldings": float((weights > 0).sum(axis=1).mean()),
        "FactorLastDate": str(pd.to_datetime(ff["date"]).max().date()),
        "FirstDate": str(nav.index[0].date()),
        "LastDate": str(nav.index[-1].date()),
    }

    nav_df = pd.DataFrame(
        {
            "date": nav.index,
            "gross_return": gross.values,
            "net_return": net.values,
            "turnover": daily_turnover.values,
            "nav": nav.values,
        }
    )
    return {"summary": summary, "nav": nav_df, "weights": weights, "alphas": alphas, "prices": prices}


def build_current_portfolio(weights: pd.DataFrame, prices: pd.DataFrame, alphas: pd.DataFrame) -> pd.DataFrame:
    as_of = weights.index[-1]
    w = weights.loc[as_of]
    rows = []
    latest_alpha = alphas.loc[:as_of].iloc[-1] if not alphas.empty and not alphas.loc[:as_of].empty else pd.Series(dtype=float)
    rank_order = w[w > 0].sort_values(ascending=False).index.tolist()
    rank_map = {ticker: i + 1 for i, ticker in enumerate(rank_order)}
    for ticker, weight in w[w > 0].sort_values(ascending=False).items():
        rows.append(
            {
                "AsOfDate": as_of.strftime("%Y-%m-%d"),
                "Ticker": ticker,
                "TargetWeight": float(weight),
                "CurrentPrice": float(prices.loc[as_of, ticker]),
                "SignalRank": rank_map.get(ticker, np.nan),
                "ResidualAlpha": float(latest_alpha.get(ticker, np.nan)) if ticker in SECTOR_ETFS else np.nan,
                "Notes": "safe_asset" if ticker == SAFE_ETF else "positive_residual_alpha",
            }
        )
    return pd.DataFrame(rows)


def build_order_sheet(portfolio: pd.DataFrame, capital: float, trade_date: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for _, r in portfolio.iterrows():
        px = float(r["CurrentPrice"])
        target = capital * float(r["TargetWeight"])
        shares = int(target // px) if px > 0 else 0
        notional = shares * px
        rows.append(
            {
                "TradeDate": trade_date,
                "AsOfDate": r["AsOfDate"],
                "Ticker": r["Ticker"],
                "TargetWeight": r["TargetWeight"],
                "CurrentPriceUSD": px,
                "TargetNotionalUSD": round(target, 2),
                "OrderShares": shares,
                "OrderNotionalUSD": round(notional, 2),
                "Action": "BUY",
            }
        )
    order_df = pd.DataFrame(rows)
    summary = pd.DataFrame(
        [
            {
                "TradeDate": trade_date,
                "AsOfDate": str(portfolio["AsOfDate"].iloc[0]),
                "PlannedCapitalUSD": capital,
                "PlannedInvestedUSD": float(order_df["OrderNotionalUSD"].sum()),
                "ResidualCashUSD": float(capital - order_df["OrderNotionalUSD"].sum()),
                "HoldingsCount": int((order_df["OrderShares"] > 0).sum()),
            }
        ]
    )
    return order_df, summary


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="US ETF residual sector rotation research backtest.")
    p.add_argument("--price-base", type=str, default="data/prices_us_etf_core")
    p.add_argument("--factor-cache", type=str, default="data/us_ff5_daily.csv")
    p.add_argument("--output-dir", type=str, default="backtests/us_residual_sector_rotation_20260328")
    p.add_argument("--regression-window", type=int, default=756)
    p.add_argument("--top-k", type=int, default=3)
    p.add_argument("--rebalance", type=str, default="ME")
    p.add_argument("--one-way-cost-bps", type=float, default=7.0)
    p.add_argument("--order-capital-usd", type=float, default=2000.0)
    p.add_argument("--trade-date", type=str, default="2026-03-30")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    result = run_backtest(
        price_base=Path(args.price_base),
        factor_cache=Path(args.factor_cache),
        regression_window=args.regression_window,
        top_k=args.top_k,
        rebalance=args.rebalance,
        one_way_cost_bps=args.one_way_cost_bps,
    )
    summary_df = pd.DataFrame([result["summary"]])
    portfolio_df = build_current_portfolio(result["weights"], result["prices"], result["alphas"])
    order_df, order_summary_df = build_order_sheet(portfolio_df, args.order_capital_usd, args.trade_date)

    summary_df.to_csv(out_dir / "us_residual_sector_rotation_summary.csv", index=False)
    result["nav"].to_csv(out_dir / "us_residual_sector_rotation_nav.csv", index=False)
    portfolio_df.to_csv(out_dir / "us_residual_sector_rotation_portfolio.csv", index=False)
    order_df.to_csv(out_dir / f"us_residual_sector_rotation_order_sheet_{int(args.order_capital_usd)}usd.csv", index=False)
    order_summary_df.to_csv(out_dir / f"us_residual_sector_rotation_order_sheet_{int(args.order_capital_usd)}usd_summary.csv", index=False)
    print(summary_df.to_string(index=False))
    print()
    print(portfolio_df.to_string(index=False))


if __name__ == "__main__":
    main()
