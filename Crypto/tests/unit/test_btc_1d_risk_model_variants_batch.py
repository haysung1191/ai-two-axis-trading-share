from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.domains.evaluation.candidate_evaluator import CandidateEvaluator
from app.domains.experiments.btc_1d_risk_model_variants_batch import (
    Btc1dRiskModelVariantsBatchService,
    Btc1dRiskModelVariantsConfig,
)
from app.domains.governance.artifact_store import ArtifactStore
from scripts.run_btc_1d_risk_model_variants_batch import parse_args
from strategies.btc_1d_ema_trend_atr_exit import Strategy as Btc1dStrategy


def test_btc_1d_risk_model_variants_cli_defaults() -> None:
    config = parse_args([])

    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200


def test_btc_1d_strategy_supports_fractional_position_scaling() -> None:
    idx = pd.date_range("2024-01-01", periods=220, freq="1d", tz="UTC")
    close = pd.Series([100.0 + (i * 0.8) + ((i % 7) * 0.6) for i in range(len(idx))], index=idx, dtype=float)
    frame = pd.DataFrame(
        {
            "open": close,
            "high": close + 1.5,
            "low": close - 1.5,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )

    signal = Btc1dStrategy().generate_signals(
        frame,
        {
            "volatility_target": 0.2,
            "volatility_window": 20,
            "min_position_size": 0.3,
        },
    )

    assert signal.max() <= 1.0
    assert ((signal > 0.0) & (signal < 1.0)).any()


def test_btc_1d_risk_model_variants_batch_writes_artifacts(tmp_path: Path) -> None:
    service = Btc1dRiskModelVariantsBatchService(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        evaluator=CandidateEvaluator(cache_dir=tmp_path / "cache"),
        analysis_results_dir=tmp_path / "analysis",
    )

    result = service.run_batch(
        Btc1dRiskModelVariantsConfig(allow_synthetic_ohlcv_fallback=True, periods=240),
        run_id="btc-1d-risk-batch",
    )

    run_dir = tmp_path / "artifacts" / "btc-1d-risk-batch"
    assert (run_dir / "btc_1d_risk_model_variants_batch.json").exists()
    assert (run_dir / "run_leaderboard.json").exists()
    assert Path(result["analysis_result_json"]).exists()
    assert Path(result["analysis_result_csv"]).exists()
    assert len(result["results"]) == 4
