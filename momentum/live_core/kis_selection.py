from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from kis_backtest_from_prices import StrategyConfig


OVERHEAT_NORMAL = "정상"
OVERHEAT_CAUTION = "주의"
OVERHEAT_OVERHEATED = "과열"


def add_scores(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    pos_count = (out[["r1", "r3", "r6", "r12"]] > 0).sum(axis=1)
    s1 = pos_count * 10.0
    s2 = ((out["avg_mom"].clip(-20, 80) + 20) / 100.0) * 25.0
    s3 = (20.0 - (out["mrat"] - 1.35).abs() * 25.0).clip(0, 20)
    s4 = (15.0 - (out["mad_gap"] - 20).abs() * 0.25).clip(0, 15)
    out["buy_score"] = s1 + s2 + s3 + s4
    out["overheat"] = OVERHEAT_NORMAL
    out.loc[(out["mad_gap"] >= 60) | (out["mrat"] >= 1.9), "overheat"] = OVERHEAT_CAUTION
    out.loc[(out["mad_gap"] >= 100) | (out["mrat"] >= 2.3) | (out["r1"] >= 45), "overheat"] = OVERHEAT_OVERHEATED
    return out


def features(close: pd.DataFrame, stg: StrategyConfig | None = None) -> dict[str, pd.DataFrame]:
    osc_lookback = max(5, int(stg.osc_lookback)) if stg is not None else 20
    osc_band_sigma = float(stg.osc_band_sigma) if stg is not None else 1.5
    osc_band_break_sigma = float(stg.osc_band_break_sigma) if stg is not None else 2.0
    r1 = (close / close.shift(20) - 1) * 100
    r3 = (close / close.shift(60) - 1) * 100
    r6 = (close / close.shift(120) - 1) * 100
    r12 = (close / close.shift(240) - 1) * 100
    avg_mom = (r1 + r3 + r6 + r12) / 4
    ma21 = close.rolling(21, min_periods=21).mean()
    ma60 = close.rolling(60, min_periods=60).mean()
    ma200 = close.rolling(200, min_periods=200).mean()
    mrat = ma21 / ma200
    mad_gap = (ma21 - ma200) / ma200 * 100
    osc_mean = close.rolling(osc_lookback, min_periods=osc_lookback).mean()
    osc_std = close.rolling(osc_lookback, min_periods=osc_lookback).std(ddof=0).replace(0.0, np.nan)
    osc_z = (close - osc_mean) / osc_std
    osc_recovery = (close > close.shift(1)).astype(float)
    osc_lower_band = osc_mean - osc_band_sigma * osc_std
    osc_break = close < (osc_mean - osc_band_break_sigma * osc_std)
    osc_break_persist = osc_break.rolling(2, min_periods=1).sum()
    return {
        "r1": r1,
        "r3": r3,
        "r6": r6,
        "r12": r12,
        "avg_mom": avg_mom,
        "mrat": mrat,
        "mad_gap": mad_gap,
        "ma60": ma60,
        "osc_mean": osc_mean,
        "osc_std": osc_std,
        "osc_z": osc_z,
        "osc_recovery": osc_recovery,
        "osc_lower_band": osc_lower_band,
        "osc_break": osc_break.astype(float),
        "osc_break_persist": osc_break_persist,
    }


def feature_frame_at(feat: dict[str, pd.DataFrame], dt: pd.Timestamp) -> pd.DataFrame:
    df = pd.DataFrame({k: v.loc[dt] for k, v in feat.items()}).dropna()
    if df.empty:
        return df
    df = df[np.isfinite(df).all(axis=1)]
    if df.empty:
        return df
    return add_scores(df)


def oscillation_candidates_at(
    feat: dict[str, pd.DataFrame],
    dt: pd.Timestamp,
    stg: StrategyConfig,
    eligible_mask: pd.DataFrame | None = None,
) -> pd.DataFrame:
    df = feature_frame_at(feat, dt)
    if df.empty:
        return df
    if eligible_mask is not None and dt in eligible_mask.index:
        eligible = eligible_mask.loc[dt].fillna(False)
        df = df.loc[df.index.intersection(eligible[eligible].index)]
        if df.empty:
            return df
    cond = (
        (df["osc_z"] <= stg.osc_z_entry)
        & (df["r1"] < 0)
        & (df["osc_recovery"] > 0)
        & (df["osc_break"] <= 0)
        & (df["osc_break_persist"] < 2)
        & (df["mad_gap"] <= stg.mad_t2)
        & (df["overheat"] != OVERHEAT_OVERHEATED)
    )
    out = df.loc[cond].copy()
    if out.empty:
        return out
    out["osc_priority"] = (-out["osc_z"]).clip(lower=0.0) + ((-out["r1"]).clip(lower=0.0) / 100.0)
    return out.sort_values(["osc_priority", "buy_score", "avg_mom"], ascending=[False, False, False])


def select_buffer(ranked: list[str], prev: list[str], top_n: int, use_buffer: bool, entry_rank: int, exit_rank: int) -> list[str]:
    if not ranked:
        return []
    if not use_buffer:
        return ranked[:top_n]
    rmap = {t: i + 1 for i, t in enumerate(ranked)}
    kept = [t for t in prev if t in rmap and rmap[t] <= exit_rank]
    out = list(kept)
    for t in ranked:
        if rmap[t] <= entry_rank and t not in out:
            out.append(t)
        if len(out) >= top_n:
            break
    return out[:top_n]


def rank_at(feat: dict[str, pd.DataFrame], dt: pd.Timestamp, eligible_mask: pd.DataFrame | None = None) -> pd.DataFrame:
    df = feature_frame_at(feat, dt)
    if df.empty:
        return df
    if eligible_mask is not None and dt in eligible_mask.index:
        eligible = eligible_mask.loc[dt].fillna(False)
        df = df.loc[df.index.intersection(eligible[eligible].index)]
        if df.empty:
            return df
    df = df[df["overheat"] != OVERHEAT_OVERHEATED]
    return df.sort_values(["buy_score", "avg_mom"], ascending=[False, False])
