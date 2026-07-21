from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.domains.evaluation.candidate_evaluator import CandidateEvaluator
from app.domains.experiments.btc_1d_regime_gate_variants_batch import (
    Btc1dRegimeGateVariantsConfig,
    Btc1dRegimeGateVariantsBatchService,
)
from app.domains.governance.artifact_store import ArtifactStore
from scripts.run_btc_1d_regime_gate_variants_batch import parse_args
from strategies.btc_1d_ema_trend_atr_exit import Strategy as Btc1dStrategy


def test_btc_1d_regime_gate_variants_cli_defaults() -> None:
    config = parse_args([])

    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.lookback_periods == (1400, 1800, 2200, 2600)


def test_btc_1d_strategy_regime_gate_blocks_sideways_series() -> None:
    idx = pd.date_range("2024-01-01", periods=220, freq="1d", tz="UTC")
    close = pd.Series([100.0 + ((i % 4) * 0.05) for i in range(len(idx))], index=idx, dtype=float)
    frame = pd.DataFrame(
        {
            "open": close,
            "high": close + 0.1,
            "low": close - 0.1,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )

    signal = Btc1dStrategy().generate_signals(
        frame,
        {
            "volatility_target": 0.2,
            "min_position_size": 0.35,
            "trend_filter_window": 20,
            "min_trend_strength": 0.0035,
        },
    )

    assert float(signal.max()) == 0.0


def test_btc_1d_regime_gate_variants_batch_writes_artifacts(tmp_path: Path) -> None:
    service = Btc1dRegimeGateVariantsBatchService(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        evaluator=CandidateEvaluator(cache_dir=tmp_path / "cache"),
        analysis_results_dir=tmp_path / "analysis",
    )

    result = service.run_batch(
        Btc1dRegimeGateVariantsConfig(
            lookback_periods=(240, 320),
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-regime-gate-test",
    )

    run_dir = tmp_path / "artifacts" / "btc-1d-regime-gate-test"
    assert (run_dir / "btc_1d_regime_gate_variants_batch.json").exists()
    assert (run_dir / "run_leaderboard.json").exists()
    assert Path(result["analysis_result_json"]).exists()
    assert len(result["results"]) == 3
