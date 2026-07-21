from __future__ import annotations

from typing import Any


def normalize_candidate_features(candidate: Any) -> dict[str, float]:
    feature_obj = candidate.features
    return {
        "close": float(feature_obj.close),
        "ema_20": float(feature_obj.ema_fast),
        "ema_50": float(feature_obj.ema_slow),
        "volume_zscore": float(feature_obj.volume_ratio - 1.0),
        # System B does not expose 7d drawdown directly; this remains an auditable approximation.
        "drawdown_7d": max(0.0, float(feature_obj.atr_pct) * 3.0),
    }
