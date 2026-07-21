import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from typing import Iterable

import pandas as pd
import yfinance as yf


CORE_US_ETFS = [
    ("SPY", "SPDR S&P 500 ETF Trust"),
    ("QQQ", "Invesco QQQ Trust"),
    ("IWM", "iShares Russell 2000 ETF"),
    ("DIA", "SPDR Dow Jones Industrial Average ETF Trust"),
    ("TLT", "iShares 20+ Year Treasury Bond ETF"),
    ("IEF", "iShares 7-10 Year Treasury Bond ETF"),
    ("SHY", "iShares 1-3 Year Treasury Bond ETF"),
    ("GLD", "SPDR Gold Shares"),
    ("VNQ", "Vanguard Real Estate ETF"),
    ("HYG", "iShares iBoxx $ High Yield Corporate Bond ETF"),
    ("LQD", "iShares iBoxx $ Investment Grade Corporate Bond ETF"),
    ("XLK", "Technology Select Sector SPDR Fund"),
    ("XLF", "Financial Select Sector SPDR Fund"),
    ("XLE", "Energy Select Sector SPDR Fund"),
    ("XLV", "Health Care Select Sector SPDR Fund"),
    ("XLI", "Industrial Select Sector SPDR Fund"),
    ("XLP", "Consumer Staples Select Sector SPDR Fund"),
    ("XLY", "Consumer Discretionary Select Sector SPDR Fund"),
]


def normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "close", "volume"])
    out = df.reset_index().rename(columns={"Date": "date", "index": "date", "Close": "close", "Volume": "volume"})
    cols = {c.lower(): c for c in out.columns}
    if "date" not in out.columns and "date" in cols:
        out = out.rename(columns={cols["date"]: "date"})
    if "close" not in out.columns and "close" in cols:
        out = out.rename(columns={cols["close"]: "close"})
    if "volume" not in out.columns and "volume" in cols:
        out = out.rename(columns={cols["volume"]: "volume"})
    out = out[["date", "close", "volume"]].copy()
    out["date"] = pd.to_datetime(out["date"])
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out["volume"] = pd.to_numeric(out["volume"], errors="coerce").fillna(0.0)
    out = out.dropna(subset=["date", "close"])
    out = out[out["close"] > 0].sort_values("date").drop_duplicates(subset=["date"]).reset_index(drop=True)
    return out


def batch_download(tickers: list[str], start: str, end: str) -> dict[str, pd.DataFrame]:
    raw = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False, group_by="ticker", threads=True)
    out: dict[str, pd.DataFrame] = {}
    if raw.empty:
        return out
    if isinstance(raw.columns, pd.MultiIndex):
        for ticker in tickers:
            if ticker in raw.columns.get_level_values(0):
                out[ticker] = normalize_frame(raw[ticker])
    else:
        if len(tickers) == 1:
            out[tickers[0]] = normalize_frame(raw)
    return out


def write_price_file(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, compression="gzip", encoding="utf-8-sig")


def write_universe_report(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def backfill(out_base: Path, start: str, end: str, tickers: Iterable[tuple[str, str]]) -> pd.DataFrame:
    (out_base / "stock").mkdir(parents=True, exist_ok=True)
    (out_base / "etf").mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    downloaded = batch_download([code for code, _ in tickers], start, end)
    for code, name in tickers:
        df = downloaded.get(code, pd.DataFrame())
        if df.empty:
            rows.append({"Ticker": code, "Name": name, "Status": "EMPTY", "Bars": 0, "FirstDate": "", "LastDate": ""})
            continue
        write_price_file(out_base / "etf" / f"{code}.csv.gz", df)
        rows.append(
            {
                "Ticker": code,
                "Name": name,
                "Status": "OK",
                "Bars": int(len(df)),
                "FirstDate": str(df["date"].iloc[0].date()),
                "LastDate": str(df["date"].iloc[-1].date()),
                "PriceBasis": "adjusted_close",
            }
        )
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Backfill a core US ETF research universe into KIS-compatible csv.gz files.")
    p.add_argument("--out-base", type=str, default="data/prices_us_etf_core")
    p.add_argument("--report-path", type=str, default="backtests/us_etf_core_universe.csv")
    p.add_argument("--start", type=str, default="2015-01-01")
    p.add_argument("--end", type=str, default="")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    end = args.end or pd.Timestamp.today().strftime("%Y-%m-%d")
    out_base = Path(args.out_base)
    report_path = Path(args.report_path)
    report = backfill(out_base, args.start, end, CORE_US_ETFS)
    write_universe_report(report_path, report.to_dict(orient="records"))
    print(f"saved {report_path}")
    print(f"synced {out_base}")
    print(report.to_string(index=False))


if __name__ == "__main__":
    main()
