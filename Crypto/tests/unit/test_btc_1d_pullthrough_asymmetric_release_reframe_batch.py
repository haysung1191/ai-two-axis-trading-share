from __future__ import annotations

from app.domains.experiments.btc_1d_pullthrough_asymmetric_release_reframe_batch import (
    Btc1dPullthroughAsymmetricReleaseReframeBatchService,
    Btc1dPullthroughAsymmetricReleaseReframeConfig,
    DEFAULT_VARIANTS,
)


def test_pullthrough_asymmetric_release_reframe_batch_runs(tmp_path) -> None:
    service = Btc1dPullthroughAsymmetricReleaseReframeBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dPullthroughAsymmetricReleaseReframeConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-pullthrough-asymmetric-release-reframe-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
