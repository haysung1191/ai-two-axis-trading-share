import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import argparse
import os
import re
import time
from datetime import datetime, timedelta
from io import StringIO
from typing import Iterable, List

import pandas as pd
import requests
from bs4 import BeautifulSoup

import config
from kis_flow_data import merge_flow_frames, read_flow_file, write_flow_file


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://finance.naver.com/",
}


def _safe_today() -> str:
    dt = datetime.today()
    while dt.weekday() >= 5:
        dt -= timedelta(days=1)
    return dt.strftime("%Y%m%d")


def _collect_codes_from_price_base(price_base: str, market: str = "stock") -> List[str]:
    folder = os.path.join(price_base, market)
    if not os.path.isdir(folder):
        return []
    return sorted(name.replace(".csv.gz", "") for name in os.listdir(folder) if name.endswith(".csv.gz"))


def _fetch_html(code: str, page: int) -> str:
    url = f"https://finance.naver.com/item/frgn.naver?code={code}&page={page}"
    resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=30)
    resp.raise_for_status()
    if not resp.encoding:
        resp.encoding = "euc-kr"
    return resp.text


def _extract_last_page(html: str) -> int:
    soup = BeautifulSoup(html, "html.parser")
    navi = soup.select_one("table.Nnavi")
    if navi is None:
        return 1
    pages = []
    for link in navi.select("a[href]"):
        href = link.get("href", "")
        match = re.search(r"[?&]page=(\d+)", href)
        if match:
            pages.append(int(match.group(1)))
    return max(pages) if pages else 1


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df.columns, pd.MultiIndex):
        return df
    flat = []
    for col in df.columns:
        parts = [str(x).strip() for x in col if str(x).strip() and str(x) != "nan"]
        flat.append("_".join(parts))
    out = df.copy()
    out.columns = flat
    return out


