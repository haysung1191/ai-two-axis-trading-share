from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from app.domains.experiments.btc_1d_volume_pressure_trend_high_cagr_batch import (
    Btc1dVolumePressureTrendHighCagrConfig,
    Btc1dVolumePressureTrendHighCagrBatchService,
    DEFAULT_VARIANTS,
)
from strategies.btc_1d_volume_pressure_trend import compute_btc_1d_volume_pressure_trend_signals


def make_ohlcv(length: int = 320, trend: float = 0.7, amplitude: float = 3.0, volume_cycle: float = 0.4) -> pd.DataFrame:
    index = pd.date_range("2020-01-01", periods=length, freq="D")
    base = np.linspace(100.0, 100.0 + trend * length, num=length)
    wave = amplitude * np.sin(np.linspace(0.0, 10.0, num=length))
    close = base + wave
    open_ = close - 0.6
    high = close + 1.2
    low = close - 1.2
    volume = 1_000.0 + (250.0 * np.sin(np.linspace(0.0, 12.0 * volume_cycle, num=length))) + np.linspace(0.0, 150.0, num=length)
    return pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=index,
    )


def test_volume_pressure_trend_strategy_emits_signals() -> None:
    ohlcv = make_ohlcv(length=320, trend=0.9, amplitude=4.0, volume_cycle=0.5)
    signals = compute_btc_1d_volume_pressure_trend_signals(ohlcv)
    assert len(signals) == len(ohlcv)
    assert signals.isin([0.0, 1.0]).all()


def test_volume_pressure_trend_batch_outputs_analysis(tmp_path: Path) -> None:
    service = Btc1dVolumePressureTrendHighCagrBatchService(analysis_results_dir=tmp_path / "analysis_results")
    result = service.run_batch(
        Btc1dVolumePressureTrendHighCagrConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="unit-test-volume-pressure-trend",
    )
    assert result["run_id"] == "unit-test-volume-pressure-trend"
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert (tmp_path / "analysis_results").exists()
