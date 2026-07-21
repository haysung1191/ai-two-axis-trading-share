import argparse
from io import StringIO
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from typing import Any

import pandas as pd
import requests


API_URL = "https://en.wikipedia.org/w/api.php"
PAGE_TITLE = "S&P 100"
OLDID_URL = "https://en.wikipedia.org/w/index.php?title=S%26P_100&oldid={oldid}"


def month_ends(start: str, end: str) -> list[pd.Timestamp]:
    idx = pd.date_range(start=start, end=end, freq="ME")
    return [pd.Timestamp(x).normalize() for x in idx]


def fetch_revision_before(ts: pd.Timestamp, session: requests.Session) -> dict[str, Any] | None:
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": PAGE_TITLE,
        "rvlimit": 1,
        "rvdir": "older",
        "rvstart": ts.strftime("%Y-%m-%dT23:59:59Z"),
        "rvprop": "ids|timestamp",
    }
    resp = session.get(API_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        revs = page.get("revisions", [])
        if revs:
            rev = revs[0]
            return {
                "oldid": int(rev["revid"]),
                "timestamp": pd.Timestamp(rev["timestamp"]).normalize(),
            }
    return None


def parse_constituents_from_oldid(oldid: int, session: requests.Session) -> pd.DataFrame:
    url = OLDID_URL.format(oldid=oldid)
    html = session.get(url, timeout=30).text
    tables = pd.read_html(StringIO(html))
    for table in tables:
        cols = {str(c) for c in table.columns}
        if {"Symbol", "Name", "Sector"}.issubset(cols):
            out = table[["Symbol", "Name", "Sector"]].copy()
            out["Symbol"] = out["Symbol"].astype(str).str.strip()
            out["YahooTicker"] = out["Symbol"].str.replace(".", "-", regex=False)
            return out.sort_values("Symbol").reset_index(drop=True)
        if {"Symbol", "Name"}.issubset(cols):
            out = table[["Symbol", "Name"]].copy()
            out["Sector"] = pd.NA
            out["Symbol"] = out["Symbol"].astype(str).str.strip()
            out["YahooTicker"] = out["Symbol"].str.replace(".", "-", regex=False)
            return out.sort_values("Symbol").reset_index(drop=True)
    raise RuntimeError(f"Could not find constituent table for oldid={oldid}")


def build_snapshots(start: str, end: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    snap_rows: list[dict[str, Any]] = []
    cache: dict[int, pd.DataFrame] = {}
    dates = month_ends(start, end)
    for dt in dates:
        rev = fetch_revision_before(dt, session)
        if not rev:
            continue
        oldid = int(rev["oldid"])
        if oldid not in cache:
            cache[oldid] = parse_constituents_from_oldid(oldid, session)
        df = cache[oldid].copy()
        df["SnapshotDate"] = dt.date().isoformat()
        df["RevisionDate"] = pd.Timestamp(rev["timestamp"]).date().isoformat()
        df["OldId"] = oldid
        snap_rows.extend(df.to_dict("records"))

    snapshots = pd.DataFrame(snap_rows)
    if snapshots.empty:
        return snapshots, pd.DataFrame()

    unique_snapshots = (
        snapshots[["SnapshotDate", "RevisionDate", "OldId"]]
        .drop_duplicates()
        .sort_values("SnapshotDate")
        .reset_index(drop=True)
    )
    next_dates = pd.to_datetime(unique_snapshots["SnapshotDate"]).shift(-1)
    unique_snapshots["StartDate"] = unique_snapshots["SnapshotDate"]
    unique_snapshots["EndDate"] = (
        next_dates.sub(pd.Timedelta(days=1)).dt.date.astype(str).fillna(pd.to_datetime(end).date().isoformat())
    )

    interval_frames = []
    for _, snap in unique_snapshots.iterrows():
        part = snapshots[snapshots["SnapshotDate"].astype(str) == str(snap["SnapshotDate"])].copy()
        part["StartDate"] = snap["StartDate"]
        part["EndDate"] = snap["EndDate"]
        part["UniverseType"] = "WIKIPEDIA_REVISION_POINT_IN_TIME_APPROX"
        interval_frames.append(part)

    intervals = (
        pd.concat(interval_frames, ignore_index=True)
        [["Symbol", "YahooTicker", "Name", "Sector", "UniverseType", "StartDate", "EndDate", "SnapshotDate", "RevisionDate", "OldId"]]
        .sort_values(["StartDate", "Symbol"])
        .reset_index(drop=True)
    )
    return snapshots, intervals


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build approximate point-in-time S&P 100 membership from Wikipedia revision snapshots.")
    p.add_argument("--start", type=str, default="2015-01-01")
    p.add_argument("--end", type=str, default="2026-03-31")
    p.add_argument("--snapshot-path", type=str, default="backtests/us_sp100_membership_wiki_snapshots.csv")
    p.add_argument("--interval-path", type=str, default="backtests/us_sp100_membership_wiki_intervals.csv")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    snapshots, intervals = build_snapshots(args.start, args.end)
    Path(args.snapshot_path).parent.mkdir(parents=True, exist_ok=True)
    snapshots.to_csv(args.snapshot_path, index=False, encoding="utf-8-sig")
    intervals.to_csv(args.interval_path, index=False, encoding="utf-8-sig")
    print(f"saved {args.snapshot_path} rows={len(snapshots)}")
    print(f"saved {args.interval_path} rows={len(intervals)}")
    if not intervals.empty:
        summary = (
            intervals.groupby("StartDate")["Symbol"]
            .nunique()
            .rename("ConstituentCount")
            .reset_index()
        )
        print(summary.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
