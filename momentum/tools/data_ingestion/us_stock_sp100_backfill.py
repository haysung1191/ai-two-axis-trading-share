import argparse
from io import StringIO
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import pandas as pd
import requests
import yfinance as yf


WIKI_URL = "https://en.wikipedia.org/wiki/S%26P_100"


def fetch_sp100_universe() -> pd.DataFrame:
    html = requests.get(WIKI_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30).text
    tables = pd.read_html(StringIO(html))
    table = next(t for t in tables if {"Symbol", "Name", "Sector"}.issubset(set(map(str, t.columns))))
    out = table[["Symbol", "Name", "Sector"]].copy()
    out["YahooTicker"] = out["Symbol"].astype(str).str.replace(".", "-", regex=False)
    out["UniverseType"] = "STATIC_CURRENT_MEMBERSHIP"
    return out.sort_values("Symbol").reset_index(drop=True)


def load_membership_universe(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    cols = ["Symbol", "YahooTicker", "Name", "Sector", "UniverseType"]
    df = df[cols].copy()
    df["NameMissing"] = df["Name"].isna().astype(int)
    df["SectorMissing"] = df["Sector"].isna().astype(int)
    out = (
        df.sort_values(["Symbol", "NameMissing", "SectorMissing", "Name", "Sector"])
        .groupby(["Symbol", "YahooTicker"], as_index=False)
        .first()
        .drop(columns=["NameMissing", "SectorMissing"])
        .sort_values("Symbol")
        .reset_index(drop=True)
    )
    return out


def normalize_download(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "close", "volume"])
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]
    out = df.reset_index().rename(columns={"Date": "date", "Close": "close", "Volume": "volume"})
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
                out[ticker] = normalize_download(raw[ticker], ticker)
    else:
        if len(tickers) == 1:
            out[tickers[0]] = normalize_download(raw, tickers[0])
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Backfill S&P 100 stock prices for US momentum research.")
    p.add_argument("--out-base", type=str, default="data/prices_us_stock_sp100")
    p.add_argument("--report-path", type=str, default="backtests/us_stock_sp100_universe.csv")
    p.add_argument("--membership-path", type=str, default="")
    p.add_argument("--start", type=str, default="2015-01-01")
    p.add_argument("--end", type=str, default="2026-03-28")
    p.add_argument("--batch-size", type=int, default=25)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    out_base = Path(args.out_base)
    (out_base / "stock").mkdir(parents=True, exist_ok=True)

    universe = load_membership_universe(args.membership_path) if args.membership_path else fetch_sp100_universe()
    rows: list[dict] = []
    for i in range(0, len(universe), args.batch_size):
        batch = universe.iloc[i:i + args.batch_size].copy()
        data = batch_download(batch["YahooTicker"].tolist(), args.start, args.end)
        for _, r in batch.iterrows():
            ticker = str(r["YahooTicker"])
            symbol = str(r["Symbol"])
            df = data.get(ticker, pd.DataFrame())
            status = "OK" if not df.empty else "EMPTY"
            if not df.empty:
                df.to_csv(out_base / "stock" / f"{symbol}.csv.gz", index=False, compression="gzip", encoding="utf-8-sig")
            rows.append(
                {
                    "Symbol": symbol,
                    "YahooTicker": ticker,
                    "Name": r["Name"],
                    "Sector": r["Sector"],
                    "UniverseType": r["UniverseType"],
                    "Status": status,
                    "Bars": int(len(df)),
                    "FirstDate": str(df["date"].iloc[0].date()) if not df.empty else "",
                    "LastDate": str(df["date"].iloc[-1].date()) if not df.empty else "",
                }
            )

    report = pd.DataFrame(rows).sort_values(["Status", "Symbol"], ascending=[True, True]).reset_index(drop=True)
    Path(args.report_path).parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(args.report_path, index=False, encoding="utf-8-sig")
    safe = report.copy()
    for col in safe.columns:
        safe[col] = safe[col].astype(str).str.encode("cp949", errors="ignore").str.decode("cp949", errors="ignore")
    print(safe.to_string(index=False))


if __name__ == "__main__":
    main()
