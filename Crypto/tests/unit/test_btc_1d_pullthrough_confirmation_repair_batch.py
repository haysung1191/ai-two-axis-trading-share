from __future__ import annotations

from app.domains.experiments.btc_1d_pullthrough_confirmation_repair_batch import (
    Btc1dPullthroughConfirmationRepairBatchService,
    Btc1dPullthroughConfirmationRepairConfig,
    DEFAULT_VARIANTS,
)
from app.domains.strategy.loader import load_strategy


def test_pullthrough_confirmation_strategy_loads() -> None:
    strategy = load_strategy("btc_1d_volatility_expansion_pullthrough_confirmation")
    assert strategy.name == "btc_1d_volatility_expansion_pullthrough_confirmation"


def test_btc_1d_pullthrough_confirmation_repair_batch_runs(tmp_path) -> None:
    service = Btc1dPullthroughConfirmationRepairBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dPullthroughConfirmationRepairConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-pullthrough-confirmation-repair-test",
    )
    assert len(result["results"]) == len(DEFAULT_VARIANTS)
    assert result["best_variant"]["variant_label"] in {variant["label"] for variant in DEFAULT_VARIANTS}
    assert result["analysis_result_json"].endswith(".json")
