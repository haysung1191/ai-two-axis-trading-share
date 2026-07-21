import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import argparse
import re
from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd

import config
from datetime import datetime, timezone


@dataclass
class StrategyConfig:
    name: str
    rebalance: str  # "D" or "W-FRI"
    top_n_stock: int
    top_n_etf: int
    fee_rate: float
    use_buffer: bool = False
    entry_rank: int = 20
    exit_rank: int = 25


def add_signals(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    mom_cols = ["momentum_1m", "momentum_3m", "momentum_6m", "momentum_12m"]
    for c in mom_cols:
        if c not in out.columns:
            out[c] = 0.0

    pos_count = (out[mom_cols] > 0).sum(axis=1)
    score_consistency = pos_count * 10.0
    score_avg = ((out["avg_momentum"].clip(-20, 80) + 20) / 100.0) * 25.0
    score_mrat = (20.0 - (out["MRAT"] - 1.35).abs() * 25.0).clip(0, 20)
    score_mad = (15.0 - (out["MAD_gap_pct"] - 20).abs() * 0.25).clip(0, 15)
    out["buy_score"] = (score_consistency + score_avg + score_mrat + score_mad).round(4)

    out["overheat_warning"] = "정상"
    out.loc[(out["MAD_gap_pct"] >= 60) | (out["MRAT"] >= 1.9), "overheat_warning"] = "주의"
    out.loc[(out["MAD_gap_pct"] >= 100) | (out["MRAT"] >= 2.3) | (out["momentum_1m"] >= 45), "overheat_warning"] = "과열"
    return out


def list_snapshot_uris(prefix: str, bucket_name: str) -> List[Tuple[pd.Timestamp, str]]:
    if not bucket_name:
        raise RuntimeError("GCS bucket is not configured.")

    from google.cloud import storage

    pat = re.compile(rf"^{re.escape(prefix)}(\d{{8}})_(\d{{4}})\.xlsx$")
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blobs = list(bucket.list_blobs(prefix=prefix))

    out: List[Tuple[pd.Timestamp, str]] = []
    for b in blobs:
        name = b.name.split("/")[-1]
        m = pat.match(name)
        if not m:
            continue
        ts = pd.to_datetime(m.group(1) + m.group(2), format="%Y%m%d%H%M")
        uri = f"gs://{bucket_name}/{b.name}"
        out.append((ts, uri))
    out.sort(key=lambda x: x[0])
    return out


def load_snapshot_series(prefix: str, tag: str, bucket_name: str) -> Dict[pd.Timestamp, pd.DataFrame]:
    pairs = list_snapshot_uris(prefix, bucket_name)
    # Keep latest snapshot per calendar day.
    latest_per_day: Dict[pd.Timestamp, Tuple[pd.Timestamp, str]] = {}
    for ts, uri in pairs:
        day = ts.normalize()
        prev = latest_per_day.get(day)
        if prev is None or ts > prev[0]:
            latest_per_day[day] = (ts, uri)

    out: Dict[pd.Timestamp, pd.DataFrame] = {}

    for day, (ts, uri) in sorted(latest_per_day.items(), key=lambda x: x[0]):
        df = pd.read_excel(uri)
        if df is None or df.empty:
            continue
        need = ["Code", "Name", "current_price", "MAD_gap_pct", "MRAT", "momentum_1m", "momentum_3m", "momentum_6m", "momentum_12m", "avg_momentum"]
        miss = [c for c in need if c not in df.columns]
        if miss:
            continue

        df = df.copy()
        df["Code"] = df["Code"].astype(str).str.zfill(6)
        df["ticker"] = tag + "_" + df["Code"]
        df = add_signals(df)
        df = df[df["current_price"] > 0]
        df = df.drop_duplicates(subset=["ticker"])
        out[day] = df.set_index("ticker")
    return out


def choose_dates(dates: Sequence[pd.Timestamp], rule: str) -> List[pd.Timestamp]:
    idx = pd.DatetimeIndex(sorted(dates))
    if rule == "D":
        return list(idx)
    if rule == "W-FRI":
        out = list(idx[idx.weekday == 4])
        if out and out[-1] != idx[-1]:
            out.append(idx[-1])
        if not out:
            out = [idx[-1]]
        return out
    raise ValueError(f"Unknown rule: {rule}")


def select_with_buffer(ranked: List[str], prev: List[str], top_n: int, use_buffer: bool, entry_rank: int, exit_rank: int) -> List[str]:
    if not ranked:
        return []
    if not use_buffer:
        return ranked[:top_n]
    rmap = {t: i + 1 for i, t in enumerate(ranked)}
    kept = [t for t in prev if t in rmap and rmap[t] <= exit_rank]
    selected = list(kept)
    for t in ranked:
        if rmap[t] <= entry_rank and t not in selected:
            selected.append(t)
        if len(selected) >= top_n:
            break
    return selected[:top_n]


def get_ranked(df: pd.DataFrame, top_n: int) -> List[str]:
    if df.empty:
        return []
    d = df[df["overheat_warning"] != "과열"].sort_values(["buy_score", "avg_momentum"], ascending=[False, False])
    return list(d.head(max(top_n * 2, top_n)).index)


def simulate(
    stock_snap: Dict[pd.Timestamp, pd.DataFrame],
    etf_snap: Dict[pd.Timestamp, pd.DataFrame],
    stg: StrategyConfig,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    dates = sorted(set(stock_snap.keys()).intersection(set(etf_snap.keys())))
    if len(dates) < 2:
        raise RuntimeError("공통 스냅샷이 부족합니다.")

    reb_dates = set(choose_dates(dates, stg.rebalance))
    hold_s: List[str] = []
    hold_e: List[str] = []
    w_now: Dict[str, float] = {}
    turns: List[float] = []
    rows = []

    for i in range(1, len(dates)):
        prev_dt = dates[i - 1]
        dt = dates[i]
        prev_s = stock_snap[prev_dt]
        prev_e = etf_snap[prev_dt]
        next_s = stock_snap[dt]
        next_e = etf_snap[dt]

        fee = 0.0
        if prev_dt in reb_dates:
            ranked_s = get_ranked(prev_s, stg.top_n_stock)
            ranked_e = get_ranked(prev_e, stg.top_n_etf)
            hold_s = select_with_buffer(ranked_s, hold_s, stg.top_n_stock, stg.use_buffer, stg.entry_rank, stg.exit_rank)
            hold_e = select_with_buffer(ranked_e, hold_e, stg.top_n_etf, stg.use_buffer, stg.entry_rank, stg.exit_rank)

            w_tar: Dict[str, float] = {}
            if hold_s:
                ws = 0.5 / len(hold_s)
                w_tar.update({t: ws for t in hold_s})
            if hold_e:
                we = 0.5 / len(hold_e)
                w_tar.update({t: we for t in hold_e})
            if w_tar:
                s = sum(w_tar.values())
                w_tar = {k: v / s for k, v in w_tar.items()}

            uni = set(w_now) | set(w_tar)
            turn = sum(abs(w_tar.get(k, 0.0) - w_now.get(k, 0.0)) for k in uni)
            turns.append(turn)
            fee = turn * stg.fee_rate
            w_now = w_tar

        day_ret = 0.0
        for t, w in w_now.items():
            if t.startswith("S_"):
                if t in prev_s.index and t in next_s.index:
                    r = next_s.at[t, "current_price"] / prev_s.at[t, "current_price"] - 1.0
                else:
                    r = 0.0
            else:
                if t in prev_e.index and t in next_e.index:
                    r = next_e.at[t, "current_price"] / prev_e.at[t, "current_price"] - 1.0
                else:
                    r = 0.0
            if pd.isna(r) or np.isinf(r):
                r = 0.0
            day_ret += w * float(r)
        day_ret -= fee

        rows.append({"date": dt, "daily_return": day_ret, "n_stock": len(hold_s), "n_etf": len(hold_e)})

    df = pd.DataFrame(rows).set_index("date")
    df["nav"] = (1.0 + df["daily_return"]).cumprod()

    if df.empty:
        metrics = {"FinalNAV": 1.0, "CAGR": 0.0, "MDD": 0.0, "Sharpe": 0.0, "AvgTurnover": 0.0}
    else:
        years = max((df.index[-1] - df.index[0]).days / 365.25, 1e-9)
        cagr = float(df["nav"].iloc[-1] ** (1 / years) - 1)
        hwm = df["nav"].cummax()
        mdd = float((df["nav"] / hwm - 1.0).min())
        if len(df) < 20:
            sr = float("nan")
        else:
            sr = float(df["daily_return"].mean() / (df["daily_return"].std(ddof=0) + 1e-12) * np.sqrt(252))
        avg_turn = float(np.mean(turns)) if turns else 0.0
        metrics = {"FinalNAV": float(df["nav"].iloc[-1]), "CAGR": cagr, "MDD": mdd, "Sharpe": sr, "AvgTurnover": avg_turn}
    return df, metrics


def main() -> None:
    p = argparse.ArgumentParser(description="Backtest using saved screener snapshots in GCS.")
    p.add_argument("--top-n", type=int, default=20)
    p.add_argument("--fee-bps", type=float, default=8.0)
    p.add_argument("--save-prefix", type=str, default="snapshot_backtest")
    p.add_argument("--bucket", type=str, default=(config.GCS_BUCKET_NAME or ""))
    p.add_argument("--min-common-days", type=int, default=20)
    args = p.parse_args()

    print("Loading snapshots from GCS...")
    stock_snap = load_snapshot_series("momentum_results_", "S", args.bucket)
    etf_snap = load_snapshot_series("etf_results_", "E", args.bucket)
    common = sorted(set(stock_snap).intersection(set(etf_snap)))
    print(f"stock snapshots={len(stock_snap)}, etf snapshots={len(etf_snap)}, common={len(common)}")
    if len(common) < 2:
        raise RuntimeError("공통 스냅샷이 2개 미만이라 백테스트가 불가능합니다.")

    fee = args.fee_bps / 10000.0
    strategies = [
        StrategyConfig("Daily Top20", "D", args.top_n, args.top_n, fee, False),
        StrategyConfig("Weekly Top20", "W-FRI", args.top_n, args.top_n, fee, False),
        StrategyConfig("Weekly Buffer 20/25", "W-FRI", args.top_n, args.top_n, fee, True, 20, 25),
    ]

    summary = []
    nav = pd.DataFrame(index=pd.DatetimeIndex(common[1:]))
    for s in strategies:
        res, m = simulate(stock_snap, etf_snap, s)
        row = {"Strategy": s.name}
        row.update(m)
        summary.append(row)
        nav[s.name] = res["nav"]

    s_df = pd.DataFrame(summary)
    print("\n=== Snapshot Backtest ===")
    print(s_df.to_string(index=False))
    s_df.to_csv(f"{args.save_prefix}_summary.csv", index=False, encoding="utf-8-sig")
    nav.to_csv(f"{args.save_prefix}_nav.csv", encoding="utf-8-sig")
    print(f"\nSaved: {args.save_prefix}_summary.csv")
    print(f"Saved: {args.save_prefix}_nav.csv")
    if len(common) < args.min_common_days:
        print(
            f"주의: 공통 스냅샷 {len(common)}일로 표본이 부족합니다. "
            f"(권장 최소 {args.min_common_days}일)"
        )

    if args.bucket:
        from google.cloud import storage

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        storage_client = storage.Client()
        bucket = storage_client.bucket(args.bucket)
        summary_blob = bucket.blob(f"backtests/{args.save_prefix}_summary_{ts}.csv")
        nav_blob = bucket.blob(f"backtests/{args.save_prefix}_nav_{ts}.csv")
        summary_blob.upload_from_filename(f"{args.save_prefix}_summary.csv")
        nav_blob.upload_from_filename(f"{args.save_prefix}_nav.csv")
        print(f"Uploaded: gs://{args.bucket}/{summary_blob.name}")
        print(f"Uploaded: gs://{args.bucket}/{nav_blob.name}")


if __name__ == "__main__":
    main()
