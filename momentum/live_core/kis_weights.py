from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from kis_backtest_from_prices import StrategyConfig


def inverse_vol_weights(ret_window: pd.DataFrame, tickers: list[str]) -> dict[str, float]:
    if not tickers:
        return {}
    if ret_window.empty:
        w = 1.0 / len(tickers)
        return {t: w for t in tickers}

    vol = ret_window[tickers].std(ddof=0).replace(0, np.nan)
    inv = 1.0 / vol
    inv = inv.replace([np.inf, -np.inf], np.nan).dropna()
    if inv.empty:
        w = 1.0 / len(tickers)
        return {t: w for t in tickers}
    inv = inv / inv.sum()
    out = {t: float(inv.get(t, 0.0)) for t in tickers}
    s = sum(out.values())
    if s <= 0:
        w = 1.0 / len(tickers)
        return {t: w for t in tickers}
    return {k: v / s for k, v in out.items()}


def cap_weights_to_target(weights: dict[str, float], max_weight: float, target_gross: float) -> dict[str, float]:
    if not weights:
        return {}
    if max_weight <= 0:
        s = sum(weights.values())
        if s <= 0:
            return {}
        return {k: (v / s) * target_gross for k, v in weights.items()}

    n = len(weights)
    feasible_gross = min(target_gross, n * max_weight)
    if feasible_gross <= 0:
        return {}

    raw_sum = sum(weights.values())
    if raw_sum <= 0:
        return {}
    working = {k: v / raw_sum * feasible_gross for k, v in weights.items()}
    fixed: dict[str, float] = {}

    while True:
        over = [k for k, v in working.items() if v > max_weight + 1e-12]
        if not over:
            break
        for k in over:
            fixed[k] = max_weight
            working.pop(k, None)
        rem_target = feasible_gross - sum(fixed.values())
        if rem_target <= 1e-12 or not working:
            working = {}
            break
        rem_sum = sum(working.values())
        if rem_sum <= 0:
            working = {}
            break
        scale = rem_target / rem_sum
        working = {k: v * scale for k, v in working.items()}

    out = {}
    out.update(fixed)
    out.update(working)
    return dict(sorted(out.items()))


def risk_budget_weights(ret_window: pd.DataFrame, tickers: list[str], stg: StrategyConfig) -> dict[str, float]:
    if not tickers:
        return {}
    if ret_window.empty or len(ret_window) < 10:
        w = 1.0 / len(tickers)
        return {t: w for t in tickers}
    cols = [t for t in tickers if t in ret_window.columns]
    if not cols:
        return {}
    sample = ret_window[cols].dropna(how="all")
    if len(sample) < 10:
        w = 1.0 / len(cols)
        return {t: w for t in cols}
    vol = sample.std(ddof=0).replace(0.0, np.nan)
    inv = (1.0 / vol).replace([np.inf, -np.inf], np.nan).dropna()
    inv = inv / inv.sum() if not inv.empty else pd.Series(dtype=float)
    cov = sample.cov().fillna(0.0)
    if cov.empty:
        w = 1.0 / len(cols)
        return {t: w for t in cols}
    alpha = float(np.clip(stg.risk_budget_shrinkage, 0.0, 1.0))
    diag = np.diag(np.diag(cov.values))
    shrunk = ((1.0 - alpha) * cov.values) + (alpha * diag)
    ridge = 1e-6 * np.eye(len(cols))
    ones = np.ones(len(cols), dtype=float)
    try:
        raw = np.linalg.solve(shrunk + ridge, ones)
    except np.linalg.LinAlgError:
        if inv.empty:
            w = 1.0 / len(cols)
            return {t: w for t in cols}
        inv = inv / inv.sum()
        return {str(k): float(v) for k, v in inv.items()}
    raw = np.clip(raw, 0.0, None)
    if float(raw.sum()) <= 0.0:
        w = 1.0 / len(cols)
        return {t: w for t in cols}
    raw = raw / raw.sum()
    weights = pd.Series({str(t): float(w) for t, w in zip(cols, raw)})
    blend = float(np.clip(stg.risk_budget_iv_blend, 0.0, 1.0))
    if blend > 0.0 and not inv.empty:
        inv = inv.reindex(weights.index).fillna(0.0)
        if float(inv.sum()) > 0.0:
            inv = inv / inv.sum()
            weights = ((1.0 - blend) * weights) + (blend * inv)
            weights = weights.clip(lower=0.0)
            if float(weights.sum()) > 0.0:
                weights = weights / weights.sum()
    return {str(k): float(v) for k, v in weights.items() if float(v) > 0.0}


def mad_multiplier(gap_pct: float, stg: StrategyConfig) -> float:
    if not np.isfinite(gap_pct):
        return stg.mad_w2
    if gap_pct < stg.mad_t1:
        return stg.mad_w1
    if gap_pct < stg.mad_t2:
        return stg.mad_w2
    if gap_pct < stg.mad_t3:
        return stg.mad_w3
    return stg.mad_w4


def score_weights_from_rank(df_rank: pd.DataFrame, stg: StrategyConfig) -> dict[str, float]:
    if df_rank is None or df_rank.empty:
        return {}
    picked = df_rank.head(max(1, int(stg.score_top_k))).copy()
    if picked.empty:
        return {}

    s = picked["buy_score"].clip(lower=0.0).pow(stg.score_power)
    mad_scale = picked["mad_gap"].apply(lambda x: mad_multiplier(float(x), stg))
    raw = (s * mad_scale).replace([np.inf, -np.inf], np.nan).dropna()
    raw = raw[raw > 0]
    if raw.empty:
        return {}
    raw = raw / raw.sum()
    return {str(k): float(v) for k, v in raw.items()}
