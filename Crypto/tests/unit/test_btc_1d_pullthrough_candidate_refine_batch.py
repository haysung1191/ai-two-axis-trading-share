from __future__ import annotations

from app.domains.experiments.btc_1d_pullthrough_candidate_refine_batch import (
    Btc1dPullthroughCandidateRefineBatchService,
    Btc1dPullthroughCandidateRefineConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_pullthrough_candidate_refine_batch_runs(tmp_path) -> None:
    service = Btc1dPullthroughCandidateRefineBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dPullthroughCandidateRefineConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-pullthrough-refine-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["best_variant"]["variant_label"] in {variant["label"] for variant in DEFAULT_VARIANTS}
    assert result["analysis_result_json"].endswith(".json")
