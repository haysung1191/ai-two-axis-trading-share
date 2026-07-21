from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
PRICE_DIR = ROOT / "data" / "prices_operating_institutional_v1" / "stock"
INPUT_DIR = ROOT / "inputs" / "event_momentum_mad_minimal"
OUTPUT_DIR = ROOT / "backtests" / "event_momentum_mad_minimal_correction_run"

EVENT_PATH = INPUT_DIR / "events.csv"
BASKET_PATH = INPUT_DIR / "baskets.csv"

ALLOWED_EVENT_TYPES = {"policy_regulation", "tariff_trade", "commodity_shock"}
MOMENTUM_LOOKBACKS = (20, 60, 120)
SELECTION_RATIO = 0.30
MAD_LOOKBACK = 20
MAX_HOLD_DAYS = 20
REBALANCE_EVERY = 5
MAX_CONCURRENT_POSITIONS = 10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-path", type=Path, default=EVENT_PATH)
    parser.add_argument("--basket-path", type=Path, default=BASKET_PATH)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    return parser.parse_args()


def load_inputs(event_path: Path, basket_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    events = pd.read_csv(event_path, dtype={"event_id": str, "event_type": str})
    baskets = pd.read_csv(basket_path, dtype={"event_id": str, "ticker": str, "name": str, "link_type": str, "rationale": str})
    return events, baskets


def load_close_matrix(tickers: list[str]) -> pd.DataFrame:
    series = []
    for ticker in tickers:
        path = PRICE_DIR / f"{ticker}.csv.gz"
        if not path.exists():
            raise FileNotFoundError(f"missing price file for {ticker}: {path}")
        df = pd.read_csv(path, compression="gzip", parse_dates=["date"])
        df = df[["date", "close"]].copy()
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna(subset=["date", "close"])
        df = df[df["close"] > 0].drop_duplicates(subset=["date"]).sort_values("date")
        series.append(pd.Series(df["close"].values, index=pd.to_datetime(df["date"]), name=ticker))
    close = pd.concat(series, axis=1).sort_index().dropna(how="any")
    if close.empty:
        raise ValueError("no common close matrix available")
    return close


def next_trade_date(dates: pd.DatetimeIndex, ts: pd.Timestamp) -> pd.Timestamp | None:
    later = dates[dates > ts]
    return pd.Timestamp(later[0]) if len(later) else None


def calculate_momentum_scores(close: pd.DataFrame, eval_date: pd.Timestamp, tickers: list[str]) -> pd.DataFrame:
    pos = close.index.get_loc(eval_date)
    rows = []
    for ticker in tickers:
        r20 = close.iloc[pos][ticker] / close.iloc[pos - 20][ticker] - 1.0
        r60 = close.iloc[pos][ticker] / close.iloc[pos - 60][ticker] - 1.0
        r120 = close.iloc[pos][ticker] / close.iloc[pos - 120][ticker] - 1.0
        score = float(np.mean([r20, r60, r120]))
        rows.append({"Ticker": ticker, "R20": float(r20), "R60": float(r60), "R120": float(r120), "MomentumScore": score})
    scores = pd.DataFrame(rows).sort_values(["MomentumScore", "Ticker"], ascending=[False, True]).reset_index(drop=True)
    scores["Rank"] = range(1, len(scores) + 1)
    return scores


def apply_mad_sizing(scores: pd.DataFrame) -> pd.DataFrame:
    median_r20 = float(scores["R20"].median())
    mad = float(np.median(np.abs(scores["R20"] - median_r20)))
    scale = mad if mad > 1e-12 else 1e-12
    scores = scores.copy()
    scores["MadScore"] = (scores["R20"] - median_r20).abs() / scale
    select_n = max(1, math.floor(len(scores) * SELECTION_RATIO))
    selected = scores[scores["MomentumScore"] > 0].head(select_n).copy()
    if selected.empty:
        return pd.DataFrame(columns=["Ticker", "Rank", "MomentumScore", "R20", "R60", "R120", "MadScore", "Weight"])
    selected["BaseWeight"] = 1.0 / len(selected)
    selected["MadMultiplier"] = 1.0 / (1.0 + selected["MadScore"])
    selected["RawWeight"] = selected["BaseWeight"] * selected["MadMultiplier"]
    selected["Weight"] = selected["RawWeight"] / selected["RawWeight"].sum()
    return selected[["Ticker", "Rank", "MomentumScore", "R20", "R60", "R120", "MadScore", "Weight"]].copy()


def build_event_schedule(event: pd.Series, close: pd.DataFrame, basket: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    event_date = pd.Timestamp(event["event_date"])
    basket_tickers = basket["ticker"].astype(str).tolist()
    eval_date = next_trade_date(close.index, event_date)
    if eval_date is None:
        return pd.DataFrame(), [{"event_id": event["event_id"], "status": "SKIP", "reason": "no evaluation date after event"}]
    eval_pos = close.index.get_loc(eval_date)
    if eval_pos < max(MOMENTUM_LOOKBACKS):
        return pd.DataFrame(), [{"event_id": event["event_id"], "status": "SKIP", "reason": "insufficient momentum history"}]
    if len(basket_tickers) < 3:
        return pd.DataFrame(), [{"event_id": event["event_id"], "status": "SKIP", "reason": "basket has fewer than 3 names"}]

    logs: list[dict] = []
    schedule_rows: list[dict] = []
    for step in range(0, MAX_HOLD_DAYS + 1, REBALANCE_EVERY):
        current_eval_pos = eval_pos + step
        if current_eval_pos >= len(close.index) - 1:
            break
        current_eval_date = pd.Timestamp(close.index[current_eval_pos])
        trade_date = pd.Timestamp(close.index[current_eval_pos + 1])
        scores = calculate_momentum_scores(close, current_eval_date, basket_tickers)
        selected = apply_mad_sizing(scores)
        if selected.empty:
            logs.append(
                {
                    "event_id": event["event_id"],
                    "status": "CASH",
                    "eval_date": current_eval_date.strftime("%Y-%m-%d"),
                    "effective_date": trade_date.strftime("%Y-%m-%d"),
                    "selected_count": 0,
                }
            )
            continue
        for row in selected.to_dict(orient="records"):
            schedule_rows.append(
                {
                    "event_id": event["event_id"],
                    "event_date": event_date.strftime("%Y-%m-%d"),
                    "event_type": event["event_type"],
                    "event_title": event["event_title"],
                    "eval_date": current_eval_date.strftime("%Y-%m-%d"),
                    "effective_date": trade_date.strftime("%Y-%m-%d"),
                    "ticker": row["Ticker"],
                    "rank": int(row["Rank"]),
                    "momentum_score": float(row["MomentumScore"]),
                    "mad_score": float(row["MadScore"]),
                    "event_weight": float(row["Weight"]),
                }
            )
        logs.append(
            {
                "event_id": event["event_id"],
                "status": "OK",
                "eval_date": current_eval_date.strftime("%Y-%m-%d"),
                "effective_date": trade_date.strftime("%Y-%m-%d"),
                "selected_count": int(len(selected)),
            }
        )
    return pd.DataFrame(schedule_rows), logs


def combine_event_targets(close: pd.DataFrame, schedule: pd.DataFrame) -> pd.DataFrame:
    if schedule.empty:
        raise ValueError("empty schedule")
    schedule = schedule.copy()
    schedule["effective_date"] = pd.to_datetime(schedule["effective_date"])
    all_tickers = sorted(schedule["ticker"].astype(str).unique())
    target = pd.DataFrame(0.0, index=close.index, columns=all_tickers)
    target["__cash__"] = 1.0

    for date in close.index:
        active = schedule[schedule["effective_date"] <= date].copy()
        if active.empty:
            continue
        event_last = schedule.groupby("event_id")["effective_date"].max().rename("last_effective_date")
        active = active.merge(event_last, left_on="event_id", right_index=True, how="left")
        active = active[active["last_effective_date"] > date].copy()
        if active.empty:
            continue
        latest = active.groupby("event_id")["effective_date"].max().rename("latest_date")
        active = active.merge(latest, left_on="event_id", right_index=True, how="left")
        active = active[active["effective_date"] == active["latest_date"]].copy()
        active["event_date_ts"] = pd.to_datetime(active["event_date"])
        active = active.sort_values(["event_date_ts", "rank"], ascending=[False, True]).reset_index(drop=True)
        active = active.head(MAX_CONCURRENT_POSITIONS).copy()
        if active.empty:
            continue
        active["event_count"] = active.groupby("event_id")["event_id"].transform("count")
        event_ids = active["event_id"].drop_duplicates().tolist()
        sleeve_weight = 1.0 / len(event_ids)
        active["portfolio_weight"] = sleeve_weight * active["event_weight"]

        row = pd.Series(0.0, index=target.columns)
        for rec in active.to_dict(orient="records"):
            row[str(rec["ticker"])] += float(rec["portfolio_weight"])
        cash_weight = max(0.0, 1.0 - float(row.drop(labels="__cash__").sum()))
        row["__cash__"] = cash_weight
        target.loc[date] = row

    return target


def build_daily_nav(close: pd.DataFrame, target: pd.DataFrame) -> pd.DataFrame:
    returns = close.pct_change().fillna(0.0)
    aligned_target = target.reindex(close.index).ffill().fillna(0.0)
    invested = aligned_target.drop(columns="__cash__", errors="ignore").sum(axis=1) > 1e-12
    if not invested.any():
        raise ValueError("portfolio never becomes invested")
    first_active_date = pd.Timestamp(invested[invested].index[0])
    aligned_target = aligned_target.loc[first_active_date:].copy()
    returns = returns.loc[first_active_date:].copy()
    shifted_weights = aligned_target.shift(1).fillna(0.0)
    shifted_weights["__cash__"] = shifted_weights.get("__cash__", 0.0)
    daily_return = (shifted_weights.drop(columns="__cash__", errors="ignore") * returns[shifted_weights.drop(columns="__cash__", errors="ignore").columns]).sum(axis=1)
    nav = (1.0 + daily_return).cumprod()
    out = pd.DataFrame({"date": aligned_target.index, "daily_return": daily_return.values, "nav": nav.values})
    return out


def compute_trade_log(target: pd.DataFrame, close: pd.DataFrame) -> pd.DataFrame:
    ticker_cols = [c for c in target.columns if c != "__cash__"]
    rows = []
    prev = pd.Series(0.0, index=ticker_cols)
    for date in target.index:
        curr = target.loc[date, ticker_cols]
        delta = curr - prev
        changed = delta[delta.abs() > 1e-12]
        for ticker, val in changed.items():
            rows.append(
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "ticker": ticker,
                    "action": "BUY" if val > 0 else "SELL",
                    "weight_delta": float(val),
                    "price": float(close.loc[date, ticker]),
                }
            )
        prev = curr.copy()
    return pd.DataFrame(rows)


def summarize_results(nav_df: pd.DataFrame, trade_log: pd.DataFrame, schedule: pd.DataFrame) -> dict:
    years = max((pd.Timestamp(nav_df["date"].iloc[-1]) - pd.Timestamp(nav_df["date"].iloc[0])).days / 365.25, 1e-9)
    final_nav = float(nav_df["nav"].iloc[-1])
    cagr = final_nav ** (1 / years) - 1.0
    hwm = nav_df["nav"].cummax()
    mdd = float((nav_df["nav"] / hwm - 1.0).min())
    vol = float(nav_df["daily_return"].std(ddof=0) * math.sqrt(252))
    sharpe = float((nav_df["daily_return"].mean() / (nav_df["daily_return"].std(ddof=0) + 1e-12)) * math.sqrt(252))
    event_count = int(schedule["event_id"].nunique()) if not schedule.empty else 0
    trade_count = int(len(trade_log))
    event_summary = schedule.groupby("event_id").agg(
        first_effective_date=("effective_date", "min"),
        last_effective_date=("effective_date", "max"),
        avg_selected=("ticker", "count"),
    ).reset_index() if not schedule.empty else pd.DataFrame(columns=["event_id", "first_effective_date", "last_effective_date", "avg_selected"])

    return {
        "event_count": event_count,
        "trade_count": trade_count,
        "cagr": float(cagr),
        "max_drawdown": mdd,
        "annualized_volatility": vol,
        "sharpe": sharpe,
        "final_nav": final_nav,
        "start_date": str(pd.Timestamp(nav_df["date"].iloc[0]).date()),
        "end_date": str(pd.Timestamp(nav_df["date"].iloc[-1]).date()),
        "event_summary_rows": int(len(event_summary)),
    }


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    events, baskets = load_inputs(args.event_path, args.basket_path)
    events = events.copy()
    events["event_type"] = events["event_type"].astype(str)
    if not set(events["event_type"]).issubset(ALLOWED_EVENT_TYPES):
        bad = sorted(set(events["event_type"]) - ALLOWED_EVENT_TYPES)
        raise SystemExit(f"unsupported event types: {bad}")

    required_mapping_cols = [
        "transmission_var_1",
        "transmission_reason_1",
    ]
    for col in required_mapping_cols:
        if events[col].astype(str).str.strip().eq("").any():
            raise SystemExit(f"missing required transmission mapping column values: {col}")

    tickers = sorted(baskets["ticker"].astype(str).unique().tolist())
    close = load_close_matrix(tickers)

    schedule_frames = []
    event_logs = []
    for _, event in events.iterrows():
        basket = baskets[baskets["event_id"] == event["event_id"]].copy()
        schedule, logs = build_event_schedule(event, close, basket)
        schedule_frames.append(schedule)
        event_logs.extend(logs)

    schedule_all = pd.concat(schedule_frames, ignore_index=True) if schedule_frames else pd.DataFrame()
    if schedule_all.empty:
        raise SystemExit("no valid event schedules generated")

    target = combine_event_targets(close, schedule_all)
    nav_df = build_daily_nav(close[target.drop(columns="__cash__").columns], target)
    trade_log = compute_trade_log(target, close[target.drop(columns="__cash__").columns])
    summary = summarize_results(nav_df, trade_log, schedule_all)

    event_status = pd.DataFrame(event_logs)
    event_summary = (
        schedule_all.groupby(["event_id", "event_title", "event_type"])
        .agg(
            first_eval_date=("eval_date", "min"),
            last_eval_date=("eval_date", "max"),
            first_trade_date=("effective_date", "min"),
            last_trade_date=("effective_date", "max"),
            rebalance_rows=("ticker", "count"),
            unique_names=("ticker", "nunique"),
        )
        .reset_index()
    )

    nav_df.to_csv(output_dir / "daily_nav.csv", index=False, encoding="utf-8-sig")
    trade_log.to_csv(output_dir / "trade_log.csv", index=False, encoding="utf-8-sig")
    schedule_all.to_csv(output_dir / "schedule.csv", index=False, encoding="utf-8-sig")
    event_status.to_csv(output_dir / "event_status.csv", index=False, encoding="utf-8-sig")
    event_summary.to_csv(output_dir / "event_summary.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame([summary]).to_csv(output_dir / "run_summary.csv", index=False, encoding="utf-8-sig")
    (output_dir / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(pd.DataFrame([summary]).to_string(index=False))


if __name__ == "__main__":
    main()
