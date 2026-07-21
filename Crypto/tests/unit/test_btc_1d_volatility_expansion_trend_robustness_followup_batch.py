from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_expansion_trend_robustness_followup_batch import (
    Btc1dVolatilityExpansionTrendRobustnessFollowupBatchService,
    Btc1dVolatilityExpansionTrendRobustnessFollowupConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_volatility_expansion_trend_robustness_followup_batch_runs(tmp_path) -> None:
    service = Btc1dVolatilityExpansionTrendRobustnessFollowupBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dVolatilityExpansionTrendRobustnessFollowupConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-vol-exp-trend-robustness-followup-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")


def test_btc_1d_volatility_expansion_trend_robustness_followup_batch_labels_present(tmp_path) -> None:
    service = Btc1dVolatilityExpansionTrendRobustnessFollowupBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dVolatilityExpansionTrendRobustnessFollowupConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-vol-exp-trend-robustness-followup-labels",
    )

    labels = {row["variant_label"] for row in result["results"]}
    assert "stronger_expansion_filter_reference" in labels
    assert "shorter_memory_and_hold" in labels
