from __future__ import annotations

import math
from typing import Dict, Mapping, Sequence, Tuple

import numpy as np
import pandas as pd


def compute_nav_metrics(nav_df: pd.DataFrame) -> tuple[float, float, float]:
    years = max((nav_df.index[-1] - nav_df.index[0]).days / 365.25, 1e-9)
    cagr = float(nav_df["nav"].iloc[-1] ** (1 / years) - 1)
    hwm = nav_df["nav"].cummax()
    mdd = float((nav_df["nav"] / hwm - 1).min())
    sharpe = float((nav_df["daily_return"].mean() / (nav_df["daily_return"].std(ddof=0) + 1e-12)) * math.sqrt(252))
    return cagr, mdd, sharpe


def summarize_backtest_metrics(
    out: pd.DataFrame,
    *,
    turns: Sequence[float],
    exposures: Sequence[float],
    holdings_count: Sequence[int],
    rebalance_dates_log: Sequence[pd.Timestamp],
    trade_buy_count: int,
    trade_sell_count: int,
    regime_state: pd.Series,
    osc_entry_count: int,
    osc_exit_count: int,
    osc_stop_count: int,
    rotation_signals: Sequence[float],
    stock_sleeves: Sequence[float],
    etf_sleeves: Sequence[float],
) -> Dict[str, float | int | str]:
    cagr, mdd, sharpe = compute_nav_metrics(out)
    years = max((out.index[-1] - out.index[0]).days / 365.25, 1e-9)
    avg_turn = float(np.mean(turns)) if turns else 0.0
    annual_turn = float(np.sum(turns) / years) if turns else 0.0
    avg_exp = float(np.mean(exposures)) if exposures else 0.0
    avg_holdings = float(np.mean(holdings_count)) if holdings_count else 0.0
    rebalance_count = int(len(rebalance_dates_log))
    first_reb = rebalance_dates_log[0] if rebalance_dates_log else pd.NaT
    last_reb = rebalance_dates_log[-1] if rebalance_dates_log else pd.NaT
    return {
        "FinalNAV": float(out["nav"].iloc[-1]),
        "CAGR": cagr,
        "MDD": mdd,
        "Sharpe": sharpe,
        "AvgTurnover": avg_turn,
        "AnnualTurnover": annual_turn,
        "AvgGrossExposure": avg_exp,
        "AvgHoldings": avg_holdings,
        "RebalanceCount": rebalance_count,
        "BuyTrades": int(trade_buy_count),
        "SellTrades": int(trade_sell_count),
        "RangeDaysPct": float((regime_state == "RANGE").mean()),
        "UptrendDaysPct": float((regime_state == "UPTREND").mean()),
        "DowntrendDaysPct": float((regime_state == "DOWNTREND").mean()),
        "TransitionDaysPct": float((regime_state == "TRANSITION").mean()),
        "OscEntryCount": int(osc_entry_count),
        "OscExitCount": int(osc_exit_count),
        "OscStopCount": int(osc_stop_count),
        "RotationSignalAvg": float(np.mean(rotation_signals)) if rotation_signals else 0.0,
        "AvgStockSleeve": float(np.mean(stock_sleeves)) if stock_sleeves else np.nan,
        "AvgEtfSleeve": float(np.mean(etf_sleeves)) if etf_sleeves else np.nan,
        "FirstRebalance": first_reb.strftime("%Y-%m-%d") if pd.notna(first_reb) else "",
        "LastRebalance": last_reb.strftime("%Y-%m-%d") if pd.notna(last_reb) else "",
    }


def blend_component_metrics(
    component_weights: Mapping[str, float],
    component_results: Mapping[str, Tuple[pd.DataFrame, Dict[str, float]]],
    out: pd.DataFrame,
) -> Dict[str, float | int | str]:
    cagr, mdd, sharpe = compute_nav_metrics(out)

    def weighted_metric(key: str, default: float = 0.0) -> float:
        total = 0.0
        for component_name, weight in component_weights.items():
            _, metrics = component_results[component_name]
            total += float(weight) * float(metrics.get(key, default))
        return float(total)

    first_rebalance_dates = []
    last_rebalance_dates = []
    for component_name in component_weights.keys():
        _, metrics = component_results[component_name]
        first_rebalance = str(metrics.get("FirstRebalance", "") or "").strip()
        last_rebalance = str(metrics.get("LastRebalance", "") or "").strip()
        if first_rebalance:
            first_rebalance_dates.append(first_rebalance)
        if last_rebalance:
            last_rebalance_dates.append(last_rebalance)

    return {
        "FinalNAV": float(out["nav"].iloc[-1]),
        "CAGR": cagr,
        "MDD": mdd,
        "Sharpe": sharpe,
        "AvgTurnover": weighted_metric("AvgTurnover"),
        "AnnualTurnover": weighted_metric("AnnualTurnover"),
        "AvgGrossExposure": weighted_metric("AvgGrossExposure"),
        "AvgHoldings": weighted_metric("AvgHoldings"),
        "RebalanceCount": int(round(weighted_metric("RebalanceCount"))),
        "BuyTrades": int(round(weighted_metric("BuyTrades"))),
        "SellTrades": int(round(weighted_metric("SellTrades"))),
        "RangeDaysPct": weighted_metric("RangeDaysPct"),
        "UptrendDaysPct": weighted_metric("UptrendDaysPct"),
        "DowntrendDaysPct": weighted_metric("DowntrendDaysPct"),
        "TransitionDaysPct": weighted_metric("TransitionDaysPct"),
        "OscEntryCount": int(round(weighted_metric("OscEntryCount"))),
        "OscExitCount": int(round(weighted_metric("OscExitCount"))),
        "OscStopCount": int(round(weighted_metric("OscStopCount"))),
        "RotationSignalAvg": weighted_metric("RotationSignalAvg"),
        "AvgStockSleeve": weighted_metric("AvgStockSleeve"),
        "AvgEtfSleeve": weighted_metric("AvgEtfSleeve"),
        "FirstRebalance": min(first_rebalance_dates) if first_rebalance_dates else "",
        "LastRebalance": max(last_rebalance_dates) if last_rebalance_dates else "",
    }
