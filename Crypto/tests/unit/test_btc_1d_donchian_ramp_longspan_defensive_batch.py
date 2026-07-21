from __future__ import annotations

from app.domains.experiments.btc_1d_donchian_ramp_longspan_defensive_batch import (
    Btc1dDonchianRampLongspanDefensiveBatchService,
    Btc1dDonchianRampLongspanDefensiveConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_donchian_ramp_longspan_defensive_batch_runs(tmp_path) -> None:
    service = Btc1dDonchianRampLongspanDefensiveBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dDonchianRampLongspanDefensiveConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-donchian-ramp-longspan-defensive-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
