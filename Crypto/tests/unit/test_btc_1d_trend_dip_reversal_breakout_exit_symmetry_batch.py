from __future__ import annotations

from pathlib import Path

from app.domains.experiments.btc_1d_trend_dip_reversal_breakout_exit_symmetry_batch import (
    Btc1dTrendDipReversalBreakoutExitSymmetryBatchService,
)


def test_trend_dip_exit_symmetry_batch_produces_ranked_results(tmp_path: Path) -> None:
    service = Btc1dTrendDipReversalBreakoutExitSymmetryBatchService(
        analysis_results_dir=tmp_path / "analysis",
    )

    result = service.run_batch(run_id="test-btc-1d-trend-dip-exit-symmetry")

    assert result["run_id"] == "test-btc-1d-trend-dip-exit-symmetry"
    assert len(result["results"]) == 5
    assert [row["cagr"] for row in result["results"]] == sorted(
        [row["cagr"] for row in result["results"]],
        reverse=True,
    )
    assert Path(result["analysis_result_json"]).exists()
    assert Path(result["analysis_result_csv"]).exists()


def test_trend_dip_exit_symmetry_batch_labels_variants(tmp_path: Path) -> None:
    service = Btc1dTrendDipReversalBreakoutExitSymmetryBatchService(
        analysis_results_dir=tmp_path / "analysis",
    )

    result = service.run_batch(run_id="test-btc-1d-trend-dip-exit-symmetry-labels")

    labels = {row["variant_label"] for row in result["results"]}
    assert labels == {
        "current_reference",
        "tighter_stop_longer_hold",
        "looser_stop_shorter_hold",
        "tighter_stop_mid_hold",
        "mid_stop_shorter_hold",
    }
