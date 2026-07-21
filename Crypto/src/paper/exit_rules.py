from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExitDecision:
    should_exit: bool
    exit_price_pre_slip: float | None
    reason: str | None


def evaluate_long_exit(
    candle_o: float,
    candle_h: float,
    candle_l: float,
    candle_c: float,
    stop_price: float,
    tp_price: float,
    time_exit_now: bool,
) -> ExitDecision:
    """
    Conservative exit evaluation using only this candle OHLC.

    - If both SL and TP hit in same candle: assume SL first (worst case)
    - Gap rules:
      - If O <= SL: SL at O (worst)
      - If O >= TP: TP at TP (conservative)
    - Time exit: if time_exit_now and no SL/TP hit, exit at close
    """
    hit_sl = candle_l <= stop_price
    hit_tp = candle_h >= tp_price

    if hit_sl and hit_tp:
        if candle_o <= stop_price:
            return ExitDecision(True, candle_o, "SL_GAP")
        return ExitDecision(True, stop_price, "SL")

    if hit_sl:
        if candle_o <= stop_price:
            return ExitDecision(True, candle_o, "SL_GAP")
        return ExitDecision(True, stop_price, "SL")

    if hit_tp:
        if candle_o >= tp_price:
            return ExitDecision(True, tp_price, "TP_GAP")
        return ExitDecision(True, tp_price, "TP")

    if time_exit_now:
        return ExitDecision(True, candle_c, "TIME")

    return ExitDecision(False, None, None)

