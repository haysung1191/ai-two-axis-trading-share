import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import pandas as pd
import yfinance as yf


CANONICAL_UNIVERSE = [
    ("SPY", "SPDR S&P 500 ETF Trust", "risk"),
    ("QQQ", "Invesco QQQ Trust", "risk"),
    ("IWM", "iShares Russell 2000 ETF", "risk"),
    ("EFA", "iShares MSCI EAFE ETF", "risk"),
    ("EEM", "iShares MSCI Emerging Markets ETF", "risk"),
    ("VNQ", "Vanguard Real Estate ETF", "risk"),
    ("GLD", "SPDR Gold Shares", "risk"),
    ("PDBC", "Invesco Optimum Yield Diversified Commodity Strategy No K-1 ETF", "risk"),
    ("HYG", "iShares iBoxx $ High Yield Corporate Bond ETF", "risk"),
    ("IEF", "iShares 7-10 Year Treasury Bond ETF", "defensive"),
    ("TLT", "iShares 20+ Year Treasury Bond ETF", "defensive"),
    ("BIL", "SPDR Bloomberg 1-3 Month T-Bill ETF", "defensive"),
]

RISK_TICKERS = [ticker for ticker, _, sleeve in CANONICAL_UNIVERSE if sleeve == "risk"]
ALL_TICKERS = [ticker for ticker, _, _ in CANONICAL_UNIVERSE]
REQUIRED_RETURN_WINDOWS = {"R1M": 1, "R3M": 3, "R6M": 6, "R12M": 12}


def normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "close", "volume"])
    out = df.copy()
    if "date" not in out.columns:
        out = out.reset_index()
    out = out.rename(
        columns={
            "Date": "date",
            "index": "date",
            "Close": "close",
            "Volume": "volume",
        }
    )
    cols = {c.lower(): c for c in out.columns}
    if "date" not in out.columns and "date" in cols:
        out = out.rename(columns={cols["date"]: "date"})
    if "close" not in out.columns and "close" in cols:
        out = out.rename(columns={cols["close"]: "close"})
    if "volume" not in out.columns and "volume" in cols:
        out = out.rename(columns={cols["volume"]: "volume"})
    out = out.loc[:, ~out.columns.duplicated()].copy()
    out = out[["date", "close", "volume"]].copy()
    out["date"] = pd.to_datetime(out["date"])
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out["volume"] = pd.to_numeric(out["volume"], errors="coerce").fillna(0.0)
    out = out.dropna(subset=["date", "close"])
    out = out[out["close"] > 0].sort_values("date").drop_duplicates(subset=["date"]).reset_index(drop=True)
    return out


def batch_download(tickers: list[str], start: str, end: str) -> dict[str, pd.DataFrame]:
    raw = yf.download(
        tickers,
        start=start,
        end=end,
        auto_adjust=True,
        progress=False,
        group_by="ticker",
        threads=True,
    )
    out: dict[str, pd.DataFrame] = {}
    if raw.empty:
        return out
    if isinstance(raw.columns, pd.MultiIndex):
        for ticker in tickers:
            if ticker in raw.columns.get_level_values(0):
                out[ticker] = normalize_frame(raw[ticker])
    elif len(tickers) == 1:
        out[tickers[0]] = normalize_frame(raw)
    return out


def sync_prices(price_base: Path, start: str, end: str) -> None:
    (price_base / "etf").mkdir(parents=True, exist_ok=True)
    downloaded = batch_download(ALL_TICKERS, start, end)
    for ticker in ALL_TICKERS:
        df = downloaded.get(ticker, pd.DataFrame(columns=["date", "close", "volume"]))
        if df.empty:
            continue
        df.to_csv(price_base / "etf" / f"{ticker}.csv.gz", index=False, compression="gzip", encoding="utf-8-sig")


