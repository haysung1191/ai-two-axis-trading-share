import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import argparse
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from pykrx import stock as pykrx_stock


LOOKBACKS = [20, 60, 120, 240]
MA_SHORT = 21
MA_LONG = 200


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


def safe_get_close_snapshot(date_str: str, market: str = "ALL") -> pd.Series:
    df = pykrx_stock.get_market_ohlcv_by_ticker(date_str, market=market)
    if df is None or df.empty or "종가" not in df.columns:
        return pd.Series(dtype=float)
    close = pd.to_numeric(df["종가"], errors="coerce")
    close.index = close.index.astype(str).str.zfill(6)
    return close


def safe_get_etf_close_snapshot(date_str: str) -> pd.Series:
    df = pykrx_stock.get_etf_ohlcv_by_ticker(date_str)
    if df is None or df.empty or "종가" not in df.columns:
        return pd.Series(dtype=float)
    close = pd.to_numeric(df["종가"], errors="coerce")
    close.index = close.index.astype(str).str.zfill(6)
    return close


def get_trading_dates(start: str, end: str) -> List[pd.Timestamp]:
    dts = pd.date_range(start=start, end=end, freq="B")
    out: List[pd.Timestamp] = []
    for dt in dts:
        date_str = dt.strftime("%Y%m%d")
        snapshot = safe_get_close_snapshot(date_str)
        if not snapshot.empty:
            out.append(dt)
    return out


def build_close_matrix(dates: Sequence[pd.Timestamp], mode: str) -> pd.DataFrame:
    rows = []
    for dt in dates:
        date_str = dt.strftime("%Y%m%d")
        if mode == "stock":
            snap = safe_get_close_snapshot(date_str)
            if not snap.empty:
                snap = snap[snap > 0]
                snap.index = ["S_" + x for x in snap.index]
        else:
            snap = safe_get_etf_close_snapshot(date_str)
            if not snap.empty:
                snap = snap[snap > 0]
                snap.index = ["E_" + x for x in snap.index]
        rows.append(pd.DataFrame({"date": dt, "ticker": snap.index, "close": snap.values}))

    long_df = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["date", "ticker", "close"])
    if long_df.empty:
        return pd.DataFrame(index=pd.DatetimeIndex([]))
    close = long_df.pivot(index="date", columns="ticker", values="close").sort_index()
    return close


