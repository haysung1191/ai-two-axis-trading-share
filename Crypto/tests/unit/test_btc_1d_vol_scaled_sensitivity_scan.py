from __future__ import annotations

from pathlib import Path

from app.domains.evaluation.candidate_evaluator import CandidateEvaluator
from app.domains.experiments.btc_1d_vol_scaled_sensitivity_scan import (
    Btc1dVolScaledSensitivityConfig,
    Btc1dVolScaledSensitivityScanService,
)
from app.domains.governance.artifact_store import ArtifactStore
from scripts.run_btc_1d_vol_scaled_sensitivity_scan import parse_args


def test_btc_1d_vol_scaled_sensitivity_scan_cli_defaults() -> None:
    config = parse_args([])

    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.top_stage2 == 3


def test_btc_1d_vol_scaled_sensitivity_scan_writes_artifacts(tmp_path: Path) -> None:
    service = Btc1dVolScaledSensitivityScanService(
        artifact_store=ArtifactStore(root_dir=tmp_path / "artifacts"),
        evaluator=CandidateEvaluator(cache_dir=tmp_path / "cache"),
        analysis_results_dir=tmp_path / "analysis",
    )

    result = service.run_scan(
        Btc1dVolScaledSensitivityConfig(allow_synthetic_ohlcv_fallback=True, periods=240, top_stage2=2),
        run_id="btc-1d-volscan-test",
    )

    run_dir = tmp_path / "artifacts" / "btc-1d-volscan-test"
    assert (run_dir / "btc_1d_vol_scaled_sensitivity_scan.json").exists()
    assert (run_dir / "run_leaderboard.json").exists()
    assert Path(result["analysis_result_json"]).exists()
    assert Path(result["analysis_result_csv"]).exists()
    assert len(result["results"]) == 36