def load_prices(price_base: Path) -> tuple[pd.DataFrame, list[dict], list[str]]:
    series = []
    snapshot_rows = []
    issues: list[str] = []
    for ticker, name, sleeve in CANONICAL_UNIVERSE:
        path = price_base / "etf" / f"{ticker}.csv.gz"
        if not path.exists():
            snapshot_rows.append(
                {
                    "Ticker": ticker,
                    "Name": name,
                    "Sleeve": sleeve,
                    "Status": "MISSING_FILE",
                    "Bars": 0,
                    "FirstDate": "",
                    "LastDate": "",
                }
            )
            issues.append(f"missing price file: {ticker}")
            continue
        df = pd.read_csv(path, compression="gzip", parse_dates=["date"])
        df = normalize_frame(df)
        if df.empty:
            snapshot_rows.append(
                {
                    "Ticker": ticker,
                    "Name": name,
                    "Sleeve": sleeve,
                    "Status": "EMPTY_FILE",
                    "Bars": 0,
                    "FirstDate": "",
                    "LastDate": "",
                }
            )
            issues.append(f"empty price file: {ticker}")
            continue
        if df["date"].duplicated().any():
            issues.append(f"duplicate dates: {ticker}")
        snapshot_rows.append(
            {
                "Ticker": ticker,
                "Name": name,
                "Sleeve": sleeve,
                "Status": "OK",
                "Bars": int(len(df)),
                "FirstDate": str(df["date"].iloc[0].date()),
                "LastDate": str(df["date"].iloc[-1].date()),
            }
        )
        series.append(pd.Series(df["close"].values, index=pd.to_datetime(df["date"]), name=ticker))
    close = pd.concat(series, axis=1).sort_index() if series else pd.DataFrame()
    return close, snapshot_rows, issues


def compute_month_end_series(close: pd.DataFrame) -> tuple[pd.DataFrame, pd.Timestamp | None, list[str]]:
    issues: list[str] = []
    if close.empty:
        return pd.DataFrame(), None, ["no price matrix"]
    missing_tickers = [ticker for ticker in ALL_TICKERS if ticker not in close.columns]
    for ticker in missing_tickers:
        issues.append(f"ticker missing from matrix: {ticker}")
    common = close[ALL_TICKERS].dropna(how="any") if all(ticker in close.columns for ticker in ALL_TICKERS) else pd.DataFrame()
    if common.empty:
        return pd.DataFrame(), None, issues + ["no common fully populated dates"]
    month_end = common.groupby(common.index.to_period("M")).tail(1).copy()
    if month_end.empty:
        return month_end, None, issues + ["no month-end rows"]
    latest_common = pd.Timestamp(common.index.max())
    latest_common_period = latest_common.to_period("M")
    calendar_month_end = pd.Timestamp(latest_common.to_period("M").end_time.normalize())
    if latest_common.normalize() < calendar_month_end.normalize():
        month_end = month_end[month_end.index.to_period("M") < latest_common_period].copy()
    if month_end.empty:
        return month_end, None, issues + ["no completed month-end rows"]
    latest_month_end = pd.Timestamp(month_end.index.max())
    # Explicitly verify that the selected signal date is the last common trading day of its month.
    month_mask = common.index.to_period("M") == latest_month_end.to_period("M")
    expected = pd.Timestamp(common.index[month_mask].max())
    if latest_month_end != expected:
        issues.append("latest month-end not detected correctly")
    return month_end, latest_month_end, issues


def compute_signal_tables(month_end: pd.DataFrame, signal_date: pd.Timestamp) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    issues: list[str] = []
    score_rows = []
    eligibility_rows = []
    if signal_date not in month_end.index:
        return pd.DataFrame(), pd.DataFrame(), ["signal date missing from month-end table"]
    pos = month_end.index.get_loc(signal_date)
    bil_r12 = None
    if pos >= 12:
        bil_r12 = float(month_end["BIL"].iloc[pos] / month_end["BIL"].iloc[pos - 12] - 1.0)
    else:
        issues.append("insufficient BIL history for 12M return")
    for ticker in RISK_TICKERS:
        row = {
            "SignalDate": signal_date.strftime("%Y-%m-%d"),
            "Ticker": ticker,
            "R1M": pd.NA,
            "R3M": pd.NA,
            "R6M": pd.NA,
            "R12M": pd.NA,
            "CompositeScore": pd.NA,
            "Status": "OK",
        }
        enough = True
        returns: dict[str, float] = {}
        for label, months in REQUIRED_RETURN_WINDOWS.items():
            if pos < months:
                enough = False
                row["Status"] = "INSUFFICIENT_HISTORY"
                continue
            value = float(month_end[ticker].iloc[pos] / month_end[ticker].iloc[pos - months] - 1.0)
            row[label] = value
            returns[label] = value
        if enough:
            row["CompositeScore"] = (
                0.10 * returns["R1M"]
                + 0.25 * returns["R3M"]
                + 0.30 * returns["R6M"]
                + 0.35 * returns["R12M"]
            )
        score_rows.append(row)
        eligible = False
        eligibility_status = "OK"
        if bil_r12 is None or pd.isna(row["R12M"]):
            eligibility_status = "STOP"
            issues.append(f"insufficient 12M history for eligibility: {ticker}")
        else:
            eligible = float(row["R12M"]) > float(bil_r12)
        eligibility_rows.append(
            {
                "SignalDate": signal_date.strftime("%Y-%m-%d"),
                "Ticker": ticker,
                "AssetR12M": row["R12M"],
                "BILR12M": bil_r12,
                "Eligible": int(eligible) if eligibility_status == "OK" else pd.NA,
                "Status": eligibility_status,
            }
        )
    return pd.DataFrame(score_rows), pd.DataFrame(eligibility_rows), issues


