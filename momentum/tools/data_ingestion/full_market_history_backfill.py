from __future__ import annotations

import argparse
import csv
import io
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys
from typing import Iterable

import pandas as pd
import requests


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
NASDAQ_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt"
OTHER_LISTED_URL = "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt"


def normalize_price_frame(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["date", "close", "volume"])
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = [str(c[0]) for c in df.columns]
    out = df.reset_index().rename(columns={"Date": "date", "Close": "close", "Adj Close": "close", "Volume": "volume"})
    out = out.loc[:, ~out.columns.duplicated()]
    lower = {str(c).lower(): c for c in out.columns}
    if "date" not in out.columns and "date" in lower:
        out = out.rename(columns={lower["date"]: "date"})
    if "date" not in out.columns and "날짜" in out.columns:
        out = out.rename(columns={"날짜": "date"})
    if "close" not in out.columns and "close" in lower:
        out = out.rename(columns={lower["close"]: "close"})
    if "volume" not in out.columns and "volume" in lower:
        out = out.rename(columns={lower["volume"]: "volume"})
    if not {"date", "close"}.issubset(out.columns):
        return pd.DataFrame(columns=["date", "close", "volume"])
    if "volume" not in out.columns:
        out["volume"] = 0.0
    out = out[["date", "close", "volume"]].copy()
    if isinstance(out["date"], pd.DataFrame):
        out["date"] = out["date"].iloc[:, 0]
    if isinstance(out["close"], pd.DataFrame):
        out["close"] = out["close"].iloc[:, 0]
    if isinstance(out["volume"], pd.DataFrame):
        out["volume"] = out["volume"].iloc[:, 0]
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out["volume"] = pd.to_numeric(out["volume"], errors="coerce").fillna(0.0)
    out = out.dropna(subset=["date", "close"])
    out = out[out["close"] > 0].sort_values("date").drop_duplicates(subset=["date"]).reset_index(drop=True)
    return out


def is_supported_us_symbol(symbol: str) -> bool:
    text = str(symbol).strip().upper()
    if not text:
        return False
    # Nasdaq/CTA feeds include preferred shares, warrants, rights, and units.
    # Their Yahoo mappings are inconsistent and should not kill the broad backfill.
    if any(ch in text for ch in ["$", "^", "/", " "]):
        return False
    return bool(re_fullmatch_us_symbol(text))


def is_supported_us_security(row: pd.Series) -> bool:
    if not is_supported_us_symbol(str(row.get("symbol", ""))):
        return False
    if str(row.get("asset_type", "")) == "etf":
        return True
    name = str(row.get("name", "")).lower()
    excluded_terms = [
        "warrant",
        "right",
        "unit",
        "preferred",
        "preference",
        "depositary share",
        "note due",
        "notes due",
        "debenture",
        "acquisition corp. ii",
        "acquisition corp iii",
        "acquisition corp.",
    ]
    if any(term in name for term in excluded_terms):
        return False
    common_terms = ["common stock", "ordinary share", "ordinary shares", "adr", "american depositary"]
    return any(term in name for term in common_terms)


def re_fullmatch_us_symbol(text: str) -> bool:
    import re

    return re.fullmatch(r"[A-Z0-9.\-]+", text) is not None


def _parse_pipe_table(text: str) -> list[dict[str, str]]:
    lines = [line for line in text.splitlines() if "|" in line and not line.startswith("File Creation Time")]
    reader = csv.DictReader(io.StringIO("\n".join(lines)), delimiter="|")
    return [dict(row) for row in reader if row]


def fetch_us_listed_universe(timeout: int = 30) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    nasdaq_text = requests.get(NASDAQ_LISTED_URL, timeout=timeout).text
    for row in _parse_pipe_table(nasdaq_text):
        symbol = str(row.get("Symbol", "")).strip()
        if not symbol or symbol == "Symbol" or row.get("Test Issue", "N") == "Y":
            continue
        rows.append(
            {
                "symbol": symbol,
                "yahoo_ticker": symbol.replace(".", "-"),
                "name": str(row.get("Security Name", "")).strip(),
                "asset_type": "etf" if row.get("ETF", "N") == "Y" else "stock",
                "source": "nasdaqlisted",
            }
        )
    other_text = requests.get(OTHER_LISTED_URL, timeout=timeout).text
    for row in _parse_pipe_table(other_text):
        symbol = str(row.get("ACT Symbol", "")).strip()
        if not symbol or symbol == "ACT Symbol" or row.get("Test Issue", "N") == "Y":
            continue
        rows.append(
            {
                "symbol": symbol,
                "yahoo_ticker": symbol.replace(".", "-"),
                "name": str(row.get("Security Name", "")).strip(),
                "asset_type": "etf" if row.get("ETF", "N") == "Y" else "stock",
                "source": "otherlisted",
            }
        )
    df = pd.DataFrame(rows).drop_duplicates(subset=["symbol"]).sort_values("symbol").reset_index(drop=True)
    return df


