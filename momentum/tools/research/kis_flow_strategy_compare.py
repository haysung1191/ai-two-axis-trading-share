import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


import argparse
import math
import os
from typing import Dict, List

import numpy as np
import pandas as pd

from kis_backtest_from_prices import (
    StrategyConfig,
    build_market_matrices,
    compute_point_in_time_universe,
    rebalance_dates,
    run_one,
)
from kis_flow_data import build_flow_matrices


def zscore_row(df: pd.DataFrame) -> pd.DataFrame:
    mean = df.mean(axis=1)
    std = df.std(axis=1, ddof=0).replace(0.0, np.nan)
    return df.sub(mean, axis=0).div(std, axis=0)


def summarize_output(out: pd.DataFrame) -> Dict[str, float]:
    if out.empty:
        return {
            "FinalNAV": 1.0,
            "CAGR": 0.0,
            "MDD": 0.0,
            "Sharpe": 0.0,
        }
    years = max((out.index[-1] - out.index[0]).days / 365.25, 1e-9)
    nav = (1.0 + out["daily_return"].astype(float).fillna(0.0)).cumprod()
    hwm = nav.cummax()
    return {
        "FinalNAV": float(nav.iloc[-1]),
        "CAGR": float(nav.iloc[-1] ** (1 / years) - 1),
        "MDD": float((nav / hwm - 1).min()),
        "Sharpe": float((out["daily_return"].mean() / (out["daily_return"].std(ddof=0) + 1e-12)) * math.sqrt(252)),
    }


def compute_flow_score(
    close_s: pd.DataFrame,
    value_s: pd.DataFrame,
    flow_mats: Dict[str, pd.DataFrame],
    foreign_ratio_cap: float = 40.0,
    foreign_ratio_penalty: float = 0.50,
) -> pd.DataFrame:
    foreign = flow_mats.get("foreign_net_volume", pd.DataFrame(index=close_s.index, columns=close_s.columns))
    foreign = foreign.reindex(index=close_s.index, columns=close_s.columns).fillna(0.0)
    inst = flow_mats.get("institution_net_volume", pd.DataFrame(index=close_s.index, columns=close_s.columns))
    inst = inst.reindex(index=close_s.index, columns=close_s.columns).fillna(0.0)
    foreign_ratio = flow_mats.get("foreign_ratio", pd.DataFrame(index=close_s.index, columns=close_s.columns))
    foreign_ratio = foreign_ratio.reindex(index=close_s.index, columns=close_s.columns)

    traded_value_20 = value_s.rolling(20, min_periods=20).sum().replace(0.0, np.nan)
    traded_value_60 = value_s.rolling(60, min_periods=60).sum().replace(0.0, np.nan)

    foreign_20 = (foreign * close_s).rolling(20, min_periods=20).sum() / traded_value_20
    foreign_60 = (foreign * close_s).rolling(60, min_periods=60).sum() / traded_value_60
    inst_20 = (inst * close_s).rolling(20, min_periods=20).sum() / traded_value_20
    crowd_penalty = zscore_row(foreign_ratio.where(foreign_ratio >= foreign_ratio_cap))

    score = zscore_row(foreign_20) + 0.75 * zscore_row(foreign_60) + 0.20 * zscore_row(inst_20)
    if foreign_ratio_penalty > 0:
        score = score - foreign_ratio_penalty * crowd_penalty.fillna(0.0)
    return score.replace([np.inf, -np.inf], np.nan)


