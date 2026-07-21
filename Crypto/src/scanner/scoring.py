from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureSnapshot:
    rsi: float
    macd_hist: float
    ema_fast: float
    ema_slow: float
    volume_ratio: float
    atr: float
    atr_pct: float
    bb_width: float
    close: float


def score_candidate(f: FeatureSnapshot) -> float:
    score = 0.0
    score += max(-2.0, min(2.0, f.macd_hist * 10.0))
    score += 1.0 if f.ema_fast > f.ema_slow else -0.5
    score += 0.5 if f.close > f.ema_slow else -0.5
    score += max(-1.0, min(2.0, (f.volume_ratio - 1.0)))
    if f.rsi > 75.0:
        score -= 1.0
    if f.atr_pct > 0.10:
        score -= 0.5
    return score