def finalize_status(
    snapshot_rows: list[dict],
    signal_date: pd.Timestamp | None,
    month_end: pd.DataFrame,
    issues: list[str],
) -> tuple[str, str]:
    if issues:
        return "STOP", "; ".join(sorted(set(issues)))
    if signal_date is None or month_end.empty:
        return "STOP", "no valid month-end signal date"
    return "GO", ""


def write_outputs(
    output_dir: Path,
    snapshot_rows: list[dict],
    signal_date: pd.Timestamp | None,
    batch_status: str,
    stop_reason: str,
    score_df: pd.DataFrame,
    eligibility_df: pd.DataFrame,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_df = pd.DataFrame(snapshot_rows)
    snapshot_df["LatestMonthEnd"] = signal_date.strftime("%Y-%m-%d") if signal_date is not None else ""
    snapshot_df["BatchStatus"] = batch_status
    snapshot_df["StopReason"] = stop_reason
    snapshot_df.to_csv(output_dir / "universe_snapshot.csv", index=False, encoding="utf-8-sig")
    score_df.to_csv(output_dir / "momentum_score_table.csv", index=False, encoding="utf-8-sig")
    eligibility_df.to_csv(output_dir / "eligibility_table.csv", index=False, encoding="utf-8-sig")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Batch 1 builder for US ETF cross-asset dual momentum MVP v1.")
    p.add_argument("--price-base", type=str, default="data/prices_us_etf_dm_v1")
    p.add_argument("--output-dir", type=str, default="backtests/us_etf_dual_momentum_mvp_v1_batch1")
    p.add_argument("--start", type=str, default="2015-01-01")
    p.add_argument("--end", type=str, default="")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    end = args.end or pd.Timestamp.today().strftime("%Y-%m-%d")
    price_base = Path(args.price_base)
    output_dir = Path(args.output_dir)

    sync_prices(price_base, args.start, end)
    close, snapshot_rows, issues = load_prices(price_base)
    month_end, signal_date, month_end_issues = compute_month_end_series(close)
    issues.extend(month_end_issues)

    if signal_date is None:
        score_df = pd.DataFrame(columns=["SignalDate", "Ticker", "R1M", "R3M", "R6M", "R12M", "CompositeScore", "Status"])
        eligibility_df = pd.DataFrame(columns=["SignalDate", "Ticker", "AssetR12M", "BILR12M", "Eligible", "Status"])
    else:
        score_df, eligibility_df, signal_issues = compute_signal_tables(month_end, signal_date)
        issues.extend(signal_issues)

    batch_status, stop_reason = finalize_status(snapshot_rows, signal_date, month_end, issues)
    write_outputs(output_dir, snapshot_rows, signal_date, batch_status, stop_reason, score_df, eligibility_df)

    print(f"batch_status={batch_status}")
    if signal_date is not None:
        print(f"latest_month_end={signal_date.strftime('%Y-%m-%d')}")
    if stop_reason:
        print(f"stop_reason={stop_reason}")
    print(f"saved {output_dir}")


if __name__ == "__main__":
    main()
