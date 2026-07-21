from __future__ import annotations

from pathlib import Path

from app.domains.evaluation.candidate_evaluator import CandidateEvaluator
from app.domains.experiments.btc_1d_promoted_candidate_regression import (
    PROMOTED_PARAMETERS,
    Btc1dPromotedCandidateRegressionConfig,
    Btc1dPromotedCandidateRegressionService,
)
from app.domains.governance.artifact_store import ArtifactStore
from scripts.run_btc_1d_promoted_candidate_regression import parse_args


def test_btc_1d_promoted_candidate_regression_cli_defaults() -> None:
    config = parse_args([])

    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.lookback_periods == (1400, 1800, 2200, 2600)


def test_btc_1d_promoted_candidate_regression_uses_soft_low_vol_cap() -> None:
    assert PROMOTED_PARAMETERS["min_annualized_volatility"] == 0.2
    assert PROMOTED_PARAMETERS["low_volatility_cap_threshold"] == 0.50
    assert PROMOTED_PARAMETERS["low_volatility_position_cap"] == 0.25


def test_btc_1d_promoted_candidate_regression_writes_artifacts(tmp_path: Path) -> None:
    service = Btc1dPromotedCandidateRegressionService(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        evaluator=CandidateEvaluator(cache_dir=tmp_path / "cache"),
        analysis_results_dir=tmp_path / "analysis",
    )

    result = service.run_batch(
        Btc1dPromotedCandidateRegressionConfig(
            lookback_periods=(240, 320),
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-promoted-regression-test",
    )

    run_dir = tmp_path / "artifacts" / "btc-1d-promoted-regression-test"
    assert (run_dir / "btc_1d_promoted_candidate_regression.json").exists()
    assert (run_dir / "run_leaderboard.json").exists()
    assert Path(result["analysis_result_json"]).exists()
    assert result["summary"]["total_count"] == 2
    assert len(result["results"]) == 2


def test_btc_1d_promoted_candidate_regression_can_skip_writes(tmp_path: Path) -> None:
    service = Btc1dPromotedCandidateRegressionService(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        evaluator=CandidateEvaluator(cache_dir=tmp_path / "cache"),
        analysis_results_dir=tmp_path / "analysis",
    )

    result = service.run_batch(
        Btc1dPromotedCandidateRegressionConfig(
            lookback_periods=(240,),
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-promoted-regression-no-write-test",
        write_artifacts=False,
        write_analysis_result=False,
    )

    assert not (tmp_path / "artifacts" / "btc-1d-promoted-regression-no-write-test").exists()
    assert list((tmp_path / "analysis").glob("*.json")) == []
    assert result["analysis_result_json"] is None
    assert result["summary"]["total_count"] == 1