def fetch_kr_universe(asset_type: str) -> pd.DataFrame:
    if asset_type == "stock":
        rows = []
        try:
            import FinanceDataReader as fdr

            listing = fdr.StockListing("KRX")
            for _, row in listing.iterrows():
                code = str(row.get("Code", "")).strip()
                name = str(row.get("Name", "")).strip()
                market = str(row.get("Market", "")).upper()
                if len(code) == 6 and code.isdigit() and name and market in {"KOSPI", "KOSDAQ", "KONEX"}:
                    rows.append((code, name))
        except Exception:
            rows = []
        if not rows:
            from live_core.kis_screener_universe import get_current_stock_universe
            import config

            rows = get_current_stock_universe(config_module=config, repo_root=REPO_ROOT, print_fn=lambda _: None)
    elif asset_type == "etf":
        from live_core.kis_screener_universe import get_etf_tickers

        rows = get_etf_tickers(print_fn=lambda _: None)
    else:
        raise ValueError("asset_type must be stock or etf")
    return pd.DataFrame(
        [{"symbol": str(code).zfill(6), "name": name, "asset_type": asset_type, "source": "krx"} for code, name in rows]
    ).drop_duplicates(subset=["symbol"]).sort_values("symbol").reset_index(drop=True)


def download_us_batch(tickers: list[str], start: str, end: str, source: str = "yahoo-chart") -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for ticker in tickers:
        if source == "fdr":
            out[ticker] = download_us_one(ticker, start, end)
        else:
            out[ticker] = download_us_one_yahoo_chart(ticker, start, end)
    return out


def download_us_one_yahoo_chart(ticker: str, start: str, end: str) -> pd.DataFrame:
    start_ts = int(pd.Timestamp(start, tz="UTC").timestamp())
    end_ts = int((pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1)).timestamp())
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {
        "period1": start_ts,
        "period2": end_ts,
        "interval": "1d",
        "events": "history",
        "includeAdjustedClose": "true",
    }
    try:
        response = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=5)
        if response.status_code != 200:
            return pd.DataFrame(columns=["date", "close", "volume"])
        payload = response.json()
        result = ((payload.get("chart") or {}).get("result") or [None])[0]
        if not result:
            return pd.DataFrame(columns=["date", "close", "volume"])
        timestamps = result.get("timestamp") or []
        quote = (((result.get("indicators") or {}).get("quote") or [{}])[0]) or {}
        adj = (((result.get("indicators") or {}).get("adjclose") or [{}])[0]).get("adjclose")
        close = adj or quote.get("close") or []
        volume = quote.get("volume") or [0] * len(timestamps)
        rows = []
        for idx, ts in enumerate(timestamps):
            c = close[idx] if idx < len(close) else None
            if c is None:
                continue
            rows.append(
                {
                    "date": pd.to_datetime(int(ts), unit="s", utc=True).tz_convert(None).normalize(),
                    "close": c,
                    "volume": volume[idx] if idx < len(volume) and volume[idx] is not None else 0,
                }
            )
        return normalize_price_frame(pd.DataFrame(rows))
    except Exception:
        return pd.DataFrame(columns=["date", "close", "volume"])


def download_us_one(ticker: str, start: str, end: str) -> pd.DataFrame:
    try:
        import FinanceDataReader as fdr

        df = fdr.DataReader(ticker, start, end)
        out = normalize_price_frame(df)
        if not out.empty:
            return out
    except Exception:
        pass
    return download_us_one_yahoo_chart(ticker, start, end)


