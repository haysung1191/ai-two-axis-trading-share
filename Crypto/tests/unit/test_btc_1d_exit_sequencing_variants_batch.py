from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.domains.evaluation.candidate_evaluator import CandidateEvaluator
from app.domains.experiments.btc_1d_exit_sequencing_variants_batch import (
    Btc1dExitSequencingVariantsBatchService,
    Btc1dExitSequencingVariantsConfig,
)
from app.domains.governance.artifact_store import ArtifactStore
from scripts.run_btc_1d_exit_sequencing_variants_batch import parse_args
from strategies.btc_1d_ema_trend_atr_exit import Strategy as Btc1dStrategy


def test_btc_1d_exit_sequencing_variants_cli_defaults() -> None:
    config = parse_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.lookback_periods == (1400, 1800, 2200, 2600)


def test_btc_1d_strategy_stagnation_exit_flattens_stale_trade() -> None:
    idx = pd.date_range("2024-01-01", periods=220, freq="1d", tz="UTC")
    close = pd.Series([100.0 + min(i, 40) * 0.6 + ((i % 25) * 0.02) for i in range(len(idx))], index=idx, dtype=float)
    frame = pd.DataFrame({"open": close, "high": close + 0.4, "low": close - 0.4, "close": close, "volume": 1000.0}, index=idx)
    signal = Btc1dStrategy().generate_signals(
        frame,
        {
            "volatility_target": 0.2,
            "min_position_size": 0.35,
            "stagnation_exit_bars": 8,
            "stagnation_atr_band": 0.5,
        },
    )
    assert (signal.iloc[-20:] == 0.0).any()


def test_btc_1d_exit_sequencing_variants_batch_writes_artifacts(tmp_path: Path) -> None:
    service = Btc1dExitSequencingVariantsBatchService(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        evaluator=CandidateEvaluator(cache_dir=tmp_path / "cache"),
        analysis_results_dir=tmp_path / "analysis",
    )
    result = service.run_batch(
        Btc1dExitSequencingVariantsConfig(lookback_periods=(240, 320), allow_synthetic_ohlcv_fallback=True),
        run_id="btc-1d-exit-seq-test",
    )
    run_dir = tmp_path / "artifacts" / "btc-1d-exit-seq-test"
    assert (run_dir / "btc_1d_exit_sequencing_variants_batch.json").exists()
    assert (run_dir / "run_leaderboard.json").exists()
    assert Path(result["analysis_result_json"]).exists()
    assert len(result["results"]) == 4
