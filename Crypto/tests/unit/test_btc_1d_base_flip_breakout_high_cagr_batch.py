from __future__ import annotations

from app.domains.experiments.btc_1d_base_flip_breakout_high_cagr_batch import (
    Btc1dBaseFlipBreakoutHighCagrBatchService,
    Btc1dBaseFlipBreakoutHighCagrConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_base_flip_breakout_high_cagr_batch_runs(tmp_path) -> None:
    service = Btc1dBaseFlipBreakoutHighCagrBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dBaseFlipBreakoutHighCagrConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-base-flip-breakout-high-cagr-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