def download_kr_one(symbol: str, start: str, end: str) -> pd.DataFrame:
    code = str(symbol).zfill(6)
    try:
        from pykrx import stock as pykrx_stock

        raw = pykrx_stock.get_market_ohlcv_by_date(
            start.replace("-", ""),
            end.replace("-", ""),
            code,
            adjusted=True,
        )
        if raw is not None and not raw.empty:
            rename = {}
            for col in raw.columns:
                text = str(col)
                if text in {"종가", "close", "Close"}:
                    rename[col] = "close"
                elif text in {"거래량", "volume", "Volume"}:
                    rename[col] = "volume"
            normalized = raw.rename(columns=rename)
            return normalize_price_frame(normalized)
    except Exception:
        pass

    import FinanceDataReader as fdr

    return normalize_price_frame(fdr.DataReader(code, start, end))


def write_price(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, compression="gzip", encoding="utf-8-sig")


def existing_bar_count(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return int(len(pd.read_csv(path, compression="gzip", usecols=["date"])))
    except Exception:
        return 0


def select_rows(df: pd.DataFrame, asset_types: set[str], max_items: int) -> pd.DataFrame:
    out = df[df["asset_type"].isin(asset_types)].copy()
    return out.reset_index(drop=True)


def apply_window(df: pd.DataFrame, offset: int, max_items: int) -> pd.DataFrame:
    out = df.copy().reset_index(drop=True)
    if offset > 0:
        out = out.iloc[offset:].copy()
    if max_items > 0:
        out = out.head(max_items)
    return out.reset_index(drop=True)


def filter_symbols(df: pd.DataFrame, symbols: str) -> pd.DataFrame:
    wanted = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not wanted:
        return df
    normalized = df["symbol"].astype(str).str.upper()
    out = df[normalized.isin(wanted)].copy()
    order = {symbol: i for i, symbol in enumerate(wanted)}
    out["_order"] = out["symbol"].astype(str).str.upper().map(order)
    return out.sort_values("_order").drop(columns=["_order"]).reset_index(drop=True)


def explicit_symbol_rows(symbols: str, asset_type: str, source: str) -> pd.DataFrame:
    wanted = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    return pd.DataFrame(
        [{"symbol": symbol, "name": "", "asset_type": asset_type, "source": source} for symbol in wanted]
    )


def backfill_us(args: argparse.Namespace, asset_types: set[str]) -> pd.DataFrame:
    source_universe = pd.read_csv(args.universe_path) if args.universe_path else fetch_us_listed_universe()
    universe = apply_window(select_rows(source_universe, asset_types, 0), args.offset, args.max_items)
    universe = filter_symbols(universe, args.symbols)
    rows: list[dict] = []
    if args.universe_only:
        return universe
    supported_mask = universe.apply(is_supported_us_security, axis=1)
    unsupported = universe[~supported_mask].copy()
    universe = universe[supported_mask].copy().reset_index(drop=True)
    for _, row in unsupported.iterrows():
        rows.append({**row.to_dict(), "status": "SKIPPED_UNSUPPORTED_SYMBOL", "bars": 0})
    out_base = Path(args.out_base_us)
    if args.skip_existing_min_bars > 0:
        keep_indexes = []
        for idx, row in universe.iterrows():
            path = out_base / row["asset_type"] / f"{row['symbol']}.csv.gz"
            bars = existing_bar_count(path)
            if bars >= args.skip_existing_min_bars:
                rows.append({**row.to_dict(), "status": "SKIPPED_EXISTING", "bars": bars})
            else:
                keep_indexes.append(idx)
        universe = universe.loc[keep_indexes].reset_index(drop=True)
    for i in range(0, len(universe), args.batch_size):
        batch = universe.iloc[i : i + args.batch_size]
        print(f"progress batch_start={i + 1} batch_end={i + len(batch)} remaining={len(universe) - i}", flush=True)
        data = download_us_batch(batch["yahoo_ticker"].tolist(), args.start, args.end, source=args.us_source)
        for _, row in batch.iterrows():
            df = data.get(row["yahoo_ticker"], pd.DataFrame())
            status = "OK" if not df.empty else "EMPTY"
            if not df.empty:
                write_price(out_base / row["asset_type"] / f"{row['symbol']}.csv.gz", df)
            rows.append({**row.to_dict(), "status": status, "bars": int(len(df))})
        time.sleep(args.sleep_sec)
    return pd.DataFrame(rows)


def backfill_kr(args: argparse.Namespace, asset_types: set[str]) -> pd.DataFrame:
    universe = (
        pd.read_csv(args.universe_path, dtype={"symbol": str})
        if args.universe_path
        else pd.concat([fetch_kr_universe(t) for t in sorted(asset_types)], ignore_index=True)
    )
    universe = apply_window(select_rows(universe, asset_types, 0), args.offset, args.max_items)
    universe = filter_symbols(universe, args.symbols)
    if universe.empty and args.symbols and len(asset_types) == 1:
        universe = explicit_symbol_rows(args.symbols, next(iter(asset_types)), "explicit_symbols")
    rows: list[dict] = []
    if args.universe_only:
        return universe
    out_base = Path(args.out_base_kr)
    if args.skip_existing_min_bars > 0:
        keep_indexes = []
        for idx, row in universe.iterrows():
            path = out_base / row["asset_type"] / f"{str(row['symbol']).zfill(6)}.csv.gz"
            bars = existing_bar_count(path)
            if bars >= args.skip_existing_min_bars:
                row_dict = row.to_dict()
                row_dict["symbol"] = str(row_dict["symbol"]).zfill(6)
                rows.append({**row_dict, "status": "SKIPPED_EXISTING", "bars": bars})
            else:
                keep_indexes.append(idx)
        universe = universe.loc[keep_indexes].reset_index(drop=True)
    for _, row in universe.iterrows():
        print(f"progress symbol={row['symbol']} asset_type={row['asset_type']}", flush=True)
        try:
            df = download_kr_one(row["symbol"], args.start, args.end)
            status = "OK" if not df.empty else "EMPTY"
            if not df.empty:
                write_price(out_base / row["asset_type"] / f"{str(row['symbol']).zfill(6)}.csv.gz", df)
            row_dict = row.to_dict()
            row_dict["symbol"] = str(row_dict["symbol"]).zfill(6)
            rows.append({**row_dict, "status": status, "bars": int(len(df))})
        except Exception as exc:
            row_dict = row.to_dict()
            row_dict["symbol"] = str(row_dict["symbol"]).zfill(6)
            rows.append({**row_dict, "status": "ERROR", "bars": 0, "error": str(exc)[:240]})
        time.sleep(args.sleep_sec)
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Backfill broad US/KR stock and ETF daily history.")
    p.add_argument("--mode", choices=["us-stock", "us-etf", "kr-stock", "kr-etf", "all"], default="all")
    p.add_argument("--start", default="2000-01-01")
    p.add_argument("--end", default=datetime.today().strftime("%Y-%m-%d"))
    p.add_argument("--max-items", type=int, default=0, help="0 means all resolved symbols.")
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--symbols", default="", help="Comma-separated symbol allowlist for smoke or targeted repair runs.")
    p.add_argument("--universe-path", default="", help="Optional pre-resolved universe CSV to avoid refetching listings per chunk.")
    p.add_argument("--batch-size", type=int, default=50)
    p.add_argument("--sleep-sec", type=float, default=0.2)
    p.add_argument("--skip-existing-min-bars", type=int, default=0)
    p.add_argument("--us-source", choices=["yahoo-chart", "fdr"], default="yahoo-chart")
    p.add_argument("--universe-only", action="store_true")
    p.add_argument("--out-base-us", default="data/prices_us_full_history")
    p.add_argument("--out-base-kr", default="data/prices_kr_full_history")
    p.add_argument("--report-path", default="backtests/full_market_history_backfill_report.csv")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    frames: list[pd.DataFrame] = []
    if args.mode in {"us-stock", "us-etf", "all"}:
        us_types = {"stock", "etf"} if args.mode == "all" else {args.mode.split("-")[1]}
        df = backfill_us(args, us_types)
        df["region"] = "US"
        frames.append(df)
    if args.mode in {"kr-stock", "kr-etf", "all"}:
        kr_types = {"stock", "etf"} if args.mode == "all" else {args.mode.split("-")[1]}
        df = backfill_kr(args, kr_types)
        df["region"] = "KR"
        frames.append(df)

    report = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    report_path = Path(args.report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(report_path, index=False, encoding="utf-8-sig")
    print(f"rows={len(report)} report={report_path}")
    if "status" in report.columns:
        print(report["status"].value_counts(dropna=False).to_string())


if __name__ == "__main__":
    main()
