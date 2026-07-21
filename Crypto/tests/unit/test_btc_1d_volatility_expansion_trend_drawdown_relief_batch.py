from __future__ import annotations

from app.domains.experiments.btc_1d_volatility_expansion_trend_drawdown_relief_batch import (
    Btc1dVolatilityExpansionTrendDrawdownReliefBatchService,
    Btc1dVolatilityExpansionTrendDrawdownReliefConfig,
    DEFAULT_VARIANTS,
)


def test_btc_1d_volatility_expansion_trend_drawdown_relief_batch_runs(tmp_path) -> None:
    service = Btc1dVolatilityExpansionTrendDrawdownReliefBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dVolatilityExpansionTrendDrawdownReliefConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-volatility-expansion-trend-drawdown-relief-test",
    )

    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")


def test_btc_1d_volatility_expansion_trend_drawdown_relief_labels_present(tmp_path) -> None:
    service = Btc1dVolatilityExpansionTrendDrawdownReliefBatchService(analysis_results_dir=tmp_path)

    result = service.run_batch(
        Btc1dVolatilityExpansionTrendDrawdownReliefConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-volatility-expansion-trend-drawdown-relief-labels",
    )

    labels = {row["variant_label"] for row in result["results"]}
    assert "top_reference" in labels
    assert "tighter_stop_shorter_hold" in labels
