from __future__ import annotations


def _clip(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def _offensive_component_breakdown(
    *,
    mom_12m: float,
    mom_6m: float,
    mom_1m: float,
    mad_gap_pct: float,
    breakout_distance_pct: float,
    volume_ratio_5d_20d: float,
) -> dict[str, float]:
    return {
        "offensive_component_mom12": _clip(mom_12m, 0, 240) / 240 * 30,
        "offensive_component_mom6": _clip(mom_6m, 0, 120) / 120 * 20,
        "offensive_component_mom1": _clip(mom_1m, 0, 40) / 40 * 15,
        "offensive_component_trend": _clip(mad_gap_pct, 0, 35) / 35 * 15,
        "offensive_component_breakout": _clip(100 + breakout_distance_pct, 80, 100) / 100 * 10,
        "offensive_component_volume": _clip(volume_ratio_5d_20d, 0.5, 2.0) / 2.0 * 10,
    }


def calculate_momentum_metrics(prices: list[dict]) -> dict | None:
    if not prices:
        return None

    try:
        idx_1m, idx_3m, idx_6m, idx_12m = 20, 60, 120, 240
        if len(prices) <= idx_12m:
            return None

        p_cur = float(prices[0]["stck_clpr"])
        p_1m = float(prices[idx_1m]["stck_clpr"])
        p_3m = float(prices[idx_3m]["stck_clpr"])
        p_6m = float(prices[idx_6m]["stck_clpr"])
        p_12m = float(prices[idx_12m]["stck_clpr"])

        mom_1m = (p_cur - p_1m) / p_1m * 100 if p_1m > 0 else 0
        mom_3m = (p_cur - p_3m) / p_3m * 100 if p_3m > 0 else 0
        mom_6m = (p_cur - p_6m) / p_6m * 100 if p_6m > 0 else 0
        mom_12m = (p_cur - p_12m) / p_12m * 100 if p_12m > 0 else 0
        avg_mom = (mom_1m + mom_3m + mom_6m + mom_12m) / 4

        volume_5d_avg = sum(float(p["acml_vol"]) for p in prices[:5]) / 5 if len(prices) >= 5 else 0
        volume_20d_avg = sum(float(p["acml_vol"]) for p in prices[:20]) / 20 if len(prices) >= 20 else 0
        volume_ratio_5d_20d = volume_5d_avg / volume_20d_avg if volume_20d_avg > 0 else 0

        ma_21 = sum(float(prices[i]["stck_clpr"]) for i in range(21)) / 21 if len(prices) >= 21 else p_cur
        ma_200 = sum(float(prices[i]["stck_clpr"]) for i in range(200)) / 200 if len(prices) >= 200 else p_cur
        mrat = ma_21 / ma_200 if ma_200 > 0 else 0
        mad_gap_pct = (ma_21 - ma_200) / ma_200 * 100 if ma_200 > 0 else 0
        trailing_252d_high = max(float(p["stck_clpr"]) for p in prices[:252]) if len(prices) >= 252 else max(
            float(p["stck_clpr"]) for p in prices
        )
        breakout_distance_pct = (
            (p_cur - trailing_252d_high) / trailing_252d_high * 100 if trailing_252d_high > 0 else 0
        )
        momentum_acceleration = mom_1m - mom_3m

        offensive_components = _offensive_component_breakdown(
            mom_12m=mom_12m,
            mom_6m=mom_6m,
            mom_1m=mom_1m,
            mad_gap_pct=mad_gap_pct,
            breakout_distance_pct=breakout_distance_pct,
            volume_ratio_5d_20d=volume_ratio_5d_20d,
        )
        offensive_score = sum(offensive_components.values())

        metrics = {
            "momentum_1m": round(mom_1m, 2),
            "momentum_3m": round(mom_3m, 2),
            "momentum_6m": round(mom_6m, 2),
            "momentum_12m": round(mom_12m, 2),
            "avg_momentum": round(avg_mom, 2),
            "MA_21": round(ma_21, 0),
            "MA_200": round(ma_200, 0),
            "MRAT": round(mrat, 4),
            "MAD_gap_pct": round(mad_gap_pct, 2),
            "volume_5d_avg": round(volume_5d_avg, 2),
            "volume_20d_avg": round(volume_20d_avg, 2),
            "volume_ratio_5d_20d": round(volume_ratio_5d_20d, 4),
            "trailing_252d_high": round(trailing_252d_high, 2),
            "breakout_distance_pct": round(breakout_distance_pct, 2),
            "momentum_acceleration": round(momentum_acceleration, 2),
            "offensive_score": round(offensive_score, 2),
            "current_price": p_cur,
        }
        metrics.update({key: round(value, 2) for key, value in offensive_components.items()})
        return metrics
    except Exception:
        return None