def compute_features(close: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    ret_1m = close / close.shift(LOOKBACKS[0]) - 1.0
    ret_3m = close / close.shift(LOOKBACKS[1]) - 1.0
    ret_6m = close / close.shift(LOOKBACKS[2]) - 1.0
    ret_12m = close / close.shift(LOOKBACKS[3]) - 1.0
    avg_mom = (ret_1m + ret_3m + ret_6m + ret_12m) / 4.0
    ma21 = close.rolling(MA_SHORT, min_periods=MA_SHORT).mean()
    ma200 = close.rolling(MA_LONG, min_periods=MA_LONG).mean()
    mrat = ma21 / ma200
    mad_gap = (ma21 - ma200) / ma200 * 100.0

    return {
        "ret_1m": ret_1m * 100.0,
        "ret_3m": ret_3m * 100.0,
        "ret_6m": ret_6m * 100.0,
        "ret_12m": ret_12m * 100.0,
        "avg_mom": avg_mom * 100.0,
        "mrat": mrat,
        "mad_gap": mad_gap,
    }


def compute_buy_score(frame: pd.DataFrame) -> pd.Series:
    mom_cols = ["ret_1m", "ret_3m", "ret_6m", "ret_12m"]
    pos_count = (frame[mom_cols] > 0).sum(axis=1)
    score_consistency = pos_count * 10.0
    score_avg_mom = ((frame["avg_mom"].clip(-20, 80) + 20) / 100.0) * 25.0
    score_mrat = (20.0 - (frame["mrat"] - 1.35).abs() * 25.0).clip(0, 20)
    score_mad = (15.0 - (frame["mad_gap"] - 20).abs() * 0.25).clip(0, 15)
    return (score_consistency + score_avg_mom + score_mrat + score_mad).round(4)


def add_overheat(frame: pd.DataFrame) -> pd.Series:
    overheat = pd.Series("정상", index=frame.index)
    overheat[(frame["mad_gap"] >= 60) | (frame["mrat"] >= 1.9)] = "주의"
    overheat[(frame["mad_gap"] >= 100) | (frame["mrat"] >= 2.3) | (frame["ret_1m"] >= 45)] = "과열"
    return overheat


def rank_universe_at_date(feat: Dict[str, pd.DataFrame], dt: pd.Timestamp) -> pd.DataFrame:
    raw = pd.DataFrame(
        {
            "ret_1m": feat["ret_1m"].loc[dt],
            "ret_3m": feat["ret_3m"].loc[dt],
            "ret_6m": feat["ret_6m"].loc[dt],
            "ret_12m": feat["ret_12m"].loc[dt],
            "avg_mom": feat["avg_mom"].loc[dt],
            "mrat": feat["mrat"].loc[dt],
            "mad_gap": feat["mad_gap"].loc[dt],
        }
    ).dropna()

    if raw.empty:
        return raw

    raw = raw[np.isfinite(raw).all(axis=1)]
    raw = raw[(raw["mrat"] > 0) & (raw["avg_mom"].notna())]
    if raw.empty:
        return raw

    raw["buy_score"] = compute_buy_score(raw)
    raw["overheat"] = add_overheat(raw)
    raw = raw.sort_values(["buy_score", "avg_mom"], ascending=[False, False])
    raw["rank"] = np.arange(1, len(raw) + 1)
    return raw


def rebalance_dates(all_dates: Sequence[pd.Timestamp], rule: str) -> List[pd.Timestamp]:
    idx = pd.DatetimeIndex(all_dates)
    if rule == "D":
        return list(idx)
    if rule == "W-FRI":
        mask = idx.weekday == 4
        weekly = idx[mask]
        if len(weekly) == 0 or weekly[-1] != idx[-1]:
            weekly = weekly.append(pd.DatetimeIndex([idx[-1]]))
        return list(weekly)
    raise ValueError(f"Unsupported rebalance rule: {rule}")


def select_holdings(
    ranked: pd.DataFrame,
    prev: List[str],
    top_n: int,
    use_buffer: bool,
    entry_rank: int,
    exit_rank: int,
) -> List[str]:
    if ranked.empty or top_n <= 0:
        return []

    if not use_buffer:
        return list(ranked.head(top_n).index)

    rank_map = ranked["rank"].to_dict()
    kept = [t for t in prev if t in rank_map and rank_map[t] <= exit_rank]
    selected = list(kept)
    for ticker in ranked.index:
        if rank_map[ticker] <= entry_rank and ticker not in selected:
            selected.append(ticker)
        if len(selected) >= top_n:
            break
    return selected[:top_n]


def annualized_return(nav: pd.Series) -> float:
    if nav.empty:
        return 0.0
    years = max((nav.index[-1] - nav.index[0]).days / 365.25, 1e-9)
    return float((nav.iloc[-1] / nav.iloc[0]) ** (1 / years) - 1)


def max_drawdown(nav: pd.Series) -> float:
    if nav.empty:
        return 0.0
    hwm = nav.cummax()
    dd = nav / hwm - 1.0
    return float(dd.min())


def sharpe_ratio(daily_ret: pd.Series) -> float:
    if daily_ret.empty:
        return 0.0
    mu = daily_ret.mean()
    sigma = daily_ret.std(ddof=0)
    if sigma == 0 or np.isnan(sigma):
        return 0.0
    return float((mu / sigma) * math.sqrt(252))


def run_backtest(
    close_stock: pd.DataFrame,
    close_etf: pd.DataFrame,
    config: StrategyConfig,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    dates = sorted(set(close_stock.index).intersection(set(close_etf.index)))
    if len(dates) < 260:
        raise RuntimeError("거래일 데이터가 부족합니다. 백테스트 기간을 늘려주세요.")
    dates = pd.DatetimeIndex(dates)

    feat_stock = compute_features(close_stock.loc[dates])
    feat_etf = compute_features(close_etf.loc[dates])

    ret_stock = close_stock.loc[dates].pct_change().fillna(0.0)
    ret_etf = close_etf.loc[dates].pct_change().fillna(0.0)

    reb_dates = set(rebalance_dates(dates, config.rebalance))

    current_w: Dict[str, float] = {}
    hold_stock: List[str] = []
    hold_etf: List[str] = []
    turnover_list: List[float] = []
    out_rows = []

    for i in range(1, len(dates)):
        prev_dt = dates[i - 1]
        dt = dates[i]

        if prev_dt in reb_dates:
            ranked_stock = rank_universe_at_date(feat_stock, prev_dt)
            ranked_etf = rank_universe_at_date(feat_etf, prev_dt)
            ranked_stock = ranked_stock[ranked_stock["overheat"] != "과열"]
            ranked_etf = ranked_etf[ranked_etf["overheat"] != "과열"]

            hold_stock = select_holdings(
                ranked_stock,
                hold_stock,
                config.top_n_stock,
                config.use_buffer,
                config.entry_rank,
                config.exit_rank,
            )
            hold_etf = select_holdings(
                ranked_etf,
                hold_etf,
                config.top_n_etf,
                config.use_buffer,
                config.entry_rank,
                config.exit_rank,
            )

            target_w: Dict[str, float] = {}
            if hold_stock:
                w_s = 0.5 / len(hold_stock)
                target_w.update({t: w_s for t in hold_stock})
            if hold_etf:
                w_e = 0.5 / len(hold_etf)
                target_w.update({t: w_e for t in hold_etf})

            # If one side is empty, re-normalize to 100%.
            if target_w:
                s = sum(target_w.values())
                target_w = {k: v / s for k, v in target_w.items()}

            universe = set(current_w) | set(target_w)
            turnover = sum(abs(target_w.get(k, 0.0) - current_w.get(k, 0.0)) for k in universe)
            turnover_list.append(turnover)
            current_w = target_w
            fee = turnover * config.fee_rate
        else:
            fee = 0.0

        if current_w:
            day_ret = 0.0
            for ticker, w in current_w.items():
                if ticker.startswith("S_"):
                    r = ret_stock.at[dt, ticker] if ticker in ret_stock.columns else 0.0
                else:
                    r = ret_etf.at[dt, ticker] if ticker in ret_etf.columns else 0.0
                if pd.isna(r):
                    r = 0.0
                day_ret += w * float(r)
            day_ret -= fee
        else:
            day_ret = 0.0

        out_rows.append(
            {
                "date": dt,
                "daily_return": day_ret,
                "n_stock": len(hold_stock),
                "n_etf": len(hold_etf),
            }
        )

    result = pd.DataFrame(out_rows).set_index("date")
    result["nav"] = (1.0 + result["daily_return"]).cumprod()

    avg_turnover = float(np.mean(turnover_list)) if turnover_list else 0.0
    metrics = {
        "CAGR": annualized_return(result["nav"]),
        "MDD": max_drawdown(result["nav"]),
        "Sharpe": sharpe_ratio(result["daily_return"]),
        "AvgTurnover": avg_turnover,
        "FinalNAV": float(result["nav"].iloc[-1]),
    }
    return result, metrics


def print_summary(summary: pd.DataFrame) -> None:
    view = summary.copy()
    for col in ["CAGR", "MDD", "Sharpe", "AvgTurnover", "FinalNAV"]:
        if col not in view.columns:
            continue
        if col in {"CAGR", "MDD", "AvgTurnover"}:
            view[col] = (view[col] * 100).map(lambda x: f"{x:,.2f}%")
        elif col in {"Sharpe", "FinalNAV"}:
            view[col] = view[col].map(lambda x: f"{x:,.3f}")
    print("\n=== Strategy Comparison ===")
    print(view.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Momentum rotation backtest (ETF + stocks).")
    parser.add_argument("--start", type=str, default="2024-01-01")
    parser.add_argument("--end", type=str, default=datetime_to_str(pd.Timestamp.today()))
    parser.add_argument("--top-n", type=int, default=20, help="Top N for each universe (stock/ETF).")
    parser.add_argument("--fee-bps", type=float, default=8.0, help="Rebalance fee in bps per turnover.")
    parser.add_argument("--save-prefix", type=str, default="backtest_result")
    args = parser.parse_args()

    fee = args.fee_bps / 10000.0
    print(f"Loading trading dates: {args.start} ~ {args.end}")
    dates = get_trading_dates(args.start, args.end)
    if len(dates) < 260:
        raise RuntimeError("거래일이 260일 미만입니다. 기간을 늘려주세요.")

    print("Building stock close matrix...")
    close_stock = build_close_matrix(dates, mode="stock")
    print("Building ETF close matrix...")
    close_etf = build_close_matrix(dates, mode="etf")

    common_dates = sorted(set(close_stock.index).intersection(set(close_etf.index)))
    close_stock = close_stock.loc[common_dates]
    close_etf = close_etf.loc[common_dates]
    print(f"Usable dates: {len(common_dates)}, stock tickers: {close_stock.shape[1]}, etf tickers: {close_etf.shape[1]}")

    strategies = [
        StrategyConfig(
            name="Daily Top20",
            rebalance="D",
            top_n_stock=args.top_n,
            top_n_etf=args.top_n,
            fee_rate=fee,
            use_buffer=False,
        ),
        StrategyConfig(
            name="Weekly Top20",
            rebalance="W-FRI",
            top_n_stock=args.top_n,
            top_n_etf=args.top_n,
            fee_rate=fee,
            use_buffer=False,
        ),
        StrategyConfig(
            name="Weekly Buffer 20/25",
            rebalance="W-FRI",
            top_n_stock=args.top_n,
            top_n_etf=args.top_n,
            fee_rate=fee,
            use_buffer=True,
            entry_rank=20,
            exit_rank=25,
        ),
    ]

    summary_rows = []
    nav_df = pd.DataFrame(index=pd.DatetimeIndex(common_dates[1:]))

    for stg in strategies:
        print(f"Running: {stg.name}")
        result, metrics = run_backtest(close_stock, close_etf, stg)
        row = {"Strategy": stg.name}
        row.update(metrics)
        summary_rows.append(row)
        nav_df[stg.name] = result["nav"]

    summary = pd.DataFrame(summary_rows)
    print_summary(summary)

    summary_path = f"{args.save_prefix}_summary.csv"
    nav_path = f"{args.save_prefix}_nav.csv"
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")
    nav_df.to_csv(nav_path, encoding="utf-8-sig")
    print(f"\nSaved: {summary_path}")
    print(f"Saved: {nav_path}")


def datetime_to_str(ts: pd.Timestamp) -> str:
    return ts.strftime("%Y-%m-%d")


if __name__ == "__main__":
    main()