def run_flow_strategy(
    close_s: pd.DataFrame,
    value_s: pd.DataFrame,
    flow_mats: Dict[str, pd.DataFrame],
    stg: StrategyConfig,
    min_common_dates: int,
    hold_buffer: int = 10,
    trend_ma: int = 60,
    foreign_ratio_cap: float = 40.0,
    foreign_ratio_penalty: float = 0.50,
) -> tuple[pd.DataFrame, Dict[str, float]]:
    dates = sorted(close_s.index)
    if len(dates) < min_common_dates:
        raise RuntimeError(f"Not enough common dates. Need at least {min_common_dates}.")
    dates = pd.DatetimeIndex(dates)
    cs = close_s.loc[dates]
    vs = value_s.loc[dates, cs.columns]
    rs = cs.pct_change(fill_method=None).fillna(0.0)

    flow_score = compute_flow_score(
        cs,
        vs,
        flow_mats,
        foreign_ratio_cap=foreign_ratio_cap,
        foreign_ratio_penalty=foreign_ratio_penalty,
    ).reindex(index=dates, columns=cs.columns)
    universe_s = compute_point_in_time_universe(cs, vs, "stock", stg)
    reb = set(rebalance_dates(dates, stg.rebalance))
    stock_trend_ok = (cs > cs.rolling(trend_ma, min_periods=trend_ma).mean()).fillna(False)

    market_proxy = cs.mean(axis=1)
    market_ma = market_proxy.rolling(stg.regime_ma_window, min_periods=stg.regime_ma_window).mean()
    market_slope = market_ma - market_ma.shift(stg.regime_slope_window)
    breadth = (cs > cs.rolling(stg.regime_ma_window, min_periods=stg.regime_ma_window).mean()).mean(axis=1)
    risk_on = ((market_proxy > market_ma) & (market_slope > 0) & (breadth >= stg.regime_breadth_threshold)).fillna(True)

    w_now: Dict[str, float] = {}
    hold_list: List[str] = []
    rows: List[Dict[str, float]] = []
    turns: List[float] = []
    holdings_count: List[int] = []

    for i in range(1, len(dates)):
        prev_dt, dt = dates[i - 1], dates[i]
        if prev_dt in reb:
            eligible = universe_s.loc[prev_dt].fillna(False) & stock_trend_ok.loc[prev_dt].fillna(False)
            score = flow_score.loc[prev_dt].where(eligible, np.nan).dropna()
            rank_limit = max(1, int(stg.score_top_k))
            buffer_limit = rank_limit + max(0, int(hold_buffer))
            ranked = score.sort_values(ascending=False)
            entry = list(ranked.head(rank_limit).index)
            survivors = [ticker for ticker in hold_list if ticker in set(ranked.head(buffer_limit).index)]
            picks = ranked.loc[list(dict.fromkeys(entry + survivors))]
            if stg.use_regime_filter and not bool(risk_on.get(prev_dt, True)):
                target = {}
            elif picks.empty:
                target = {}
            else:
                equal_w = 1.0 / len(picks)
                target = {ticker: float(min(equal_w, stg.max_weight)) for ticker in picks.index}
                total = sum(target.values())
                if total > 0:
                    target = {k: v / total for k, v in target.items()}
            uni = set(w_now) | set(target)
            turns.append(sum(abs(target.get(k, 0.0) - w_now.get(k, 0.0)) for k in uni))
            w_now = target
            hold_list = list(target.keys())

        day = 0.0
        for ticker, weight in w_now.items():
            r = rs.at[dt, ticker] if ticker in rs.columns else 0.0
            if pd.isna(r):
                r = 0.0
            day += weight * float(r)
        if turns and prev_dt in reb:
            day -= turns[-1] * stg.fee_rate
        rows.append({"date": dt, "daily_return": day})
        holdings_count.append(len(w_now))

    out = pd.DataFrame(rows).set_index("date")
    out["nav"] = (1.0 + out["daily_return"]).cumprod()
    years = max((out.index[-1] - out.index[0]).days / 365.25, 1e-9)
    metrics = {
        **summarize_output(out),
        "AnnualTurnover": float(np.sum(turns) / years) if turns else 0.0,
        "AvgTurnover": float(np.mean(turns)) if turns else 0.0,
        "AvgHoldings": float(np.mean(holdings_count)) if holdings_count else 0.0,
    }
    return out, metrics


