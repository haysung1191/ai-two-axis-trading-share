from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import pandas as pd

from kis_api import KISApi
from tools.data_ingestion.kis_data_backfill import merge_frames, prices_to_frame


ROOT = REPO_ROOT
PRICE_ROOT = ROOT / "data" / "prices_operating_institutional_v1"
SUMMARY_PATH = ROOT / "backtests" / "kis_operating_price_refresh_summary.csv"


def _recent_business_day() -> str:
    dt = datetime.today()
    while dt.weekday() >= 5:
        dt -= timedelta(days=1)
    return dt.strftime("%Y%m%d")


def _read_existing(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["date", "close", "volume"])
    return pd.read_csv(path, compression="gzip", parse_dates=["date"]).sort_values("date").reset_index(drop=True)


def main() -> None:
    api = KISApi()
    end_date = _recent_business_day()
    rows: list[dict] = []

    for market in ["stock", "etf"]:
        for path in sorted((PRICE_ROOT / market).glob("*.csv.gz")):
            code = path.name.replace(".csv.gz", "")
            old_df = _read_existing(path)
            if old_df.empty:
                start_date = (datetime.strptime(end_date, "%Y%m%d") - timedelta(days=365 * 5)).strftime("%Y%m%d")
                last_existing = ""
            else:
                last_dt = pd.to_datetime(old_df["date"]).max()
                start_date = (last_dt.to_pydatetime() - timedelta(days=30)).strftime("%Y%m%d")
                last_existing = last_dt.strftime("%Y-%m-%d")

            prices = api.get_historical_prices(code, start_date, end_date, period="D", max_records=120)
            new_df = prices_to_frame(prices)
            merged = merge_frames(old_df, new_df)
            merged.to_csv(path, index=False, compression="gzip")
            last_updated = ""
            if not merged.empty:
                last_updated = pd.to_datetime(merged["date"]).max().strftime("%Y-%m-%d")
            rows.append(
                {
                    "Market": market.upper(),
                    "Code": code,
                    "LastExistingDate": last_existing,
                    "RefreshStartDate": start_date,
                    "RefreshEndDate": end_date,
                    "FetchedBars": int(len(new_df)),
                    "LastUpdatedDate": last_updated,
                }
            )
            time.sleep(0.08)

    summary = pd.DataFrame(rows)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(SUMMARY_PATH, index=False, encoding="utf-8-sig")
    print(f"rows={len(summary)}")
    print(f"end_date={end_date}")
    print(f"summary={SUMMARY_PATH}")


if __name__ == "__main__":
    main()
