from __future__ import annotations

from app.domains.experiments.btc_1d_pullthrough_candidate_structural_repair_batch import (
    Btc1dPullthroughCandidateStructuralRepairBatchService,
    Btc1dPullthroughCandidateStructuralRepairConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_pullthrough_candidate_structural_repair_batch_runs(tmp_path) -> None:
    service = Btc1dPullthroughCandidateStructuralRepairBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dPullthroughCandidateStructuralRepairConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-pullthrough-structural-repair-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["best_variant"]["variant_label"] in {variant["label"] for variant in DEFAULT_VARIANTS}
    assert result["analysis_result_json"].endswith(".json")
