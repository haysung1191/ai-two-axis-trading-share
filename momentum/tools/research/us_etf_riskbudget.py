import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import numpy as np
import pandas as pd

from kis_backtest_from_prices import StrategyConfig, _cap_weights_to_target, _risk_budget_weights


def load_report(report_path: Path) -> pd.DataFrame:
    df = pd.read_csv(report_path)
    return df[df["Status"].astype(str).eq("OK")].copy().reset_index(drop=True)


def load_price_matrix(price_base: Path, tickers: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    close_frames = []
    value_frames = []
    for ticker in tickers:
        path = price_base / "etf" / f"{ticker}.csv.gz"
        if not path.exists():
            continue
        df = pd.read_csv(path, compression="gzip", parse_dates=["date"])
        if df.empty:
            continue
        idx = pd.to_datetime(df["date"])
        close = pd.to_numeric(df["close"], errors="coerce")
        volume = pd.to_numeric(df["volume"], errors="coerce").fillna(0.0)
        close_frames.append(pd.Series(close.values, index=idx, name=ticker))
        value_frames.append(pd.Series((close * volume).values, index=idx, name=ticker))
    close_df = pd.concat(close_frames, axis=1).sort_index()
    value_df = pd.concat(value_frames, axis=1).sort_index()
    return close_df, value_df


def compute_rebalance_dates(index: pd.DatetimeIndex, rebalance: str) -> set[pd.Timestamp]:
    if str(rebalance).upper() == "ME":
        month_ends = pd.Series(index=index, data=index)
        return set(month_ends.groupby(index.to_period("M")).tail(1).tolist())
    return set(index.intersection(index.to_series().resample(rebalance).last().dropna().index))


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


def annualized_turnover(weights: pd.DataFrame) -> float:
    turnover = weights.fillna(0.0).diff().abs().sum(axis=1).fillna(0.0)
    return float(turnover.mean() * 252.0)


def build_weights(
    close: pd.DataFrame,
    traded_value: pd.DataFrame,
    lookback: int,
    rebalance: str,
    max_weight: float,
    min_median_value: float,
) -> pd.DataFrame:
    returns = close.pct_change(fill_method=None)
    median_value = traded_value.rolling(60, min_periods=60).median()
    bars = close.notna().cumsum()
    rebalance_dates = compute_rebalance_dates(close.index, rebalance)
    stg = StrategyConfig(
        name="US ETF RiskBudget",
        rebalance=rebalance,
        top_n_stock=0,
        top_n_etf=len(close.columns),
        fee_rate=0.0,
        max_weight=max_weight,
        use_etf_risk_budget=True,
        fixed_sleeve_weights={"stock": 0.0, "etf": 1.0},
        use_point_in_time_universe=False,
        risk_budget_lookback=lookback,
        risk_budget_shrinkage=0.35,
        risk_budget_iv_blend=0.50,
    )
    rows = []
    current = {ticker: 0.0 for ticker in close.columns}
    for dt in close.index:
        if dt in rebalance_dates:
            eligible = (
                close.loc[dt].notna()
                & (bars.loc[dt] >= lookback)
                & (median_value.loc[dt] >= min_median_value)
            )
            tickers = list(close.columns[eligible])
            if tickers:
                start_loc = close.index.get_loc(dt)
                window_idx = close.index[max(0, start_loc - lookback):start_loc]
                ret_window = returns.loc[window_idx, tickers]
                raw = _risk_budget_weights(ret_window, tickers, stg)
                capped = _cap_weights_to_target(raw, max_weight=max_weight, target_gross=1.0)
                current = {ticker: float(capped.get(ticker, 0.0)) for ticker in close.columns}
            else:
                current = {ticker: 0.0 for ticker in close.columns}
        rows.append({"date": dt, **current})
    return pd.DataFrame(rows).set_index("date").reindex(close.index).ffill().fillna(0.0)


def run_backtest(
    price_base: Path,
    report_path: Path,
    lookback: int,
    rebalance: str,
    max_weight: float,
    min_median_value: float,
    one_way_cost_bps: float,
) -> dict[str, pd.DataFrame | dict[str, float]]:
    report = load_report(report_path)
    tickers = sorted(report["Ticker"].astype(str).unique().tolist())
    close, traded_value = load_price_matrix(price_base, tickers)
    weights = build_weights(close, traded_value, lookback, rebalance, max_weight, min_median_value)
    returns = close.pct_change(fill_method=None).fillna(0.0)
    shifted = weights.shift(1).fillna(0.0)
    gross = (shifted * returns).sum(axis=1)
    turnover = weights.fillna(0.0).diff().abs().sum(axis=1).fillna(0.0)
    cost = turnover * (one_way_cost_bps / 10000.0)
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
        "UniverseSize": int(len(tickers)),
        "FirstDate": str(nav.index[0].date()),
        "LastDate": str(nav.index[-1].date()),
        "PriceBasis": "adjusted_close",
    }
    nav_df = pd.DataFrame(
        {
            "date": nav.index,
            "gross_return": gross.values,
            "net_return": net.values,
            "turnover": turnover.values,
            "nav": nav.values,
        }
    )
    return {"summary": summary, "nav": nav_df, "weights": weights, "prices": close}


def build_current_portfolio(weights: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    as_of = weights.index[-1]
    w = weights.loc[as_of]
    rows = []
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
            }
        )
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="US ETF RiskBudget baseline on adjusted ETF prices.")
    p.add_argument("--price-base", type=str, default="data/prices_us_etf_core")
    p.add_argument("--report-path", type=str, default="backtests/us_etf_core_universe.csv")
    p.add_argument("--output-dir", type=str, default="backtests/us_etf_riskbudget_20260329")
    p.add_argument("--lookback", type=int, default=120)
    p.add_argument("--rebalance", type=str, default="W-FRI")
    p.add_argument("--max-weight", type=float, default=0.35)
    p.add_argument("--min-median-value", type=float, default=5_000_000.0)
    p.add_argument("--one-way-cost-bps", type=float, default=7.0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = run_backtest(
        price_base=Path(args.price_base),
        report_path=Path(args.report_path),
        lookback=args.lookback,
        rebalance=args.rebalance,
        max_weight=args.max_weight,
        min_median_value=args.min_median_value,
        one_way_cost_bps=args.one_way_cost_bps,
    )
    summary_df = pd.DataFrame([result["summary"]])
    portfolio = build_current_portfolio(result["weights"], result["prices"])
    summary_df.to_csv(out_dir / "us_etf_riskbudget_summary.csv", index=False)
    result["nav"].to_csv(out_dir / "us_etf_riskbudget_nav.csv", index=False)
    portfolio.to_csv(out_dir / "us_etf_riskbudget_portfolio.csv", index=False)
    print(summary_df.to_string(index=False))
    print()
    print(portfolio.to_string(index=False))


if __name__ == "__main__":
    main()
