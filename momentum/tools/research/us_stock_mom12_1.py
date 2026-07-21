import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import numpy as np
import pandas as pd


def load_universe(report_path: Path, membership_path: Path | None = None) -> pd.DataFrame:
    df = pd.read_csv(report_path)
    df = df[df["Status"].astype(str).eq("OK")].copy()
    if membership_path is None or not membership_path.exists():
        out = df[["Symbol", "Name", "Sector"]].drop_duplicates().sort_values("Symbol").reset_index(drop=True)
        out["StartDate"] = pd.NaT
        out["EndDate"] = pd.NaT
        out["UniverseType"] = "STATIC_CURRENT_MEMBERSHIP"
        return out

    members = pd.read_csv(membership_path, parse_dates=["StartDate", "EndDate"])
    merged = members.merge(
        df[["Symbol", "Name", "Sector", "YahooTicker", "Status", "Bars", "FirstDate", "LastDate"]],
        on=["Symbol", "YahooTicker"],
        how="inner",
        suffixes=("", "_report"),
    )
    if merged.empty:
        raise ValueError(f"No overlap between report and membership file: {membership_path}")
    merged["Name"] = merged["Name"].fillna(merged["Name_report"])
    merged["Sector"] = merged["Sector"].fillna(merged["Sector_report"])
    return (
        merged[["Symbol", "Name", "Sector", "StartDate", "EndDate", "UniverseType"]]
        .sort_values(["StartDate", "Symbol"])
        .reset_index(drop=True)
    )


