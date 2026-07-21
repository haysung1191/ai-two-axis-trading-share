from __future__ import annotations

import numpy as np
import pandas as pd

from app.domains.experiments.btc_1d_volatility_expansion_reclaim_high_cagr_batch import (
    Btc1dVolatilityExpansionReclaimHighCagrBatchService,
    Btc1dVolatilityExpansionReclaimHighCagrConfig,
    DEFAULT_VARIANTS,
)
from strategies.btc_1d_volatility_expansion_reclaim import compute_btc_1d_volatility_expansion_reclaim_signals


def make_ohlcv(length: int = 320, trend: float = 0.8, amplitude: float = 3.5, volume_cycle: float = 0.5) -> pd.DataFrame:
    index = pd.date_range("2020-01-01", periods=length, freq="D")
    base = np.linspace(100.0, 100.0 + trend * length, num=length)
    wave = amplitude * np.sin(np.linspace(0.0, 10.0, num=length))
    close = base + wave
    open_ = close - 0.5
    high = close + 1.3
    low = close - 1.3
    volume = 1_000.0 + (250.0 * np.sin(np.linspace(0.0, 12.0 * volume_cycle, num=length))) + np.linspace(0.0, 140.0, num=length)
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


def test_volatility_expansion_reclaim_strategy_emits_signals() -> None:
    ohlcv = make_ohlcv()
    signals = compute_btc_1d_volatility_expansion_reclaim_signals(ohlcv)
    assert len(signals) == len(ohlcv)
    assert signals.isin([0.0, 1.0]).all()


def test_volatility_expansion_reclaim_batch_outputs_analysis(tmp_path) -> None:
    service = Btc1dVolatilityExpansionReclaimHighCagrBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dVolatilityExpansionReclaimHighCagrConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-volatility-expansion-reclaim-high-cagr-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
