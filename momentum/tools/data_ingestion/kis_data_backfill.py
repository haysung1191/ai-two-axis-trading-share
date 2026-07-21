import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import argparse
import hashlib
import os
import time
from io import BytesIO
from datetime import datetime, timedelta
from typing import Iterable, List, Tuple

import pandas as pd
from google.cloud import storage

import config
from kis_api import KISApi
from live_core.kis_screener_universe import (
    get_current_stock_universe,
    get_etf_tickers,
    get_historical_market_tickers,
)


def today_yyyymmdd() -> str:
    dt = datetime.today()
    while dt.weekday() >= 5:
        dt -= timedelta(days=1)
    return dt.strftime("%Y%m%d")


def stable_sample(tickers: List[Tuple[str, str]], max_items: int) -> List[Tuple[str, str]]:
    if max_items <= 0 or len(tickers) <= max_items:
        return tickers

    def h(code: str) -> str:
        return hashlib.md5(str(code).encode("utf-8")).hexdigest()

    return sorted(tickers, key=lambda x: h(x[0]))[:max_items]


def get_universe(
    mode: str,
    max_items: int,
    historical_stock_universe: bool,
    start_date: str,
    end_date: str,
) -> List[Tuple[str, str, str]]:
    items: List[Tuple[str, str, str]] = []

    if mode in {"stock", "both"}:
        if historical_stock_universe:
            stock_tickers = get_historical_market_tickers(
                start_date,
                end_date,
                step_days=30,
                fallback_loader=lambda: get_current_stock_universe(
                    config_module=config,
                    repo_root=REPO_ROOT,
                ),
            )
        else:
            stock_tickers = sorted(
                get_current_stock_universe(
                    config_module=config,
                    repo_root=REPO_ROOT,
                ),
                key=lambda x: str(x[0]),
            )
        use = stable_sample(stock_tickers, max_items)
        for code, name in use:
            items.append((code, name, "stock"))

    if mode in {"etf", "both"}:
        etf_tickers = sorted(get_etf_tickers(), key=lambda x: str(x[0]))
        use = stable_sample(etf_tickers, max_items)
        for code, name in use:
            items.append((code, name, "etf"))

    return items


def prices_to_frame(prices: List[dict]) -> pd.DataFrame:
    rows = []
    for p in prices:
        d = p.get("stck_bsop_date")
        c = p.get("stck_clpr")
        v = p.get("acml_vol")
        if not d or c is None:
            continue
        rows.append(
            {
                "date": pd.to_datetime(d, format="%Y%m%d"),
                "close": float(c),
                "volume": float(v) if v is not None else 0.0,
            }
        )
    if not rows:
        return pd.DataFrame(columns=["date", "close", "volume"])
    df = pd.DataFrame(rows).drop_duplicates(subset=["date"]).sort_values("date")
    df = df[df["close"] > 0]
    return df.reset_index(drop=True)


def build_path(base: str, market: str, code: str) -> str:
    return f"{base}/{market}/{code}.csv.gz"


def parse_gs_path(path: str) -> Tuple[str, str]:
    no_scheme = path.replace("gs://", "", 1)
    if "/" not in no_scheme:
        return no_scheme, ""
    bucket_name, blob_name = no_scheme.split("/", 1)
    return bucket_name, blob_name


def read_existing(path: str) -> pd.DataFrame:
    try:
        if path.startswith("gs://"):
            bucket_name, blob_name = parse_gs_path(path)
            client = storage.Client()
            blob = client.bucket(bucket_name).blob(blob_name)
            if not blob.exists(client):
                return pd.DataFrame(columns=["date", "close", "volume"])
            raw = blob.download_as_bytes()
            return pd.read_csv(BytesIO(raw), compression="gzip", parse_dates=["date"])
        return pd.read_csv(path, compression="gzip", parse_dates=["date"])
    except Exception as e:
        print(f"[WARN] read_existing failed path={path} err={e}")
        return pd.DataFrame(columns=["date", "close", "volume"])


