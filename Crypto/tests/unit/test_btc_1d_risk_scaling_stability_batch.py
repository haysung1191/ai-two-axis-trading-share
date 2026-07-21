from __future__ import annotations

from pathlib import Path

from app.domains.evaluation.candidate_evaluator import CandidateEvaluator
from app.domains.experiments.btc_1d_risk_scaling_stability_batch import (
    Btc1dRiskScalingStabilityBatchService,
    Btc1dRiskScalingStabilityConfig,
)
from app.domains.governance.artifact_store import ArtifactStore
from scripts.run_btc_1d_risk_scaling_stability_batch import parse_args


def test_btc_1d_risk_scaling_stability_cli_defaults() -> None:
    config = parse_args([])
    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.lookback_periods == (1400, 1800, 2200, 2600)


def test_btc_1d_risk_scaling_stability_batch_writes_artifacts(tmp_path: Path) -> None:
    service = Btc1dRiskScalingStabilityBatchService(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        evaluator=CandidateEvaluator(cache_dir=tmp_path / "cache"),
        analysis_results_dir=tmp_path / "analysis",
    )
    result = service.run_batch(
        Btc1dRiskScalingStabilityConfig(
            lookback_periods=(240, 320),
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-risk-scaling-test",
    )
    run_dir = tmp_path / "artifacts" / "btc-1d-risk-scaling-test"
    assert (run_dir / "btc_1d_risk_scaling_stability_batch.json").exists()
    assert (run_dir / "run_leaderboard.json").exists()
    assert Path(result["analysis_result_json"]).exists()
    assert len(result["results"]) == 9
