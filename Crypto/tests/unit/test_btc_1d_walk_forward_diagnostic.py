from __future__ import annotations

from pathlib import Path

from app.domains.experiments.btc_1d_walk_forward_diagnostic import (
    Btc1dWalkForwardDiagnosticConfig,
    Btc1dWalkForwardDiagnosticService,
)
from scripts.run_btc_1d_walk_forward_diagnostic import parse_args


def test_btc_1d_walk_forward_diagnostic_cli_defaults() -> None:
    config = parse_args([])

    assert config.symbol == "BTCUSDT"
    assert config.interval == "1d"
    assert config.periods == 2200
    assert config.walk_forward_windows == 5


def test_btc_1d_walk_forward_diagnostic_writes_artifacts(tmp_path: Path) -> None:
    service = Btc1dWalkForwardDiagnosticService(
        analysis_results_dir=tmp_path / "analysis",
        artifacts_root=tmp_path / "artifacts",
    )

    result = service.run_diagnostic(
        Btc1dWalkForwardDiagnosticConfig(
            periods=240,
            walk_forward_windows=4,
            allow_synthetic_ohlcv_fallback=True,
        ),
        run_id="btc-1d-walkdiag-test",
    )

    run_dir = tmp_path / "artifacts" / "btc-1d-walkdiag-test"
    assert (run_dir / "btc_1d_walk_forward_diagnostic.json").exists()
    assert (run_dir / "btc_1d_walk_forward_summary.md").exists()
    assert Path(result["analysis_result_json"]).exists()
    assert Path(result["analysis_result_md"]).exists()
    assert len(result["overfitting"]["walk_forward"]) == 4
    assert result["parameter_drifts"]