def merge_frames(old: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    if old.empty:
        return new
    if new.empty:
        return old
    out = pd.concat([old, new], ignore_index=True)
    out = out.drop_duplicates(subset=["date"]).sort_values("date")
    out = out[out["close"] > 0]
    return out.reset_index(drop=True)


def write_frame(path: str, df: pd.DataFrame) -> None:
    if path.startswith("gs://"):
        bucket_name, blob_name = parse_gs_path(path)
        client = storage.Client()
        blob = client.bucket(bucket_name).blob(blob_name)
        buf = BytesIO()
        df.to_csv(buf, index=False, compression="gzip")
        buf.seek(0)
        blob.upload_from_file(buf, content_type="application/gzip")
        return
    df.to_csv(path, index=False, compression="gzip")


def ensure_local_dirs(base: str) -> None:
    if base.startswith("gs://"):
        return
    os.makedirs(os.path.join(base, "stock"), exist_ok=True)
    os.makedirs(os.path.join(base, "etf"), exist_ok=True)


def backfill(
    mode: str,
    years: int,
    incremental_days: int,
    max_items: int,
    out_base: str,
    sleep_sec: float,
    historical_stock_universe: bool,
) -> None:
    api = KISApi()
    end_date = today_yyyymmdd()
    global_start_date = (datetime.strptime(end_date, "%Y%m%d") - timedelta(days=int(years * 370))).strftime("%Y%m%d")
    universe = get_universe(mode, max_items, historical_stock_universe, global_start_date, end_date)
    ensure_local_dirs(out_base)

    max_records = max(400, int(years * 280))

    print(
        f"universe={len(universe)}, global_start={global_start_date}, end={end_date}, "
        f"incremental_days={incremental_days}, max_records={max_records}, "
        f"historical_stock_universe={historical_stock_universe}"
    )
    ok, fail = 0, 0

    for i, (code, name, market) in enumerate(universe, start=1):
        if i % 50 == 0:
            print(f"progress {i}/{len(universe)}")

        try:
            path = build_path(out_base, market, code)
            old_df = read_existing(path)

            if old_df.empty:
                start_date = global_start_date
            else:
                last_dt = pd.to_datetime(old_df["date"]).max()
                start_dt = max(
                    datetime.strptime(global_start_date, "%Y%m%d"),
                    (last_dt.to_pydatetime() - timedelta(days=incremental_days)),
                )
                start_date = start_dt.strftime("%Y%m%d")

            prices = api.get_historical_prices(code, start_date, end_date, period="D", max_records=max_records)
            new_df = prices_to_frame(prices)
            if new_df.empty:
                fail += 1
                continue

            merged = merge_frames(old_df, new_df)
            write_frame(path, merged)

            ok += 1
        except Exception as e:
            print(f"[ERROR] code={code} name={name} market={market} failed: {e}")
            fail += 1
        time.sleep(sleep_sec)

    print(f"done: success={ok}, failed={fail}, out={out_base}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Backfill KIS historical daily prices to csv.gz.")
    p.add_argument("--mode", choices=["stock", "etf", "both"], default="both")
    p.add_argument("--years", type=int, default=5)
    p.add_argument("--incremental-days", type=int, default=35)
    p.add_argument("--max-items", type=int, default=500)
    p.add_argument("--out-base", type=str, default=(f"gs://{config.GCS_BUCKET_NAME}/prices" if config.GCS_BUCKET_NAME else "data/prices"))
    p.add_argument("--sleep-sec", type=float, default=0.05)
    p.add_argument("--historical-stock-universe", type=int, default=1, help="1: use monthly historical stock universe snapshots")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    backfill(
        mode=args.mode,
        years=args.years,
        incremental_days=args.incremental_days,
        max_items=args.max_items,
        out_base=args.out_base,
        sleep_sec=args.sleep_sec,
        historical_stock_universe=bool(args.historical_stock_universe),
    )
