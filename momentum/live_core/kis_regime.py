from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from kis_backtest_from_prices import StrategyConfig


def merge_rank_frames(primary: pd.DataFrame, preserved: list[str], additions: pd.DataFrame, limit: int) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    seen: set[str] = set()
    for subset in [
        primary.loc[[t for t in preserved if t in primary.index]] if preserved else primary.iloc[0:0],
        additions,
        primary,
    ]:
        if subset.empty:
            continue
        subset = subset.loc[[t for t in subset.index if t not in seen]]
        if subset.empty:
            continue
        frames.append(subset)
        seen.update(subset.index)
        if len(seen) >= max(0, int(limit)):
            break
    if not frames:
        return primary.iloc[0:0]
    return pd.concat(frames, axis=0).head(max(0, int(limit)))


def rotation_signal_from_ranks(rank_s: pd.DataFrame, rank_e: pd.DataFrame, stg: StrategyConfig) -> tuple[float, float, float]:
    if rank_s.empty or rank_e.empty:
        return 0.0, 0.5, 0.5
    top_k = max(1, int(stg.rotation_top_k))

    def _strength(df: pd.DataFrame) -> float:
        top = df.head(top_k)
        if top.empty:
            return 0.0
        score = float(top["buy_score"].astype(float).mean()) if "buy_score" in top.columns else 0.0
        mom = float(top["avg_mom"].astype(float).mean()) if "avg_mom" in top.columns else 0.0
        return score + 0.25 * mom

    stock_strength = _strength(rank_s)
    etf_strength = _strength(rank_e)
    denom = max(abs(stock_strength) + abs(etf_strength), 1e-9)
    raw_signal = float(np.clip((etf_strength - stock_strength) / denom, -1.0, 1.0))
    tilt = float(np.clip(stg.rotation_tilt_strength, 0.0, 0.45))
    min_sleeve = float(np.clip(stg.rotation_min_sleeve_weight, 0.0, 0.5))
    etf_target = float(np.clip(0.5 + tilt * raw_signal, min_sleeve, 1.0 - min_sleeve))
    stock_target = 1.0 - etf_target
    return raw_signal, stock_target, etf_target


def compute_regime_state(close_s: pd.DataFrame, stg: StrategyConfig) -> pd.DataFrame:
    market_proxy = close_s.mean(axis=1)
    market_ma = market_proxy.rolling(stg.regime_ma_window, min_periods=stg.regime_ma_window).mean()
    market_slope = market_ma - market_ma.shift(stg.regime_slope_window)
    slope_norm = (market_slope / market_ma.replace(0.0, np.nan)).replace([np.inf, -np.inf], np.nan)
    stock_ma = close_s.rolling(stg.regime_ma_window, min_periods=stg.regime_ma_window).mean()
    breadth = (close_s > stock_ma).mean(axis=1)
    dist_from_ma = ((market_proxy - market_ma) / market_ma.replace(0.0, np.nan)).replace([np.inf, -np.inf], np.nan)
    proxy_std = market_proxy.rolling(stg.osc_lookback, min_periods=stg.osc_lookback).std(ddof=0).replace(0.0, np.nan)
    proxy_z = ((market_proxy - market_ma) / proxy_std).replace([np.inf, -np.inf], np.nan)
    breakout_persist = (proxy_z.abs() >= 1.0).rolling(10, min_periods=5).mean()

    uptrend = (
        (market_proxy > market_ma)
        & (slope_norm > stg.range_slope_threshold)
        & (breadth >= stg.regime_breadth_threshold)
    )
    downtrend = (
        (market_proxy < market_ma)
        & (slope_norm < -stg.range_slope_threshold)
        & (breadth <= (1.0 - stg.regime_breadth_threshold))
    )
    breadth_mid_low = 0.5 - stg.range_breadth_tolerance
    breadth_mid_high = 0.5 + stg.range_breadth_tolerance
    range_regime = (
        (~uptrend)
        & (~downtrend)
        & (slope_norm.abs() <= stg.range_slope_threshold)
        & (dist_from_ma.abs() <= stg.range_dist_threshold)
        & (breakout_persist.fillna(0.0) <= stg.range_breakout_persistence_threshold)
        & breadth.between(breadth_mid_low, breadth_mid_high, inclusive="both")
    )

    labels = pd.Series("TRANSITION", index=close_s.index, dtype=object)
    labels.loc[uptrend.fillna(False)] = "UPTREND"
    labels.loc[downtrend.fillna(False)] = "DOWNTREND"
    labels.loc[range_regime.fillna(False)] = "RANGE"

    risk_on = labels.isin(["UPTREND", "RANGE"])
    if not stg.use_regime_state_model:
        legacy_risk_on = (market_proxy > market_ma) & (market_slope > 0) & (breadth >= stg.regime_breadth_threshold)
        legacy_risk_on = legacy_risk_on.fillna(True)
        if float(legacy_risk_on.mean()) < 0.10:
            legacy_risk_on = (market_proxy > market_ma).fillna(True)
        labels = pd.Series(np.where(legacy_risk_on, "UPTREND", "DOWNTREND"), index=close_s.index, dtype=object)
        risk_on = legacy_risk_on

    return pd.DataFrame(
        {
            "MarketProxy": market_proxy,
            "MarketMA": market_ma,
            "MarketSlope": market_slope,
            "SlopeNorm": slope_norm,
            "Breadth": breadth,
            "DistFromMA": dist_from_ma,
            "BreakoutPersistence": breakout_persist,
            "RiskOn": risk_on.fillna(True),
            "RegimeState": labels,
        }
    )
