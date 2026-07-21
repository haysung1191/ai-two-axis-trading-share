import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import argparse
import os
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup

from news_sidecar_data import build_coverage_report, write_news_file


DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://finance.naver.com/",
}

POSITIVE_WORDS = [
    "호실적",
    "성장",
    "강세",
    "상승",
    "수주",
    "계약",
    "확대",
    "흑자",
    "개선",
    "돌파",
    "급등",
    "기대",
    "상향",
    "투자",
    "승인",
    "출시",
]

NEGATIVE_WORDS = [
    "부진",
    "약세",
    "하락",
    "적자",
    "소송",
    "조사",
    "경고",
    "리콜",
    "지연",
    "악화",
    "급락",
    "하향",
    "우려",
    "불확실",
    "논란",
    "축소",
]


def _safe_today() -> str:
    dt = datetime.today()
    while dt.weekday() >= 5:
        dt -= timedelta(days=1)
    return dt.strftime("%Y%m%d")


def _collect_codes_from_price_base(price_base: str, market: str = "stock") -> list[str]:
    folder = os.path.join(price_base, market)
    if not os.path.isdir(folder):
        return []
    return sorted(name.replace(".csv.gz", "") for name in os.listdir(folder) if name.endswith(".csv.gz"))


def _score_title(title: str) -> tuple[int, int]:
    text = str(title)
    pos = sum(text.count(word) for word in POSITIVE_WORDS)
    neg = sum(text.count(word) for word in NEGATIVE_WORDS)
    return pos, neg


def _fetch_html(code: str, page: int) -> str:
    url = f"https://finance.naver.com/item/news_news.naver?code={code}&page={page}"
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


def _normalize_news_table(df: pd.DataFrame) -> pd.DataFrame:
    tmp = df.copy()
    tmp.columns = [str(c).strip() for c in tmp.columns]
    title_col = next((c for c in tmp.columns if "제목" in c), None)
    date_col = next((c for c in tmp.columns if "날짜" in c), None)
    source_col = next((c for c in tmp.columns if "정보제공" in c), None)
    if title_col is None or date_col is None:
        return pd.DataFrame(columns=["date", "title", "source"])
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(tmp[date_col], errors="coerce"),
            "title": tmp[title_col].astype(str).str.strip(),
            "source": tmp[source_col].astype(str).str.strip() if source_col is not None else "",
        }
    )
    out = out.dropna(subset=["date"])
    out = out[~out["title"].str.contains("연관기사 목록", na=False)]
    out = out[out["title"].str.len().gt(0)]
    return out.drop_duplicates(subset=["date", "title"]).sort_values(["date", "title"]).reset_index(drop=True)


def _find_news_table(page_html: str) -> pd.DataFrame:
    tables = pd.read_html(StringIO(page_html))
    for table in tables:
        cols = [str(c).strip() for c in table.columns]
        if any("제목" in c for c in cols) and any("날짜" in c for c in cols):
            return table
    return pd.DataFrame()


def fetch_news_history(code: str, start_date: str, end_date: str) -> pd.DataFrame:
    html = _fetch_html(code, 1)
    last_page = _extract_last_page(html)
    start_ts = pd.Timestamp(datetime.strptime(start_date, "%Y%m%d"))
    end_ts = pd.Timestamp(datetime.strptime(end_date, "%Y%m%d"))
    daily: dict[str, dict[str, float]] = defaultdict(lambda: {"article_count": 0.0, "positive_hits": 0.0, "negative_hits": 0.0})

    for page in range(1, last_page + 1):
        page_html = html if page == 1 else _fetch_html(code, page)
        table = _find_news_table(page_html)
        if table.empty:
            continue
        news = _normalize_news_table(table)
        if news.empty:
            continue
        oldest = pd.to_datetime(news["date"]).min()
        for _, row in news.iterrows():
            dt = pd.Timestamp(row["date"]).normalize()
            if dt < start_ts or dt > end_ts:
                continue
            date_str = dt.strftime("%Y-%m-%d")
            pos, neg = _score_title(row["title"])
            bucket = daily[date_str]
            bucket["article_count"] += 1.0
            bucket["positive_hits"] += float(pos)
            bucket["negative_hits"] += float(neg)
        if oldest <= start_ts:
            break
        time.sleep(0.05)

    rows = []
    for date_str, stats in sorted(daily.items()):
        rows.append(
            {
                "date": date_str,
                "article_count": stats["article_count"],
                "positive_hits": stats["positive_hits"],
                "negative_hits": stats["negative_hits"],
                "title_score": stats["positive_hits"] - stats["negative_hits"],
            }
        )
    return pd.DataFrame(rows, columns=["date", "article_count", "positive_hits", "negative_hits", "title_score"])


def backfill_news(codes: list[str], out_base: str, years: int, sleep_sec: float) -> None:
    end_date = _safe_today()
    start_date = (datetime.strptime(end_date, "%Y%m%d") - timedelta(days=int(years * 370))).strftime("%Y%m%d")
    ok, fail = 0, 0
    for i, code in enumerate(codes, start=1):
        try:
            df = fetch_news_history(code, start_date, end_date)
            write_news_file(os.path.join(out_base, "stock", f"{code}.csv.gz"), df)
            ok += 1
        except Exception as e:
            print(f"[ERROR] news backfill failed code={code} err={e}")
            fail += 1
        if i % 10 == 0:
            print(f"progress {i}")
        time.sleep(sleep_sec)
    print(f"done: success={ok}, failed={fail}, out={out_base}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Backfill Korean stock news sidecar from Naver Finance headlines.")
    p.add_argument("--price-base", type=str, default="data/prices_operating_institutional_v1")
    p.add_argument("--out-base", type=str, default="data/news_kis_naver")
    p.add_argument("--coverage-out", type=str, default="backtests/kis_news_sidecar_coverage.csv")
    p.add_argument("--years", type=int, default=2)
    p.add_argument("--sleep-sec", type=float, default=0.15)
    p.add_argument("--max-items", type=int, default=0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    codes = _collect_codes_from_price_base(args.price_base, market="stock")
    if args.max_items and args.max_items > 0:
        codes = codes[: args.max_items]
    if not codes:
        raise RuntimeError(f"No stock codes found under {args.price_base}")
    os.makedirs(os.path.join(args.out_base, "stock"), exist_ok=True)
    backfill_news(codes, args.out_base, years=args.years, sleep_sec=args.sleep_sec)
    coverage = build_coverage_report(args.out_base, market="stock")
    coverage.to_csv(args.coverage_out, index=False)
    print(coverage.head(20).to_string(index=False))
    print()
    print(f"saved coverage={args.coverage_out}")


if __name__ == "__main__":
    main()