def load_price_matrix(price_base: Path, universe: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    close_frames = []
    value_frames = []
    seen: set[str] = set()
    for _, r in universe.iterrows():
        symbol = str(r["Symbol"])
        if symbol in seen:
            continue
        seen.add(symbol)
        path = price_base / "stock" / f"{symbol}.csv.gz"
        if not path.exists():
            continue
        df = pd.read_csv(path, compression="gzip", parse_dates=["date"])
        if df.empty:
            continue
        s_close = pd.to_numeric(df["close"], errors="coerce")
        s_volume = pd.to_numeric(df["volume"], errors="coerce").fillna(0.0)
        idx = pd.to_datetime(df["date"])
        close_frames.append(pd.Series(s_close.values, index=idx, name=symbol))
        value_frames.append(pd.Series((s_close * s_volume).values, index=idx, name=symbol))
    close = pd.concat(close_frames, axis=1).sort_index()
    traded_value = pd.concat(value_frames, axis=1).sort_index()
    return close, traded_value


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


def compute_signal(close: pd.DataFrame) -> pd.DataFrame:
    return close.shift(21) / close.shift(252) - 1.0


def compute_rebalance_dates(index: pd.DatetimeIndex, rebalance: str) -> set[pd.Timestamp]:
    if str(rebalance).upper() == "ME":
        month_ends = pd.Series(index=index, data=index)
        return set(month_ends.groupby(index.to_period("M")).tail(1).tolist())
    return set(index.intersection(index.to_series().resample(rebalance).last().dropna().index))


def build_membership_lookup(universe: pd.DataFrame) -> dict[str, list[tuple[pd.Timestamp | None, pd.Timestamp | None, str]]]:
    lookup: dict[str, list[tuple[pd.Timestamp | None, pd.Timestamp | None, str]]] = {}
    for _, row in universe.iterrows():
        start = row.get("StartDate")
        end = row.get("EndDate")
        sector = str(row.get("Sector", "Unknown"))
        if pd.isna(start):
            start = None
        if pd.isna(end):
            end = None
        lookup.setdefault(str(row["Symbol"]), []).append((start, end, sector))
    return lookup


def membership_sector(symbol: str, dt: pd.Timestamp, membership_lookup: dict[str, list[tuple[pd.Timestamp | None, pd.Timestamp | None, str]]]) -> str | None:
    intervals = membership_lookup.get(symbol, [])
    if not intervals:
        return None
    for start, end, sector in intervals:
        if (start is None or dt >= start) and (end is None or dt <= end):
            return sector
    return None


def build_weights(
    close: pd.DataFrame,
    traded_value: pd.DataFrame,
    universe: pd.DataFrame,
    top_n: int,
    max_per_sector: int,
    min_median_value: float,
    min_price: float,
    rebalance: str,
    membership_lookup: dict[str, list[tuple[pd.Timestamp | None, pd.Timestamp | None, str]]],
) -> pd.DataFrame:
    signal = compute_signal(close)
    median_value_60 = traded_value.rolling(60, min_periods=60).median()
    bars = close.notna().cumsum()
    rebalance_dates = compute_rebalance_dates(close.index, rebalance)
    weight_rows = []
    current = {c: 0.0 for c in close.columns}

    for dt in close.index:
        if dt in rebalance_dates:
            active_map = {symbol: membership_sector(symbol, dt, membership_lookup) for symbol in close.columns}
            eligible = (
                signal.loc[dt].notna()
                & (signal.loc[dt] > 0)
                & (close.loc[dt] >= min_price)
                & (median_value_60.loc[dt] >= min_median_value)
                & (bars.loc[dt] >= 252)
                & pd.Series({symbol: active_map.get(symbol) is not None for symbol in close.columns})
            )
            ranked = (
                pd.DataFrame({"signal": signal.loc[dt], "eligible": eligible})
                .loc[lambda x: x["eligible"]]
                .sort_values("signal", ascending=False)
            )
            picks = []
            sector_counts: dict[str, int] = {}
            for symbol, row in ranked.iterrows():
                sector = str(active_map.get(symbol, "Unknown"))
                if sector_counts.get(sector, 0) >= max_per_sector:
                    continue
                picks.append(symbol)
                sector_counts[sector] = sector_counts.get(sector, 0) + 1
                if len(picks) >= top_n:
                    break
            current = {c: 0.0 for c in close.columns}
            if picks:
                w = 1.0 / len(picks)
                for symbol in picks:
                    current[symbol] = w
        weight_rows.append({"date": dt, **current})
    return pd.DataFrame(weight_rows).set_index("date").reindex(close.index).ffill().fillna(0.0)


def run_backtest(
    price_base: Path,
    report_path: Path,
    membership_path: Path | None,
    top_n: int,
    max_per_sector: int,
    min_median_value: float,
    min_price: float,
    rebalance: str,
    one_way_cost_bps: float,
) -> dict[str, pd.DataFrame | dict[str, float]]:
    universe = load_universe(report_path, membership_path)
    close, traded_value = load_price_matrix(price_base, universe)
    close = close.dropna(axis=1, how="all")
    traded_value = traded_value.reindex_like(close)
    membership_lookup = build_membership_lookup(universe)
    weights = build_weights(close, traded_value, universe, top_n, max_per_sector, min_median_value, min_price, rebalance, membership_lookup)
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
        "MDD": max_drawdown(nav),
        "Sharpe": annualized_sharpe(net),
        "AnnualTurnover": annualized_turnover(weights),
        "AvgGrossExposure": float(weights.sum(axis=1).mean()),
        "AvgHoldings": float((weights > 0).sum(axis=1).mean()),
        "UniverseSize": int(close.shape[1]),
        "StaticUniverseBiasFlag": int(universe["StartDate"].isna().all()),
        "UniverseBiasNote": "STATIC_CURRENT_SP100_MEMBERSHIP" if universe["StartDate"].isna().all() else "WIKIPEDIA_REVISION_POINT_IN_TIME_APPROX",
        "FirstDate": str(nav.index[0].date()),
        "LastDate": str(nav.index[-1].date()),
    }
    signal = compute_signal(close)
    latest = weights.index[-1]
    current_rows = []
    held = weights.loc[latest]
    held = held[held > 0].sort_values(ascending=False)
    for rank, (symbol, weight) in enumerate(held.items(), start=1):
        sector = membership_sector(symbol, latest, membership_lookup) or ""
        current_rows.append(
            {
                "AsOfDate": latest.strftime("%Y-%m-%d"),
                "Symbol": symbol,
                "Sector": sector,
                "TargetWeight": float(weight),
                "CurrentPrice": float(close.loc[latest, symbol]),
                "Momentum12_1": float(signal.loc[latest, symbol]),
                "SignalRank": rank,
            }
        )
    portfolio = pd.DataFrame(current_rows)
    nav_df = pd.DataFrame({"date": nav.index, "gross_return": gross.values, "net_return": net.values, "turnover": turnover.values, "nav": nav.values})
    return {
        "summary": summary,
        "nav": nav_df,
        "portfolio": portfolio,
        "weights": weights,
        "prices": close,
        "traded_value": traded_value,
    }


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
                "Symbol": r["Symbol"],
                "Sector": r["Sector"],
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
                "AsOfDate": str(portfolio["AsOfDate"].iloc[0]) if not portfolio.empty else "",
                "PlannedCapitalUSD": capital,
                "PlannedInvestedUSD": float(order_df["OrderNotionalUSD"].sum()) if not order_df.empty else 0.0,
                "ResidualCashUSD": float(capital - order_df["OrderNotionalUSD"].sum()) if not order_df.empty else capital,
                "HoldingsCount": int((order_df["OrderShares"] > 0).sum()) if not order_df.empty else 0,
            }
        ]
    )
    return order_df, summary


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="US stock 12-1 momentum MVP on S&P 100-like universe.")
    p.add_argument("--price-base", type=str, default="data/prices_us_stock_sp100")
    p.add_argument("--report-path", type=str, default="backtests/us_stock_sp100_universe.csv")
    p.add_argument("--membership-path", type=str, default="")
    p.add_argument("--output-dir", type=str, default="backtests/us_stock_mom12_1_20260328")
    p.add_argument("--top-n", type=int, default=20)
    p.add_argument("--max-per-sector", type=int, default=3)
    p.add_argument("--min-median-value", type=float, default=100_000_000.0)
    p.add_argument("--min-price", type=float, default=10.0)
    p.add_argument("--rebalance", type=str, default="ME")
    p.add_argument("--one-way-cost-bps", type=float, default=7.0)
    p.add_argument("--order-capital-usd", type=float, default=5000.0)
    p.add_argument("--trade-date", type=str, default="2026-03-30")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = run_backtest(
        price_base=Path(args.price_base),
        report_path=Path(args.report_path),
        membership_path=Path(args.membership_path) if args.membership_path else None,
        top_n=args.top_n,
        max_per_sector=args.max_per_sector,
        min_median_value=args.min_median_value,
        min_price=args.min_price,
        rebalance=args.rebalance,
        one_way_cost_bps=args.one_way_cost_bps,
    )
    summary_df = pd.DataFrame([result["summary"]])
    order_df, order_summary_df = build_order_sheet(result["portfolio"], args.order_capital_usd, args.trade_date)
    summary_df.to_csv(out_dir / "us_stock_mom12_1_summary.csv", index=False)
    result["nav"].to_csv(out_dir / "us_stock_mom12_1_nav.csv", index=False)
    result["portfolio"].to_csv(out_dir / "us_stock_mom12_1_portfolio.csv", index=False)
    order_df.to_csv(out_dir / f"us_stock_mom12_1_order_sheet_{int(args.order_capital_usd)}usd.csv", index=False)
    order_summary_df.to_csv(out_dir / f"us_stock_mom12_1_order_sheet_{int(args.order_capital_usd)}usd_summary.csv", index=False)
    print(summary_df.to_string(index=False))
    print()
    print(result["portfolio"].head(30).to_string(index=False))


if __name__ == "__main__":
    main()