def main() -> None:
    p = argparse.ArgumentParser(description="Compare stock-first foreign-flow MVP against RegimeState baseline.")
    p.add_argument("--price-base", type=str, default="data/prices_operating_institutional_v1")
    p.add_argument("--flow-base", type=str, default="data/flows")
    p.add_argument("--save-path", type=str, default="tmp_flow/kis_flow_strategy_compare.csv")
    p.add_argument("--min-common-dates", type=int, default=180)
    p.add_argument("--top-n", type=int, default=20)
    p.add_argument("--fee-bps", type=float, default=8.0)
    p.add_argument("--max-files", type=int, default=0)
    p.add_argument("--flow-hold-buffer", type=int, default=10)
    p.add_argument("--flow-trend-ma", type=int, default=60)
    p.add_argument("--flow-foreign-ratio-cap", type=float, default=40.0)
    p.add_argument("--flow-foreign-ratio-penalty", type=float, default=0.50)
    p.add_argument("--flow-use-regime-filter", type=int, default=1)
    args = p.parse_args()

    close_s, value_s = build_market_matrices(args.price_base, "stock", args.max_files)
    close_e, value_e = build_market_matrices(args.price_base, "etf", args.max_files)
    flow_mats = build_flow_matrices(args.flow_base, market="stock", max_files=args.max_files)
    if flow_mats["foreign_net_volume"].empty:
        raise RuntimeError(f"No flow data found under {args.flow_base}")

    flow_start = flow_mats["foreign_net_volume"].dropna(how="all").index.min()
    if pd.isna(flow_start):
        raise RuntimeError(f"No usable foreign-flow history under {args.flow_base}")
    coverage_start = pd.Timestamp(flow_start) + pd.Timedelta(days=90)

    fee = args.fee_bps / 10000.0
    flow_stg = StrategyConfig(
        name="Weekly ForeignFlow MVP",
        rebalance="W-FRI",
        top_n_stock=args.top_n,
        top_n_etf=args.top_n,
        fee_rate=fee,
        use_regime_filter=bool(args.flow_use_regime_filter),
        regime_ma_window=200,
        regime_slope_window=20,
        regime_breadth_threshold=0.55,
        trend_exit_ma=0,
        stop_loss_pct=0.0,
        vol_lookback=20,
        target_vol_annual=0.0,
        max_weight=0.10,
        min_gross_exposure=0.0,
        score_top_k=args.top_n,
    )
    baseline_stg = StrategyConfig(
        name="Weekly Score50 RegimeState",
        rebalance="W-FRI",
        top_n_stock=args.top_n,
        top_n_etf=args.top_n,
        fee_rate=fee,
        use_regime_filter=True,
        use_regime_state_model=True,
        stop_loss_pct=0.12,
        trend_exit_ma=60,
        regime_ma_window=200,
        regime_slope_window=20,
        regime_breadth_threshold=0.55,
        vol_lookback=20,
        target_vol_annual=0.20,
        max_weight=0.20,
        min_gross_exposure=0.50,
        selection_mode="score",
        score_top_k=50,
        score_power=1.5,
        regime_off_exposure=0.40,
    )

    flow_out, flow_metrics = run_flow_strategy(
        close_s,
        value_s,
        flow_mats,
        flow_stg,
        args.min_common_dates,
        hold_buffer=args.flow_hold_buffer,
        trend_ma=args.flow_trend_ma,
        foreign_ratio_cap=args.flow_foreign_ratio_cap,
        foreign_ratio_penalty=args.flow_foreign_ratio_penalty,
    )
    base_out, base_metrics = run_one(
        close_s,
        close_e,
        baseline_stg,
        min_common_dates=args.min_common_dates,
        traded_value_s=value_s,
        traded_value_e=value_e,
    )
    flow_eval = flow_out.loc[flow_out.index >= coverage_start].copy()
    base_eval = base_out.loc[base_out.index >= coverage_start].copy()
    flow_metrics.update(summarize_output(flow_eval))
    base_metrics.update(summarize_output(base_eval))

    summary = pd.DataFrame(
        [
            {"Strategy": "Weekly ForeignFlow MVP", "CoverageStart": coverage_start.date(), **flow_metrics},
            {"Strategy": "Weekly Score50 RegimeState", "CoverageStart": coverage_start.date(), **base_metrics},
        ]
    )
    parent = os.path.dirname(args.save_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    summary.to_csv(args.save_path, index=False, encoding="utf-8-sig")
    print(summary.to_string(index=False))
    print(f"saved {args.save_path}")


if __name__ == "__main__":
    main()
