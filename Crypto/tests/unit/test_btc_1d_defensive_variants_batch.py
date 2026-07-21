from __future__ import annotations

from pathlib import Path

from app.domains.evaluation.candidate_evaluator import CandidateEvaluator
from app.domains.experiments.btc_1d_defensive_variants_batch import (
    Btc1dDefensiveVariantsConfig,
    Btc1dDefensiveVariantsBatchService,
)
from app.domains.governance.artifact_store import ArtifactStore
from scripts.run_btc_1d_defensive_variants_batch import parse_args


def test_btc_1d_defensive_variants_cli_defaults() -> None:
    config = parse_args([])

    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200


def test_btc_1d_defensive_variants_batch_writes_artifacts(tmp_path: Path) -> None:
    service = Btc1dDefensiveVariantsBatchService(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        evaluator=CandidateEvaluator(cache_dir=tmp_path / "cache"),
        analysis_results_dir=tmp_path / "analysis",
    )

    result = service.run_batch(
        Btc1dDefensiveVariantsConfig(allow_synthetic_ohlcv_fallback=True, periods=240),
        run_id="btc-1d-def-batch",
    )

    run_dir = tmp_path / "artifacts" / "btc-1d-def-batch"
    assert (run_dir / "btc_1d_defensive_variants_batch.json").exists()
    assert (run_dir / "run_leaderboard.json").exists()
    assert Path(result["analysis_result_json"]).exists()
    assert Path(result["analysis_result_csv"]).exists()
    assert len(result["results"]) == 4
