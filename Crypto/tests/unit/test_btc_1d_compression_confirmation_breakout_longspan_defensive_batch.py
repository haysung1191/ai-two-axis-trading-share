from __future__ import annotations

from app.domains.experiments.btc_1d_compression_confirmation_breakout_longspan_defensive_batch import (
    Btc1dCompressionConfirmationBreakoutLongspanDefensiveBatchService,
    Btc1dCompressionConfirmationBreakoutLongspanDefensiveConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_compression_confirmation_breakout_longspan_defensive_batch_runs(tmp_path) -> None:
    service = Btc1dCompressionConfirmationBreakoutLongspanDefensiveBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dCompressionConfirmationBreakoutLongspanDefensiveConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-compression-confirmation-breakout-longspan-defensive-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
