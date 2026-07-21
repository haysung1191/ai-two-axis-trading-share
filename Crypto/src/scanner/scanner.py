from __future__ import annotations

import json
from dataclasses import dataclass

from src.scanner.indicators import atr, bollinger_width, ema, macd, rsi, volume_ratio
from src.scanner.scoring import FeatureSnapshot, score_candidate


@dataclass(frozen=True)
class Candidate:
    symbol: str
    score: float
    rank: int
    signal_close_ts_ms: int
    features: FeatureSnapshot
    stop_dist: float
    tp_dist: float
    time_exit_ts_ms: int
    blocked_reason: str | None = None

    def features_json(self) -> str:
        return json.dumps(self.features.__dict__, separators=(",", ":"), sort_keys=True)


def scan_symbol(
    symbol: str,
    close_ts_ms: int,
    interval_ms: int,
    candles: list[tuple[int, float, float, float, float, float]],
    cfg_scanner: dict,
    cfg_strategy: dict,
) -> Candidate | None:
    by_ts = {int(ts): (o, h, l, c, v) for ts, o, h, l, c, v in candles}
    # Bithumb 1h candles are keyed by candle START timestamp.
    # For a candle that closes at close_ts_ms, the candle starts at close_ts_ms - interval_ms.
    signal_start_ts_ms = int(close_ts_ms - interval_ms)
    if signal_start_ts_ms not in by_ts:
        return None

    # Only include candles up to the just-closed candle (exclude the in-progress candle at close_ts_ms).
    keys = sorted(k for k in by_ts.keys() if k <= signal_start_ts_ms)
    if len(keys) < max(60, int(cfg_scanner.get("lookback_candles", 200)) // 2):
        return None

    closes = [float(by_ts[k][3]) for k in keys]
    highs = [float(by_ts[k][1]) for k in keys]
    lows = [float(by_ts[k][2]) for k in keys]
    vols = [float(by_ts[k][4]) for k in keys]

    rsi_v = rsi(closes, int(cfg_scanner.get("rsi_period", 14)))
    macd_v = macd(
        closes,
        fast=int(cfg_scanner.get("ema_fast", 12)),
        slow=int(cfg_scanner.get("ema_slow", 26)),
        signal_period=9,
    )
    ema_fast_v = ema(closes, int(cfg_scanner.get("ema_fast", 12)))
    ema_slow_v = ema(closes, int(cfg_scanner.get("ema_slow", 26)))
    atr_v = atr(highs, lows, closes, int(cfg_strategy.get("atr_period", 14)))
    bb_w = bollinger_width(closes, int(cfg_scanner.get("bb_period", 20)), float(cfg_scanner.get("bb_std", 2.0)))
    vol_r = volume_ratio(vols, int(cfg_scanner.get("vol_ratio_period", 20)))

    idx = len(closes) - 1
    if not (rsi_v and macd_v.hist and ema_fast_v and ema_slow_v and atr_v and bb_w and vol_r):
        return None

    f = FeatureSnapshot(
        rsi=float(rsi_v[min(idx, len(rsi_v) - 1)]),
        macd_hist=float(macd_v.hist[min(idx, len(macd_v.hist) - 1)]),
        ema_fast=float(ema_fast_v[idx]),
        ema_slow=float(ema_slow_v[idx]),
        volume_ratio=float(vol_r[min(idx, len(vol_r) - 1)]),
        atr=float(atr_v[min(idx, len(atr_v) - 1)]),
        atr_pct=float(atr_v[min(idx, len(atr_v) - 1)] / closes[idx]) if closes[idx] else 0.0,
        bb_width=float(bb_w[min(idx, len(bb_w) - 1)]),
        close=float(closes[idx]),
    )

    score = score_candidate(f)
    stop_dist = float(cfg_strategy.get("stop_atr_mult", 1.5)) * f.atr
    tp_dist = float(cfg_strategy.get("take_profit_r_mult", 2.0)) * stop_dist
    # signal at close_ts; entry at close_ts+1h; time-exit after N candles => close_ts + (N+1)*1h
    time_exit_ts_ms = int(close_ts_ms + interval_ms * (int(cfg_strategy.get("time_exit_candles", 24)) + 1))

    return Candidate(
        symbol=symbol,
        score=score,
        rank=0,
        signal_close_ts_ms=close_ts_ms,
        features=f,
        stop_dist=stop_dist,
        tp_dist=tp_dist,
        time_exit_ts_ms=time_exit_ts_ms,
    )
