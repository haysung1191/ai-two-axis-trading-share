from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_expansion_confirmation_batch import (
    Btc1dVolatilityExpansionConfirmationBatchService,
    Btc1dVolatilityExpansionConfirmationConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_volatility_expansion_confirmation_batch_runs(tmp_path) -> None:
    service = Btc1dVolatilityExpansionConfirmationBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dVolatilityExpansionConfirmationConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-vol-exp-confirmation-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")


def test_btc_1d_volatility_expansion_confirmation_batch_labels_present(tmp_path) -> None:
    service = Btc1dVolatilityExpansionConfirmationBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dVolatilityExpansionConfirmationConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-vol-exp-confirmation-labels",
    )

    labels = {row["variant_label"] for row in result["results"]}
    assert "reference_shorter_memory" in labels
    assert "buffered_longer_confirmation" in labels
