from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.domains.evaluation.candidate_evaluator import CandidateEvaluator
from app.domains.experiments.major_core_strategy_batch import MajorCoreBatchConfig, MajorCoreStrategyBatchService
from app.domains.governance.artifact_store import ArtifactStore
from scripts.run_major_core_strategy_batch import parse_args
from strategies.major_4h_trend_following import Strategy as MajorTrendStrategy


def test_major_core_batch_cli_defaults() -> None:
    config = parse_args([])

    assert config.interval == "4h"
    assert config.periods == 2000
    assert config.symbols == ("BTCUSDT", "ETHUSDT")


def test_major_trend_strategy_generates_signals() -> None:
    idx = pd.date_range("2024-01-01", periods=140, freq="4h", tz="UTC")
    close = pd.Series([100.0 + (i * 0.8) for i in range(len(idx))], index=idx, dtype=float)
    frame = pd.DataFrame(
        {
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": 1000.0,
        },
        index=idx,
    )

    signal = MajorTrendStrategy().generate_signals(frame)

    assert signal.sum() > 0


def test_major_core_batch_writes_artifacts(tmp_path: Path) -> None:
    service = MajorCoreStrategyBatchService(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        evaluator=CandidateEvaluator(cache_dir=tmp_path / "cache"),
        analysis_results_dir=tmp_path / "analysis",
    )

    result = service.run_batch(
        MajorCoreBatchConfig(allow_synthetic_ohlcv_fallback=True, periods=240),
        run_id="major-core-test",
    )

    run_dir = tmp_path / "artifacts" / "major-core-test"
    assert (run_dir / "major_core_strategy_batch.json").exists()
    assert (run_dir / "run_leaderboard.json").exists()
    assert Path(result["analysis_result_json"]).exists()
    assert Path(result["analysis_result_csv"]).exists()
    assert len(result["results"]) == 2
