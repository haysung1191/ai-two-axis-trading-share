from __future__ import annotations

import math
from dataclasses import dataclass


def ema(values: list[float], period: int) -> list[float]:
    if period <= 0 or len(values) == 0:
        return []
    k = 2.0 / (period + 1.0)
    out: list[float] = []
    e = values[0]
    out.append(e)
    for v in values[1:]:
        e = v * k + e * (1.0 - k)
        out.append(e)
    return out


def rsi(closes: list[float], period: int) -> list[float]:
    if period <= 0 or len(closes) < period + 1:
        return []
    gains: list[float] = []
    losses: list[float] = []
    for i in range(1, len(closes)):
        ch = closes[i] - closes[i - 1]
        gains.append(max(0.0, ch))
        losses.append(max(0.0, -ch))

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    out = [50.0] * period  # padding

    def calc(ag: float, al: float) -> float:
        if al == 0:
            return 100.0
        rs = ag / al
        return 100.0 - (100.0 / (1.0 + rs))

    out.append(calc(avg_gain, avg_loss))
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        out.append(calc(avg_gain, avg_loss))
    return out


@dataclass(frozen=True)
class Macd:
    macd: list[float]
    signal: list[float]
    hist: list[float]


def macd(closes: list[float], fast: int = 12, slow: int = 26, signal_period: int = 9) -> Macd:
    if len(closes) == 0:
        return Macd([], [], [])
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    m = [a - b for a, b in zip(ema_fast, ema_slow)]
    s = ema(m, signal_period)
    h = [a - b for a, b in zip(m, s)]
    return Macd(m, s, h)


def true_range(highs: list[float], lows: list[float], closes: list[float]) -> list[float]:
    if not highs or not lows or not closes:
        return []
    out = [highs[0] - lows[0]]
    for i in range(1, len(highs)):
        out.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))
    return out


def atr(highs: list[float], lows: list[float], closes: list[float], period: int) -> list[float]:
    tr = true_range(highs, lows, closes)
    if len(tr) < period:
        return []
    out: list[float] = []
    a = sum(tr[:period]) / period
    out.extend([a] * period)
    for i in range(period, len(tr)):
        a = (a * (period - 1) + tr[i]) / period
        out.append(a)
    return out


def bollinger_width(closes: list[float], period: int, std_mult: float) -> list[float]:
    if period <= 1 or len(closes) < period:
        return []
    out: list[float] = []
    for i in range(len(closes)):
        if i + 1 < period:
            out.append(0.0)
            continue
        w = closes[i + 1 - period : i + 1]
        mean = sum(w) / period
        var = sum((x - mean) ** 2 for x in w) / period
        sd = math.sqrt(var)
        upper = mean + std_mult * sd
        lower = mean - std_mult * sd
        out.append(0.0 if mean == 0 else (upper - lower) / mean)
    return out


def volume_ratio(volumes: list[float], period: int) -> list[float]:
    if period <= 0 or len(volumes) < period:
        return []
    out: list[float] = []
    for i in range(len(volumes)):
        if i + 1 < period:
            out.append(0.0)
            continue
        avg = sum(volumes[i + 1 - period : i + 1]) / period
        out.append(0.0 if avg == 0 else volumes[i] / avg)
    return out