def _normalize_naver_frame(df: pd.DataFrame) -> pd.DataFrame:
    tmp = _flatten_columns(df)
    col_map = {
        "날짜_날짜": "date",
        "날짜": "date",
        "거래량_거래량": "volume",
        "거래량": "volume",
        "기관_순매매량": "institution_net_volume",
        "외국인_순매매량": "foreign_net_volume",
        "외국인_보유주수": "foreign_shares",
        "외국인_보유율": "foreign_ratio",
    }
    tmp = tmp.rename(columns=col_map)
    required = ["date", "volume", "institution_net_volume", "foreign_net_volume", "foreign_shares", "foreign_ratio"]
    if any(col not in tmp.columns for col in required):
        return pd.DataFrame(columns=required)
    tmp = tmp[required].copy()
    tmp = tmp.dropna(subset=["date"])
    tmp["date"] = pd.to_datetime(tmp["date"], format="%Y.%m.%d", errors="coerce")
    tmp = tmp.dropna(subset=["date"])
    for col in ["volume", "institution_net_volume", "foreign_net_volume", "foreign_shares"]:
        tmp[col] = (
            tmp[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("+", "", regex=False)
            .str.strip()
        )
        tmp[col] = pd.to_numeric(tmp[col], errors="coerce")
    tmp["foreign_ratio"] = (
        tmp["foreign_ratio"].astype(str).str.replace("%", "", regex=False).str.replace(",", "", regex=False).str.strip()
    )
    tmp["foreign_ratio"] = pd.to_numeric(tmp["foreign_ratio"], errors="coerce")
    tmp = tmp.dropna(subset=["volume", "institution_net_volume", "foreign_net_volume"])
    return tmp.sort_values("date").drop_duplicates(subset=["date"]).reset_index(drop=True)


def _find_flow_table(page_html: str) -> pd.DataFrame:
    tables = pd.read_html(StringIO(page_html))
    for table in tables:
        flat = _flatten_columns(table)
        cols = set(flat.columns)
        if {"date", "volume", "institution_net_volume", "foreign_net_volume"}.issubset(
            set(
                flat.rename(
                    columns={
                        "날짜_날짜": "date",
                        "날짜": "date",
                        "거래량_거래량": "volume",
                        "거래량": "volume",
                        "기관_순매매량": "institution_net_volume",
                        "외국인_순매매량": "foreign_net_volume",
                    }
                ).columns
            )
        ):
            return table
    return pd.DataFrame()


def fetch_flow_history(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    html = _fetch_html(code, 1)
    last_page = _extract_last_page(html)
    frames = []
    start_dt = datetime.strptime(start_date, "%Y%m%d")
    end_dt = datetime.strptime(end_date, "%Y%m%d")
    for page in range(1, last_page + 1):
        if page == 1:
            page_html = html
        else:
            page_html = _fetch_html(code, page)
        table = _find_flow_table(page_html)
        if table.empty:
            continue
        df = _normalize_naver_frame(table)
        if df.empty:
            continue
        page_min = pd.to_datetime(df["date"]).min().to_pydatetime()
        page_max = pd.to_datetime(df["date"]).max().to_pydatetime()
        frames.append(df)
        if page_min <= start_dt:
            break
        if page_max < start_dt:
            break
        time.sleep(0.05)

    if not frames:
        return pd.DataFrame(
            columns=["date", "institution_net_volume", "foreign_net_volume", "foreign_shares", "foreign_ratio"]
        )

    out = pd.concat(frames, ignore_index=True)
    out = out[(out["date"] >= pd.Timestamp(start_dt)) & (out["date"] <= pd.Timestamp(end_dt))]
    out = out.sort_values("date").drop_duplicates(subset=["date"]).reset_index(drop=True)
    return out[["date", "institution_net_volume", "foreign_net_volume", "foreign_shares", "foreign_ratio"]]


def backfill_flows(
    codes: Iterable[str],
    out_base: str,
    years: int,
    incremental_days: int,
    sleep_sec: float,
) -> None:
    end_date = _safe_today()
    global_start_date = (datetime.strptime(end_date, "%Y%m%d") - timedelta(days=int(years * 370))).strftime("%Y%m%d")
    ok, fail = 0, 0

    for i, code in enumerate(codes, start=1):
        path = os.path.join(out_base, "stock", f"{code}.csv.gz")
        try:
            old_df = read_flow_file(path)
            if old_df.empty:
                start_date = global_start_date
            else:
                last_dt = pd.to_datetime(old_df["date"]).max()
                start_dt = max(
                    datetime.strptime(global_start_date, "%Y%m%d"),
                    last_dt.to_pydatetime() - timedelta(days=incremental_days),
                )
                start_date = start_dt.strftime("%Y%m%d")

            new_df = fetch_flow_history(code, start_date, end_date)
            if new_df.empty:
                print(f"[WARN] empty flow data code={code} start={start_date} end={end_date}")
                fail += 1
                continue
            merged = merge_flow_frames(old_df, new_df)
            write_flow_file(path, merged)
            ok += 1
        except Exception as e:
            print(f"[ERROR] flow backfill failed code={code} err={e}")
            fail += 1
        if i % 20 == 0:
            print(f"progress {i}")
        time.sleep(sleep_sec)
    print(f"done: success={ok}, failed={fail}, out={out_base}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Backfill daily investor-flow history for Korean stocks from Naver Finance.")
    p.add_argument("--price-base", type=str, default=(f"gs://{config.GCS_BUCKET_NAME}/prices" if config.GCS_BUCKET_NAME else "data/prices"))
    p.add_argument("--out-base", type=str, default=(f"gs://{config.GCS_BUCKET_NAME}/flows" if config.GCS_BUCKET_NAME else "data/flows"))
    p.add_argument("--years", type=int, default=5)
    p.add_argument("--incremental-days", type=int, default=45)
    p.add_argument("--sleep-sec", type=float, default=0.25)
    p.add_argument("--max-items", type=int, default=0)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    codes = _collect_codes_from_price_base(args.price_base, market="stock")
    if args.max_items and args.max_items > 0:
        codes = codes[: args.max_items]
    if not codes:
        raise RuntimeError(f"No stock codes found under {args.price_base}")
    print(f"codes={len(codes)}")
    backfill_flows(
        codes=codes,
        out_base=args.out_base,
        years=args.years,
        incremental_days=args.incremental_days,
        sleep_sec=args.sleep_sec,
    )
