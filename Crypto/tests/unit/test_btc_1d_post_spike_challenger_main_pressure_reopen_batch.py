from __future__ import annotations

import app.domains.experiments.btc_1d_post_spike_challenger_main_pressure_reopen_batch as mod
from app.domains.experiments.btc_1d_post_spike_challenger_main_pressure_reopen_batch import (
    Btc1dPostSpikeChallengerMainPressureReopenBatchService,
    Btc1dPostSpikeChallengerMainPressureReopenConfig,
)


def test_btc_1d_post_spike_challenger_main_pressure_reopen_batch_runs(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(mod, "DEFAULT_VARIANTS", mod.DEFAULT_VARIANTS[:3])
    service = Btc1dPostSpikeChallengerMainPressureReopenBatchService(analysis_results_dir=tmp_path)
    result = service.run_batch(
        Btc1dPostSpikeChallengerMainPressureReopenConfig(
            periods=1200,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-post-spike-challenger-main-pressure-reopen-test",
    )

    assert len(result["results"]) == len(mod.DEFAULT_VARIANTS)
    assert result["analysis_result_json"].endswith(".json")
    assert result["analysis_result_csv"].endswith(".csv")
    assert "cost20_cagr_gap_to_active_backup" in result["best_variant"]
    assert "beats_active_backup_cost20" in result["best_variant"]
