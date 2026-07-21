from __future__ import annotations

from pathlib import Path

from app.domains.experiments.btc_1d_upside_imbalance_reclaim_continuation_high_cagr_batch import (
    Btc1dUpsideImbalanceReclaimContinuationHighCagrBatchService,
)


def test_upside_imbalance_reclaim_continuation_batch_produces_ranked_results(tmp_path: Path) -> None:
    service = Btc1dUpsideImbalanceReclaimContinuationHighCagrBatchService(
        analysis_results_dir=tmp_path / "analysis",
    )

    result = service.run_batch(run_id="test-btc-1d-upside-imbalance-reclaim-continuation")

    assert result["run_id"] == "test-btc-1d-upside-imbalance-reclaim-continuation"
    assert len(result["results"]) == 4
    assert [row["cagr"] for row in result["results"]] == sorted(
        [row["cagr"] for row in result["results"]],
        reverse=True,
    )
    assert Path(result["analysis_result_json"]).exists()
    assert Path(result["analysis_result_csv"]).exists()


def test_upside_imbalance_reclaim_continuation_batch_labels_variants(tmp_path: Path) -> None:
    service = Btc1dUpsideImbalanceReclaimContinuationHighCagrBatchService(
        analysis_results_dir=tmp_path / "analysis",
    )

    result = service.run_batch(run_id="test-btc-1d-upside-imbalance-reclaim-continuation-labels")

    labels = {row["variant_label"] for row in result["results"]}
    assert labels == {
        "reference",
        "faster_reclaim",
        "cleaner_imbalance",
        "slower_trend",
    }
